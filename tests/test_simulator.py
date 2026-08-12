import numpy as np
import pytest

from pyfireca.data import EnvironmentalData, LandscapeInput, SpatialLayer
from pyfireca.gis import RasterMetadata
from pyfireca.ignition import IgnitionEvent, build_ignition_times
from pyfireca.simulator import (
    StaticWildfireSimulationRequest,
    run_static_wildfire_simulation,
)
from pyfireca.state import FireState


def _constant_layer(
    shape: tuple[int, int],
    value: float | int,
    *,
    units: str | None,
) -> SpatialLayer:
    return SpatialLayer(np.full(shape, value), units=units)


def _fm1_landscape(shape: tuple[int, int] = (1, 3)) -> LandscapeInput:
    environment = EnvironmentalData(
        {
            "fuel_model": _constant_layer(shape, 1, units="code"),
            "dead_1h_moisture": _constant_layer(shape, 0.05, units="fraction"),
            "dead_10h_moisture": _constant_layer(shape, 0.05, units="fraction"),
            "dead_100h_moisture": _constant_layer(shape, 0.05, units="fraction"),
            "live_herbaceous_moisture": _constant_layer(shape, 1.0, units="fraction"),
            "live_woody_moisture": _constant_layer(shape, 1.0, units="fraction"),
            "midflame_wind_speed": _constant_layer(shape, 0.0, units="m/s"),
            "wind_from_direction": _constant_layer(shape, 0.0, units="deg"),
            "slope": _constant_layer(shape, 0.0, units="deg"),
            "aspect": _constant_layer(shape, 0.0, units="deg"),
        }
    )
    metadata = RasterMetadata(
        shape=shape,
        crs="EPSG:32633",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 4500000.0),
    )
    return LandscapeInput.from_domain_layers(
        environment,
        metadata,
        domain_layer_names=("fuel_model",),
    )


def test_build_ignition_times_supports_multiple_times_and_earliest_duplicate() -> None:
    ignition = build_ignition_times(
        (2, 3),
        [
            IgnitionEvent(0, 0),
            IgnitionEvent(1, 2, 120.0),
            IgnitionEvent(1, 2, 60.0),
        ],
    )

    assert ignition[0, 0] == 0.0
    assert ignition[1, 2] == 60.0
    assert np.isposinf(ignition[0, 1])


def test_build_ignition_times_rejects_missing_or_outside_events() -> None:
    with pytest.raises(ValueError, match="at least one ignition"):
        build_ignition_times((2, 2), [])
    with pytest.raises(IndexError, match="outside raster shape"):
        build_ignition_times((2, 2), [IgnitionEvent(3, 0)])


def test_static_simulator_runs_landscape_to_arrival_state_and_metrics() -> None:
    landscape = _fm1_landscape()
    ignition = build_ignition_times(landscape.metadata.shape, [IgnitionEvent(0, 0)])
    result = run_static_wildfire_simulation(
        StaticWildfireSimulationRequest(
            landscape=landscape,
            cell_size_m=30.0,
            ignition_times_s=ignition,
        )
    )

    assert result.arrival_times_s[0, 0] == 0.0
    assert result.arrival_times_s[0, 1] > 0.0
    assert result.arrival_times_s[0, 2] == pytest.approx(
        2.0 * result.arrival_times_s[0, 1],
        rel=1e-12,
    )
    assert result.burned_mask.tolist() == [[True, True, True]]
    assert result.burned_cell_count == 3
    assert result.burned_area_m2 == pytest.approx(2700.0)
    assert result.first_arrival_s == 0.0
    assert result.last_arrival_s == pytest.approx(result.arrival_times_s[0, 2])
    assert result.unreachable_domain_cell_count == 0

    state = result.state_at(time_s=0.0, burn_duration_s=60.0)
    assert state.tolist() == [
        [
            int(FireState.BURNING),
            int(FireState.UNBURNED),
            int(FireState.UNBURNED),
        ]
    ]
    assert result.burned_mask_at(0.0).tolist() == [[True, False, False]]

    metrics = result.summary_metrics()
    assert metrics["domain_cell_count"] == 3
    assert metrics["burned_cell_count"] == 3
    assert metrics["burned_area_m2"] == pytest.approx(2700.0)
    assert metrics["runtime_s"] >= 0.0


def test_multiple_simultaneous_ignitions_reduce_middle_arrival_time() -> None:
    landscape = _fm1_landscape()
    single = run_static_wildfire_simulation(
        StaticWildfireSimulationRequest(
            landscape=landscape,
            cell_size_m=30.0,
            ignition_times_s=build_ignition_times(
                landscape.metadata.shape,
                [IgnitionEvent(0, 0)],
            ),
        )
    )
    multiple = run_static_wildfire_simulation(
        StaticWildfireSimulationRequest(
            landscape=landscape,
            cell_size_m=30.0,
            ignition_times_s=build_ignition_times(
                landscape.metadata.shape,
                [IgnitionEvent(0, 0), IgnitionEvent(0, 2)],
            ),
        )
    )

    assert multiple.arrival_times_s[0, 2] == 0.0
    assert multiple.arrival_times_s[0, 1] == pytest.approx(single.arrival_times_s[0, 1])
    assert multiple.last_arrival_s < single.last_arrival_s


def test_request_rejects_ignition_outside_domain() -> None:
    landscape = _fm1_landscape()
    landscape.initial_state[0, 2] = int(FireState.UNBURNABLE)
    ignition = build_ignition_times(landscape.metadata.shape, [IgnitionEvent(0, 2)])

    with pytest.raises(ValueError, match="inside the burnable domain"):
        StaticWildfireSimulationRequest(
            landscape=landscape,
            cell_size_m=30.0,
            ignition_times_s=ignition,
        )
