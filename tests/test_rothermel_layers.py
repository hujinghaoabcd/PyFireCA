import numpy as np
import pytest

from pyfireca.arrival import StaticArrivalTimeSolver
from pyfireca.behavior._units import ft_min_to_m_s
from pyfireca.behavior.rothermel_layers import StaticRasterRothermelInputsProvider
from pyfireca.behavior.rothermel_model import RothermelModel
from pyfireca.behavior.rothermel_spatial import StaticSpatialRothermelDirectionalSpreadRate
from pyfireca.data import EnvironmentalData, MissingEnvironmentalDataError, SpatialLayer
from pyfireca.neighborhood import VonNeumannNeighborhood


def _layer(values: object, units: str | None, *, nodata: float | int | None = None) -> SpatialLayer:
    return SpatialLayer(np.asarray(values), units=units, nodata=nodata)


def _environment(
    *,
    fuel: object = ((1, 1, 1),),
    wind_speed: object | None = None,
    wind_from: object = ((270.0, 90.0, 270.0),),
) -> EnvironmentalData:
    if wind_speed is None:
        wind_speed = np.full((1, 3), ft_min_to_m_s(100.0))
    return EnvironmentalData(
        {
            "fuel_model": _layer(fuel, "code"),
            "dead_1h_moisture": _layer(((0.05, 0.05, 0.05),), "fraction"),
            "dead_10h_moisture": _layer(((0.05, 0.05, 0.05),), "fraction"),
            "dead_100h_moisture": _layer(((0.05, 0.05, 0.05),), "fraction"),
            "live_herbaceous_moisture": _layer(((1.0, 1.0, 1.0),), "fraction"),
            "live_woody_moisture": _layer(((1.0, 1.0, 1.0),), "fraction"),
            "midflame_wind_speed": _layer(wind_speed, "m/s"),
            "wind_from_direction": _layer(wind_from, "deg"),
            "slope": _layer(((0.0, 0.0, 0.0),), "deg"),
            "aspect": _layer(((180.0, 180.0, 180.0),), "deg"),
        }
    )


def test_adapter_builds_typed_inputs_from_static_raster_layers() -> None:
    provider = StaticRasterRothermelInputsProvider(
        _environment(),
        np.ones((1, 3), dtype=bool),
    )

    inputs = provider(0, 0)

    assert inputs.fuel.code == 1
    assert inputs.moisture.dead_1h_fraction == pytest.approx(0.05)
    assert inputs.midflame_wind_speed_m_s == pytest.approx(ft_min_to_m_s(100.0))
    assert inputs.wind_from_direction_deg == pytest.approx(270.0)
    assert inputs.slope_deg == pytest.approx(0.0)
    assert inputs.aspect_deg == pytest.approx(180.0)


def test_domain_exterior_may_keep_declared_nodata() -> None:
    environment = _environment(fuel=((-9999, 1, 1),))
    environment.layers["fuel_model"].nodata = -9999
    domain = np.array([[False, True, True]], dtype=bool)

    provider = StaticRasterRothermelInputsProvider(environment, domain)

    assert provider(0, 1).fuel.code == 1
    with pytest.raises(ValueError, match="outside the simulation domain"):
        provider(0, 0)


def test_domain_interior_nodata_is_rejected() -> None:
    environment = _environment(fuel=((-9999, 1, 1),))
    environment.layers["fuel_model"].nodata = -9999

    with pytest.raises(MissingEnvironmentalDataError, match="inside the simulation domain"):
        StaticRasterRothermelInputsProvider(environment, np.ones((1, 3), dtype=bool))


def test_adapter_rejects_wrong_declared_units() -> None:
    environment = _environment()
    environment.layers["slope"].units = "percent"

    with pytest.raises(ValueError, match="must declare units='deg'"):
        StaticRasterRothermelInputsProvider(environment, np.ones((1, 3), dtype=bool))


def test_adapter_rejects_dynamic_layers() -> None:
    environment = _environment()
    environment.layers["midflame_wind_speed"] = SpatialLayer(
        np.full((2, 1, 3), ft_min_to_m_s(100.0)),
        units="m/s",
    )

    with pytest.raises(ValueError, match="accepts static layers only"):
        StaticRasterRothermelInputsProvider(environment, np.ones((1, 3), dtype=bool))


def test_adapter_rejects_noninteger_fuel_codes() -> None:
    environment = _environment(fuel=((1.5, 1.0, 1.0),))

    with pytest.raises(ValueError, match="must be integers"):
        StaticRasterRothermelInputsProvider(environment, np.ones((1, 3), dtype=bool))


def test_adapter_rejects_unaudited_fuel_code() -> None:
    environment = _environment(fuel=((3, 1, 1),))

    with pytest.raises(KeyError, match="not been audited"):
        StaticRasterRothermelInputsProvider(environment, np.ones((1, 3), dtype=bool))


def test_static_raster_layers_drive_spatially_heterogeneous_arrival() -> None:
    domain = np.ones((1, 3), dtype=bool)
    inputs_provider = StaticRasterRothermelInputsProvider(_environment(), domain)
    spread_provider = StaticSpatialRothermelDirectionalSpreadRate(
        RothermelModel(),
        inputs_provider,
    )
    solver = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=30.0,
        spread_rate_provider=spread_provider,
    )
    ignition = np.full((1, 3), np.inf, dtype=np.float64)
    ignition[0, 0] = 0.0

    arrival = solver.solve(domain, ignition)

    head = 0.04936592733340002
    backing = 0.02074385430924511
    assert arrival[0, 1] == pytest.approx(30.0 / head, rel=1e-13)
    assert arrival[0, 2] == pytest.approx(30.0 / head + 30.0 / backing, rel=1e-13)
