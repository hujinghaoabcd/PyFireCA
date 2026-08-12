import pytest

from pyfireca.config import load_static_run_config

INPUT_NAMES = (
    "fuel_model",
    "dead_1h_moisture",
    "dead_10h_moisture",
    "dead_100h_moisture",
    "live_herbaceous_moisture",
    "live_woody_moisture",
    "midflame_wind_speed",
    "wind_from_direction",
    "slope",
    "aspect",
)


def _yaml(*, extra_root: str = "", omit_input: str | None = None) -> str:
    input_lines = [f"  {name}: data/{name}.tif" for name in INPUT_NAMES if name != omit_input]
    return "\n".join(
        [
            "version: 1",
            "cell_size_m: 30.0",
            "use_wind_speed_limit: false",
            "inputs:",
            *input_lines,
            "ignitions:",
            "  - row: 10",
            "    col: 20",
            "  - row: 12",
            "    col: 21",
            "    time_s: 300",
            "output:",
            "  directory: runs/example",
            extra_root,
            "",
        ]
    )


def test_load_static_run_config_resolves_paths_relative_to_config(tmp_path) -> None:
    path = tmp_path / "configs" / "run.yml"
    path.parent.mkdir()
    path.write_text(_yaml(), encoding="utf-8")

    config = load_static_run_config(path)

    assert config.cell_size_m == 30.0
    assert config.use_wind_speed_limit is False
    assert config.inputs.fuel_model == (path.parent / "data/fuel_model.tif").resolve()
    assert config.output_directory == (path.parent / "runs/example").resolve()
    assert [(event.row, event.col, event.time_s) for event in config.ignitions] == [
        (10, 20, 0.0),
        (12, 21, 300.0),
    ]
    resolved = config.to_dict()
    assert resolved["version"] == 1
    assert resolved["inputs"]["fuel_model"] == str(config.inputs.fuel_model)


def test_config_rejects_missing_input_layer(tmp_path) -> None:
    path = tmp_path / "run.yml"
    path.write_text(_yaml(omit_input="aspect"), encoding="utf-8")

    with pytest.raises(ValueError, match="missing required input rasters"):
        load_static_run_config(path)


def test_config_rejects_unknown_root_key(tmp_path) -> None:
    path = tmp_path / "run.yml"
    path.write_text(_yaml(extra_root="mystery: true"), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown configuration keys"):
        load_static_run_config(path)


def test_config_rejects_empty_ignition_list(tmp_path) -> None:
    text = _yaml().replace(
        "ignitions:\n  - row: 10\n    col: 20\n  - row: 12\n    col: 21\n    time_s: 300",
        "ignitions: []",
    )
    path = tmp_path / "run.yml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="non-empty list"):
        load_static_run_config(path)
