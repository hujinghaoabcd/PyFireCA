import json

import numpy as np
import pytest

from pyfireca.gis import RasterMetadata, read_raster
from pyfireca.outputs import write_static_simulation_outputs
from pyfireca.simulator import StaticWildfireSimulationResult

pytest.importorskip("rasterio")


def test_write_static_simulation_outputs_round_trips_rasters_and_metrics(tmp_path) -> None:
    metadata = RasterMetadata(
        shape=(2, 2),
        crs="EPSG:32633",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 4500000.0),
        nodata=-9999,
    )
    result = StaticWildfireSimulationResult(
        arrival_times_s=np.array([[0.0, 10.0], [np.inf, 20.0]], dtype=np.float64),
        domain_mask=np.array([[True, True], [False, True]], dtype=bool),
        metadata=metadata,
        cell_size_m=30.0,
        runtime_s=0.25,
    )

    paths = write_static_simulation_outputs(result, tmp_path / "outputs")

    arrival, arrival_meta = read_raster(paths.arrival_time)
    assert arrival.dtype == np.float64
    assert arrival.tolist() == [[0.0, 10.0], [-1.0, 20.0]]
    assert arrival_meta.nodata == pytest.approx(-1.0)
    assert arrival_meta.crs == metadata.crs
    assert arrival_meta.transform == pytest.approx(metadata.transform)

    state, state_meta = read_raster(paths.state)
    assert state.dtype == np.uint8
    assert state.tolist() == [[3, 3], [0, 3]]
    assert state_meta.nodata is None

    burned, burned_meta = read_raster(paths.burned_mask)
    assert burned.dtype == np.uint8
    assert burned.tolist() == [[1, 1], [0, 1]]
    assert burned_meta.nodata is None

    metrics = json.loads(paths.metrics.read_text(encoding="utf-8"))
    assert metrics["domain_cell_count"] == 3
    assert metrics["burned_cell_count"] == 3
    assert metrics["unreachable_domain_cell_count"] == 0
    assert metrics["burned_area_m2"] == pytest.approx(2700.0)
    assert metrics["first_arrival_s"] == pytest.approx(0.0)
    assert metrics["last_arrival_s"] == pytest.approx(20.0)
    assert metrics["runtime_s"] == pytest.approx(0.25)
