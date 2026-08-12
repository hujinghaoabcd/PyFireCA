"""Compare source-cell and half-cell interface coupling across a fuel boundary.

Run from an installed/editable PyFireCA environment::

    python benchmarks/edge_coupling.py

The benchmark uses a one-row north-up raster with one sharp FM1/FM2 boundary
and eastward wind. It isolates the edge-coupling assumption while keeping the
Rothermel behavior model, moisture, wind, grid geometry, and arrival solver
fixed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pyfireca.arrival import StaticArrivalTimeSolver
from pyfireca.behavior import (
    RothermelFuelMoisture,
    RothermelInputs,
    RothermelModel,
    StaticSpatialRothermelDirectionalSpreadRate,
    get_standard_fuel_model,
)
from pyfireca.behavior._units import ft_min_to_m_s
from pyfireca.edge_coupling import HalfCellInterfaceDirectionalSpreadRate
from pyfireca.neighborhood import VonNeumannNeighborhood


@dataclass(frozen=True, slots=True)
class InterfaceBenchmarkResult:
    """Arrival comparison at and beyond one two-region fuel interface."""

    left_fuel: int
    right_fuel: int
    source_rate_m_s: float
    target_rate_m_s: float
    source_only_boundary_arrival_s: float
    half_cell_boundary_arrival_s: float
    downstream_arrival_difference_s: float


def _inputs(fuel_code: int) -> RothermelInputs:
    return RothermelInputs(
        fuel=get_standard_fuel_model(fuel_code),
        moisture=RothermelFuelMoisture(
            dead_1h_fraction=0.05,
            dead_10h_fraction=0.05,
            dead_100h_fraction=0.05,
            live_herbaceous_fraction=1.0,
            live_woody_fraction=1.0,
        ),
        midflame_wind_speed_m_s=ft_min_to_m_s(100.0),
        wind_from_direction_deg=270.0,
        slope_deg=0.0,
        aspect_deg=180.0,
    )


def run_interface_case(
    *,
    left_fuel: int,
    right_fuel: int,
    cell_size_m: float = 30.0,
) -> InterfaceBenchmarkResult:
    """Run one eastward two-region edge-coupling comparison."""

    fuel_codes = (left_fuel, left_fuel, left_fuel, right_fuel, right_fuel, right_fuel)
    inputs_by_fuel = {code: _inputs(code) for code in set(fuel_codes)}

    def inputs_provider(row: int, col: int) -> RothermelInputs:
        del row
        return inputs_by_fuel[fuel_codes[col]]

    directional = StaticSpatialRothermelDirectionalSpreadRate(
        RothermelModel(),
        inputs_provider,
    )
    interface = HalfCellInterfaceDirectionalSpreadRate(directional)
    domain = np.ones((1, len(fuel_codes)), dtype=bool)
    ignition = np.full(domain.shape, np.inf, dtype=np.float64)
    ignition[0, 0] = 0.0
    neighborhood = VonNeumannNeighborhood()

    source_only = StaticArrivalTimeSolver(
        neighborhood=neighborhood,
        cell_size_m=cell_size_m,
        spread_rate_provider=directional,
    ).solve(domain, ignition)
    half_cell = StaticArrivalTimeSolver(
        neighborhood=neighborhood,
        cell_size_m=cell_size_m,
        spread_rate_provider=interface,
    ).solve(domain, ignition)

    source_rate = directional.spread_rate_m_s(0, 2, (0, 1))
    target_rate = directional.spread_rate_m_s(0, 3, (0, 1))
    return InterfaceBenchmarkResult(
        left_fuel=left_fuel,
        right_fuel=right_fuel,
        source_rate_m_s=source_rate,
        target_rate_m_s=target_rate,
        source_only_boundary_arrival_s=float(source_only[0, 3]),
        half_cell_boundary_arrival_s=float(half_cell[0, 3]),
        downstream_arrival_difference_s=float(half_cell[0, 5] - source_only[0, 5]),
    )


def main() -> None:
    print(
        "left_fuel,right_fuel,source_rate_m_s,target_rate_m_s,"
        "source_boundary_s,half_cell_boundary_s,downstream_delta_s"
    )
    for left, right in ((1, 2), (2, 1)):
        result = run_interface_case(left_fuel=left, right_fuel=right)
        print(
            f"{result.left_fuel},{result.right_fuel},"
            f"{result.source_rate_m_s:.9f},{result.target_rate_m_s:.9f},"
            f"{result.source_only_boundary_arrival_s:.6f},"
            f"{result.half_cell_boundary_arrival_s:.6f},"
            f"{result.downstream_arrival_difference_s:.6f}"
        )


if __name__ == "__main__":
    main()
