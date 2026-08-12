import numpy as np
import pytest

from pyfireca.behavior._units import ft_min_to_m_s
from pyfireca.behavior.rothermel_landscape import build_static_raster_rothermel_arrival_solver
from pyfireca.data import EnvironmentalData, LandscapeInput, SpatialLayer
from pyfireca.gis import RasterMetadata
from pyfireca.neighborhood import VonNeumannNeighborhood
from pyfireca.state import FireState


def _layer(values: object, units: str | None) -> SpatialLayer:
    return SpatialLayer(np.asarray(values), units=units)


def _environment() -> EnvironmentalData:
    return EnvironmentalData(
        {
            "fuel_model": _layer(((1, 1, 1),), "code"),
            "dead_1h_moisture": _layer(((0.05, 0.05, 0.05),), "fraction"),
            "dead_10h_moisture": _layer(((0.05, 0.05, 0.05),), "fraction"),
            "dead_100h_moisture": _layer(((0.05, 0.05, 0.05),), "fraction"),
            "live_herbaceous_moisture": _layer(((1.0, 1.0, 1.0),), "fraction"),
            "live_woody_moisture": _layer(((1.0, 1.0, 1.0),), "fraction"),
            "midflame_wind_speed": _layer(
                np.full((1, 3), ft_min_to_m_s(100.0)),
                "m/s",
            ),
            "wind_from_direction": _layer(((270.0, 270.0, 270.0),), "deg"),
            "slope": _layer(((0.0, 0.0, 0.0),), "deg"),
            "aspect": _layer(((180.0, 180.0, 180.0),), "deg"),
        }
    )


def _metadata(transform: tuple[float, float, float, float, float, float]) -> RasterMetadata:
    return RasterMetadata(
        shape=(1, 3),
        crs="EPSG:32632",
        transform=transform,
    )


def _landscape(
    *,
    transform: tuple[float, float, float, float, float, float] = (
        30.0,
        0.0,
        500000.0,
        0.0,
        -30.0,
        4500000.0,
    ),
    state: np.ndarray | None = None,
) -> LandscapeInput:
    if state is None:
        state = np.full((1, 3), int(FireState.UNBURNED), dtype=np.uint8)
    return LandscapeInput(
        environment=_environment(),
        metadata=_metadata(transform),
        initial_state=state,
    )


def test_factory_builds_end_to_end_static_raster_solver() -> None:
    solver = build_static_raster_rothermel_arrival_solver(
        _landscape(),
        cell_size_m=30.0,
        neighborhood=VonNeumannNeighborhood(),
    )
    domain = np.ones((1, 3), dtype=bool)
    ignition = np.full((1, 3), np.inf, dtype=np.float64)
    ignition[0, 0] = 0.0

    arrival = solver.solve(domain, ignition)

    head = 0.04936592733340002
    assert arrival[0, 1] == pytest.approx(30.0 / head, rel=1e-13)
    assert arrival[0, 2] == pytest.approx(60.0 / head, rel=1e-13)


def test_factory_domain_follows_initial_unburnable_state() -> None:
    state = np.array(
        [[FireState.UNBURNED, FireState.UNBURNABLE, FireState.UNBURNED]],
        dtype=np.uint8,
    )
    solver = build_static_raster_rothermel_arrival_solver(
        _landscape(state=state),
        cell_size_m=30.0,
        neighborhood=VonNeumannNeighborhood(),
    )
    domain = state != int(FireState.UNBURNABLE)
    ignition = np.full((1, 3), np.inf, dtype=np.float64)
    ignition[0, 0] = 0.0

    arrival = solver.solve(domain, ignition)

    assert arrival[0, 0] == pytest.approx(0.0)
    assert np.isinf(arrival[0, 1])
    assert np.isinf(arrival[0, 2])


def test_factory_rejects_rotated_grid() -> None:
    landscape = _landscape(
        transform=(30.0, 1.0, 500000.0, 0.0, -30.0, 4500000.0),
    )

    with pytest.raises(ValueError, match="north-up grid"):
        build_static_raster_rothermel_arrival_solver(landscape, cell_size_m=30.0)


def test_factory_rejects_rectangular_grid() -> None:
    landscape = _landscape(
        transform=(30.0, 0.0, 500000.0, 0.0, -20.0, 4500000.0),
    )

    with pytest.raises(ValueError, match="does not match"):
        build_static_raster_rothermel_arrival_solver(landscape, cell_size_m=30.0)


def test_factory_rejects_declared_cell_size_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        build_static_raster_rothermel_arrival_solver(_landscape(), cell_size_m=10.0)
