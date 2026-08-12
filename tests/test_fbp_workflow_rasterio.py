import json

import numpy as np
import pytest
import yaml

from pyfireca import cli
from pyfireca.fbp_config import StaticFBPRasterInputPaths, StaticFBPRunConfig
from pyfireca.fbp_workflow import run_static_fbp_config, validate_static_fbp_run
from pyfireca.gis import RasterMetadata, read_raster, write_raster
from pyfireca.ignition import IgnitionEvent

pytest.importorskip("rasterio")


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


def _write_fbp_inputs(tmp_path) -> StaticFBPRasterInputPaths:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shape = (1, 3)
    metadata = RasterMetadata(
        shape=shape,
        crs="EPSG:32633",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 4500000.0),
        nodata=-9999.0,
    )
    values = {
        "fbp_fuel_type": np.full(shape, 1, dtype=np.int16),
        "ffmc": np.full(shape, 90.0, dtype=np.float32),
        "bui": np.full(shape, 60.0, dtype=np.float32),
        "wind_speed_10m": np.full(shape, 10.0, dtype=np.float32),
        "wind_from_direction": np.full(shape, 270.0, dtype=np.float32),
        "slope_percent": np.zeros(shape, dtype=np.float32),
        "aspect": np.zeros(shape, dtype=np.float32),
        "latitude": np.full(shape, 55.0, dtype=np.float32),
        "longitude": np.full(shape, -120.0, dtype=np.float32),
        "elevation": np.zeros(shape, dtype=np.float32),
    }
    paths = {}
    for name, array in values.items():
        path = data_dir / f"{name}.tif"
        write_raster(path, array, metadata)
        paths[name] = path
    return StaticFBPRasterInputPaths(**paths)


def _write_fbp_yaml(tmp_path, inputs: StaticFBPRasterInputPaths, output_name: str) -> object:
    path = tmp_path / f"{output_name}.yml"
    relative_inputs = {
        name: input_path.relative_to(tmp_path).as_posix()
        for name, input_path in inputs.named_paths()
    }
    payload = {
        "version": 1,
        "behavior": {
            "model": "fbp",
            "julian_day": 180,
            "percent_conifer": 50,
            "percent_dead_fir": 35,
            "grass_fuel_load_kg_m2": 0.35,
            "grass_curing_percent": 80,
        },
        "cell_size_m": 30.0,
        "inputs": relative_inputs,
        "ignitions": [{"row": 0, "col": 0}],
        "output": {"directory": f"runs/{output_name}"},
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_fbp_file_workflow_writes_common_reproducible_artifacts(tmp_path) -> None:
    inputs = _write_fbp_inputs(tmp_path)
    config = StaticFBPRunConfig(
        inputs=inputs,
        cell_size_m=30.0,
        ignitions=(IgnitionEvent(0, 0),),
        output_directory=tmp_path / "run",
        julian_day=180,
    )

    validate_static_fbp_run(config)
    result, artifacts = run_static_fbp_config(config)

    assert result.burned_cell_count == 3
    for path in (
        artifacts.resolved_config,
        artifacts.metadata,
        artifacts.environment,
        artifacts.metrics,
        artifacts.log,
        artifacts.outputs.arrival_time,
        artifacts.outputs.state,
        artifacts.outputs.burned_mask,
        artifacts.outputs.perimeter,
    ):
        assert path.is_file()

    resolved = yaml.safe_load(artifacts.resolved_config.read_text(encoding="utf-8"))
    assert resolved["behavior"]["model"] == "fbp"
    assert resolved["behavior"]["julian_day"] == 180

    metadata = json.loads(artifacts.metadata.read_text(encoding="utf-8"))
    assert metadata["behavior"]["model"] == "canadian_fbp"
    assert metadata["behavior"]["implementation"] == "self-contained PyFireCA runtime"
    assert metadata["behavior"]["fuel_codes"] == [1]
    assert set(metadata["input_sha256"]) == set(FBP_INPUT_NAMES)

    arrival, arrival_metadata = read_raster(artifacts.outputs.arrival_time)
    assert arrival[0, 0] == pytest.approx(0.0)
    assert 0.0 < arrival[0, 1] < arrival[0, 2]
    assert arrival_metadata.crs == "EPSG:32633"


def test_cli_dispatches_explicit_fbp_yaml_end_to_end(tmp_path, capsys) -> None:
    inputs = _write_fbp_inputs(tmp_path)
    config_path = _write_fbp_yaml(tmp_path, inputs, "cli-fbp")

    assert cli.main(["validate", str(config_path)]) == 0
    assert "Valid PyFireCA configuration" in capsys.readouterr().out

    assert cli.main(["run", str(config_path)]) == 0
    output = capsys.readouterr().out
    assert "PyFireCA run complete" in output
    assert "Burned cells: 3" in output
    run_directory = tmp_path / "runs/cli-fbp"
    assert (run_directory / "metadata.json").is_file()
    assert (run_directory / "outputs/arrival_time.tif").is_file()
    assert (run_directory / "outputs/perimeter.geojson").is_file()
