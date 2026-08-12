from pathlib import Path

import pytest

from pyfireca.config import StaticRunConfig
from pyfireca.fbp_config import (
    StaticFBPRunConfig,
    load_static_fbp_run_config,
)
from pyfireca.run_config import configured_behavior_model, load_run_config

FBP_INPUT_NAMES = (
    "fbp_fuel_type",
    "ffmc",
    "bui",
    "wind_speed_10m",
    "wind_from_direction",
    "slope_percent",
    "aspect",
    "latitude",
    "longitude",
    "elevation",
)


def _write_fbp_config(tmp_path: Path, *, extra_behavior: str = "") -> Path:
    input_lines = "\n".join(f"  {name}: data/{name}.tif" for name in FBP_INPUT_NAMES)
    config = tmp_path / "fbp.yml"
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "behavior:",
                "  model: fbp",
                "  julian_day: 180",
                "  percent_conifer: 60",
                "  percent_dead_fir: 40",
                "  grass_fuel_load_kg_m2: 0.5",
                "  grass_curing_percent: 75",
                extra_behavior,
                "cell_size_m: 30",
                "inputs:",
                input_lines,
                "ignitions:",
                "  - row: 2",
                "    col: 3",
                "    time_s: 15",
                "output:",
                "  directory: runs/fbp",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config


def test_load_static_fbp_config_preserves_model_specific_schema(tmp_path):
    path = _write_fbp_config(tmp_path)
    config = load_static_fbp_run_config(path)

    assert isinstance(config, StaticFBPRunConfig)
    assert config.julian_day == 180
    assert config.percent_conifer == 60.0
    assert config.percent_dead_fir == 40.0
    assert config.grass_fuel_load_kg_m2 == 0.5
    assert config.grass_curing_percent == 75.0
    assert config.inputs.ffmc == (tmp_path / "data/ffmc.tif").resolve()
    assert config.output_directory == (tmp_path / "runs/fbp").resolve()
    assert config.ignitions[0].time_s == 15.0
    assert config.to_dict()["behavior"]["model"] == "fbp"


def test_model_aware_loader_dispatches_explicit_fbp(tmp_path):
    path = _write_fbp_config(tmp_path)
    assert configured_behavior_model(path) == "fbp"
    assert isinstance(load_run_config(path), StaticFBPRunConfig)


def test_model_aware_loader_keeps_legacy_rothermel_schema(tmp_path):
    input_names = (
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
    input_lines = "\n".join(f"  {name}: data/{name}.tif" for name in input_names)
    path = tmp_path / "rothermel.yml"
    path.write_text(
        "\n".join(
            [
                "version: 1",
                "cell_size_m: 30",
                "inputs:",
                input_lines,
                "ignitions:",
                "  - row: 0",
                "    col: 0",
                "output:",
                "  directory: runs/rothermel",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert configured_behavior_model(path) == "rothermel"
    assert isinstance(load_run_config(path), StaticRunConfig)


def test_fbp_config_rejects_rothermel_input_names(tmp_path):
    path = _write_fbp_config(tmp_path)
    text = path.read_text(encoding="utf-8").replace("  ffmc: data/ffmc.tif\n", "")
    text = text.replace("inputs:\n", "inputs:\n  fuel_model: data/fuel_model.tif\n")
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="missing required FBP input rasters"):
        load_static_fbp_run_config(path)


def test_fbp_config_rejects_unknown_behavior_keys(tmp_path):
    path = _write_fbp_config(tmp_path, extra_behavior="  magic_ros_factor: 2")
    with pytest.raises(ValueError, match="unknown FBP behavior keys"):
        load_static_fbp_run_config(path)
