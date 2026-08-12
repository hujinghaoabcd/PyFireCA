import json

import numpy as np
import pytest
import yaml

from pyfireca.config import StaticRasterInputPaths, StaticRunConfig
from pyfireca.gis import RasterMetadata, read_raster, write_raster
from pyfireca.ignition import IgnitionEvent
from pyfireca.workflow import run_static_config, validate_static_run

pytest.importorskip("rasterio")


def _write_inputs(tmp_path) -> StaticRasterInputPaths:
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
        "fuel_model": np.full(shape, 1, dtype=np.int16),
        "dead_1h_moisture": np.full(shape, 0.05, dtype=np.float32),
        "dead_10h_moisture": np.full(shape, 0.05, dtype=np.float32),
        "dead_100h_moisture": np.full(shape, 0.05, dtype=np.float32),
        "live_herbaceous_moisture": np.full(shape, 1.0, dtype=np.float32),
        "live_woody_moisture": np.full(shape, 1.0, dtype=np.float32),
        "midflame_wind_speed": np.zeros(shape, dtype=np.float32),
        "wind_from_direction": np.zeros(shape, dtype=np.float32),
        "slope": np.zeros(shape, dtype=np.float32),
        "aspect": np.zeros(shape, dtype=np.float32),
    }
    paths = {}
    for name, array in values.items():
        path = data_dir / f"{name}.tif"
        write_raster(path, array, metadata)
        paths[name] = path
    return StaticRasterInputPaths(**paths)


def test_static_file_workflow_validates_runs_and_writes_reproducible_artifacts(tmp_path) -> None:
    inputs = _write_inputs(tmp_path)
    config = StaticRunConfig(
        inputs=inputs,
        cell_size_m=30.0,
        ignitions=(IgnitionEvent(0, 0),),
        output_directory=tmp_path / "run",
    )

    validate_static_run(config)
    result, artifacts = run_static_config(config)

    assert result.burned_cell_count == 3
    assert artifacts.directory == tmp_path / "run"
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
    assert resolved["version"] == 1
    assert resolved["cell_size_m"] == pytest.approx(30.0)
    assert resolved["ignitions"] == [{"row": 0, "col": 0, "time_s": 0.0}]

    metadata = json.loads(artifacts.metadata.read_text(encoding="utf-8"))
    assert metadata["raster"]["shape"] == [1, 3]
    assert metadata["fuel_catalogue"] == [
        {
            "code": "FM1",
            "number": 1,
            "source_commit": "29888c7ad364aa18cfb340f4c25a8e395f24260f",
        }
    ]
    assert set(metadata["input_sha256"]) == {name for name, _ in inputs.named_paths()}
    assert all(len(value) == 64 for value in metadata["input_sha256"].values())

    metrics = json.loads(artifacts.metrics.read_text(encoding="utf-8"))
    assert metrics["burned_cell_count"] == 3
    assert metrics["burned_area_m2"] == pytest.approx(2700.0)

    log = artifacts.log.read_text(encoding="utf-8")
    assert "PyFireCA static run completed" in log
    assert "burned_cell_count=3" in log

    perimeter = json.loads(artifacts.outputs.perimeter.read_text(encoding="utf-8"))
    assert perimeter["type"] == "FeatureCollection"
    assert perimeter["features"]

    arrival, arrival_metadata = read_raster(artifacts.outputs.arrival_time)
    assert arrival.shape == (1, 3)
    assert arrival[0, 0] == pytest.approx(0.0)
    assert arrival[0, 1] > 0.0
    assert arrival[0, 2] > arrival[0, 1]
    assert arrival_metadata.crs == "EPSG:32633"


def test_static_file_workflow_rejects_nonempty_output_directory(tmp_path) -> None:
    inputs = _write_inputs(tmp_path)
    output = tmp_path / "run"
    output.mkdir()
    (output / "keep.txt").write_text("existing\n", encoding="utf-8")
    config = StaticRunConfig(
        inputs=inputs,
        cell_size_m=30.0,
        ignitions=(IgnitionEvent(0, 0),),
        output_directory=output,
    )

    with pytest.raises(FileExistsError, match="must be empty"):
        run_static_config(config)
