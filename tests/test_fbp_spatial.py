"""Spatial integration tests for the self-contained Canadian FBP model."""

from __future__ import annotations

import numpy as np
import pytest

from pyfireca.behavior.fbp import FBPModel
from pyfireca.behavior.fbp_landscape import build_static_raster_fbp_arrival_solver
from pyfireca.behavior.fbp_layers import StaticRasterFBPInputsProvider
from pyfireca.behavior.fbp_spatial import StaticSpatialFBPDirectionalSpreadRate
from pyfireca.data import EnvironmentalData, LandscapeInput, SpatialLayer
from pyfireca.fbp_simulator import StaticFBPSimulationRequest, run_static_fbp_simulation
from pyfireca.gis import RasterMetadata
from pyfireca.state import FireState


def _environment(shape=(1, 3), fuel_code=1):
    def layer(value, units):
        return SpatialLayer(np.full(shape, value, dtype=np.float64), units=units)

    return EnvironmentalData(
        {
            "fbp_fuel_type": layer(fuel_code, "code"),
            "ffmc": layer(90.0, "code"),
            "bui": layer(60.0, "index"),
            "wind_speed_10m": layer(10.0, "km/h"),
            "wind_from_direction": layer(270.0, "deg"),
            "slope_percent": layer(0.0, "percent"),
            "aspect": layer(0.0, "deg"),
            "latitude": layer(55.0, "deg"),
            "longitude": layer(-120.0, "deg"),
            "elevation": layer(0.0, "m"),
        }
    )


def _landscape(shape=(1, 3), fuel_code=1):
    environment = _environment(shape=shape, fuel_code=fuel_code)
    metadata = RasterMetadata(
        shape=shape,
        crs="EPSG:32633",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 4500000.0),
    )
    state = np.full(shape, int(FireState.UNBURNED), dtype=np.uint8)
    return LandscapeInput(environment=environment, metadata=metadata, initial_state=state)


def test_static_raster_fbp_provider_preserves_native_units_and_values():
    landscape = _landscape()
    domain = np.ones(landscape.metadata.shape, dtype=bool)
    provider = StaticRasterFBPInputsProvider(
        landscape.environment,
        domain,
        julian_day=180,
    )
    inputs = provider(0, 1)
    assert inputs.fuel_type == "C1"
    assert inputs.ffmc == 90.0
    assert inputs.bui == 60.0
    assert inputs.wind_speed_10m_kmh == 10.0
    assert inputs.wind_from_direction_deg == 270.0
    assert inputs.slope_percent == 0.0
    assert inputs.latitude_deg == 55.0
    assert inputs.longitude_deg == -120.0


def test_static_spatial_fbp_provider_caches_source_behavior():
    landscape = _landscape()
    domain = np.ones(landscape.metadata.shape, dtype=bool)
    inputs_provider = StaticRasterFBPInputsProvider(
        landscape.environment,
        domain,
        julian_day=180,
    )
    spread = StaticSpatialFBPDirectionalSpreadRate(FBPModel(), inputs_provider)
    east = (0, 1)
    assert spread.spread_rate_m_s(0, 0, east) > 0.0
    assert spread.spread_rate_m_s(0, 0, east) > 0.0
    assert spread.cached_cell_count == 1


def test_fbp_landscape_factory_runs_arrival_solver_end_to_end():
    landscape = _landscape()
    solver = build_static_raster_fbp_arrival_solver(
        landscape,
        cell_size_m=30.0,
        julian_day=180,
    )
    ignition = np.full(landscape.metadata.shape, np.inf, dtype=np.float64)
    ignition[0, 0] = 0.0
    domain = np.ones(landscape.metadata.shape, dtype=bool)
    arrival = solver.solve(domain, ignition)
    assert arrival[0, 0] == 0.0
    assert np.isfinite(arrival[0, 1])
    assert np.isfinite(arrival[0, 2])
    assert arrival[0, 0] < arrival[0, 1] < arrival[0, 2]


def test_user_fbp_simulator_returns_shared_result_contract():
    landscape = _landscape()
    ignition = np.full(landscape.metadata.shape, np.inf, dtype=np.float64)
    ignition[0, 0] = 0.0
    result = run_static_fbp_simulation(
        StaticFBPSimulationRequest(
            landscape=landscape,
            cell_size_m=30.0,
            ignition_times_s=ignition,
            julian_day=180,
        )
    )
    assert result.burned_cell_count == 3
    assert result.burned_area_m2 == pytest.approx(2700.0)
    assert result.first_arrival_s == 0.0
    assert result.last_arrival_s > 0.0


def test_nf_or_water_cells_must_be_outside_burnable_domain():
    landscape = _landscape(shape=(1, 2), fuel_code=1)
    landscape.environment.layers["fbp_fuel_type"].values[0, 1] = 19
    with pytest.raises(ValueError, match="NF/WA"):
        build_static_raster_fbp_arrival_solver(
            landscape,
            cell_size_m=30.0,
            julian_day=180,
        )


def test_fbp_provider_rejects_rather_than_converts_wrong_units():
    landscape = _landscape()
    landscape.environment.layers["wind_speed_10m"].units = "m/s"
    domain = np.ones(landscape.metadata.shape, dtype=bool)
    with pytest.raises(ValueError, match="km/h"):
        StaticRasterFBPInputsProvider(
            landscape.environment,
            domain,
            julian_day=180,
        )
