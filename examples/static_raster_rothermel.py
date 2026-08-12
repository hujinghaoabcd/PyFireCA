"""End-to-end static raster Rothermel arrival example.

Run from an installed/editable PyFireCA environment::

    python examples/static_raster_rothermel.py

The example is intentionally file-free so it demonstrates the numerical/GIS
contracts without requiring Rasterio. Real GeoTIFF workflows should read and
align rasters first, then construct the same ``SpatialLayer`` objects.
"""

from __future__ import annotations

import numpy as np

from pyfireca import (
    FireState,
    LandscapeInput,
    VonNeumannNeighborhood,
    arrival_times_to_state,
    build_static_raster_rothermel_arrival_solver,
)
from pyfireca.behavior._units import ft_min_to_m_s
from pyfireca.data import EnvironmentalData, SpatialLayer
from pyfireca.gis import RasterMetadata


def layer(values: object, units: str | None) -> SpatialLayer:
    return SpatialLayer(np.asarray(values), units=units)


def main() -> None:
    shape = (5, 7)
    fuel = np.ones(shape, dtype=np.int16)
    moisture = np.full(shape, 0.05, dtype=np.float64)
    live_moisture = np.full(shape, 1.0, dtype=np.float64)
    wind_speed = np.full(shape, ft_min_to_m_s(100.0), dtype=np.float64)
    wind_from = np.full(shape, 270.0, dtype=np.float64)  # west wind pushes fire east
    slope = np.zeros(shape, dtype=np.float64)
    aspect = np.full(shape, 180.0, dtype=np.float64)

    environment = EnvironmentalData(
        {
            "fuel_model": layer(fuel, "code"),
            "dead_1h_moisture": layer(moisture, "fraction"),
            "dead_10h_moisture": layer(moisture, "fraction"),
            "dead_100h_moisture": layer(moisture, "fraction"),
            "live_herbaceous_moisture": layer(live_moisture, "fraction"),
            "live_woody_moisture": layer(live_moisture, "fraction"),
            "midflame_wind_speed": layer(wind_speed, "m/s"),
            "wind_from_direction": layer(wind_from, "deg"),
            "slope": layer(slope, "deg"),
            "aspect": layer(aspect, "deg"),
        }
    )

    initial_state = np.full(shape, int(FireState.UNBURNED), dtype=np.uint8)
    metadata = RasterMetadata(
        shape=shape,
        crs="EPSG:32632",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 4500000.0),
    )
    landscape = LandscapeInput(environment, metadata, initial_state)

    solver = build_static_raster_rothermel_arrival_solver(
        landscape,
        cell_size_m=30.0,
        neighborhood=VonNeumannNeighborhood(),
    )

    domain = initial_state != int(FireState.UNBURNABLE)
    ignition_times = np.full(shape, np.inf, dtype=np.float64)
    ignition_times[2, 1] = 0.0
    arrival = solver.solve(domain, ignition_times)

    state_at_20_min = arrival_times_to_state(
        domain,
        arrival,
        time_s=20.0 * 60.0,
        burn_duration_s=10.0 * 60.0,
    )

    np.set_printoptions(precision=1, suppress=True)
    print("Arrival time (s):")
    print(arrival)
    print("\nFireState at 20 min:")
    print(state_at_20_min)


if __name__ == "__main__":
    main()
