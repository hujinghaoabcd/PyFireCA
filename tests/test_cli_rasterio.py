import numpy as np
import pytest

from pyfireca import cli
from pyfireca.gis import RasterMetadata, write_raster

pytest.importorskip("rasterio")

_INPUT_VALUES = {
    "fuel_model": 1,
    "dead_1h_moisture": 0.05,
    "dead_10h_moisture": 0.05,
    "dead_100h_moisture": 0.05,
    "live_herbaceous_moisture": 1.0,
    "live_woody_moisture": 1.0,
    "midflame_wind_speed": 0.0,
    "wind_from_direction": 0.0,
    "slope": 0.0,
    "aspect": 0.0,
}


def _write_cli_fixture(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    metadata = RasterMetadata(
        shape=(1, 3),
        crs="EPSG:32633",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 4500000.0),
        nodata=-9999.0,
    )
    for name, value in _INPUT_VALUES.items():
        dtype = np.int16 if name == "fuel_model" else np.float32
        write_raster(
            data_dir / f"{name}.tif",
            np.full((1, 3), value, dtype=dtype),
            metadata,
        )

    input_lines = "\n".join(f"  {name}: data/{name}.tif" for name in _INPUT_VALUES)
    config_path = tmp_path / "run.yml"
    config_path.write_text(
        "\n".join(
            [
                "version: 1",
                "cell_size_m: 30.0",
                "use_wind_speed_limit: false",
                "inputs:",
                input_lines,
                "ignitions:",
                "  - row: 0",
                "    col: 0",
                "output:",
                "  directory: runs/cli-example",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def test_cli_validate_and_run_complete_file_workflow(tmp_path, capsys) -> None:
    config_path = _write_cli_fixture(tmp_path)

    assert cli.main(["validate", str(config_path)]) == 0
    validate_output = capsys.readouterr().out
    assert "Valid PyFireCA configuration" in validate_output

    assert cli.main(["run", str(config_path)]) == 0
    run_output = capsys.readouterr().out
    assert "PyFireCA run complete" in run_output
    assert "Burned cells: 3" in run_output

    run_dir = tmp_path / "runs" / "cli-example"
    assert (run_dir / "config.resolved.yml").is_file()
    assert (run_dir / "metadata.json").is_file()
    assert (run_dir / "environment.json").is_file()
    assert (run_dir / "metrics.json").is_file()
    assert (run_dir / "log.txt").is_file()
    assert (run_dir / "outputs" / "arrival_time.tif").is_file()
    assert (run_dir / "outputs" / "state.tif").is_file()
    assert (run_dir / "outputs" / "burned_mask.tif").is_file()
    assert (run_dir / "outputs" / "perimeter.geojson").is_file()
