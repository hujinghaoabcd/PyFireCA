"""Benchmark immediate-neighbor CA arrival against a continuous ellipse reference.

Run from an installed/editable PyFireCA environment::

    python benchmarks/ca_discretization.py

This benchmark is deterministic. It compares the same validated homogeneous
FM1 directional behavior under VN4 and Moore8 raster-edge topologies while
using the continuous Behave/Catchpole ignition-point ellipse as an analytical
cell-center arrival reference.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite

import numpy as np

from pyfireca.arrival import StaticArrivalTimeSolver
from pyfireca.behavior import (
    HomogeneousRothermelDirectionalSpreadRate,
    RothermelFuelMoisture,
    RothermelInputs,
    RothermelModel,
    get_standard_fuel_model,
)
from pyfireca.behavior._units import ft_min_to_m_s
from pyfireca.evaluation import (
    ArrivalErrorMetrics,
    analytical_ellipse_arrival_times,
    arrival_error_metrics,
)
from pyfireca.neighborhood import MooreNeighborhood, Neighborhood, VonNeumannNeighborhood

DEFAULT_HEADINGS_DEG = (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0)
DEFAULT_CELL_SIZES_M = (5.0, 10.0, 20.0, 30.0, 60.0)


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """One deterministic neighborhood benchmark result."""

    neighborhood: str
    cell_size_m: float
    head_direction_deg: float
    shape: tuple[int, int]
    metrics: ArrivalErrorMetrics


def _fm1_inputs(*, wind_from_direction_deg: float) -> RothermelInputs:
    return RothermelInputs(
        fuel=get_standard_fuel_model(1),
        moisture=RothermelFuelMoisture(
            dead_1h_fraction=0.05,
            dead_10h_fraction=0.05,
            dead_100h_fraction=0.05,
            live_herbaceous_fraction=1.0,
            live_woody_fraction=1.0,
        ),
        midflame_wind_speed_m_s=ft_min_to_m_s(100.0),
        wind_from_direction_deg=wind_from_direction_deg,
        slope_deg=0.0,
        aspect_deg=180.0,
    )


def centered_square_shape(*, half_extent_m: float, cell_size_m: float) -> tuple[int, int]:
    """Return an odd square shape for a fixed physical half-extent.

    The requested half-extent must be an integer number of cells so cell-size
    sweeps compare exactly the same center-to-boundary physical distance.
    """

    if not isfinite(half_extent_m) or half_extent_m <= 0.0:
        raise ValueError("half_extent_m must be finite and positive")
    if not isfinite(cell_size_m) or cell_size_m <= 0.0:
        raise ValueError("cell_size_m must be finite and positive")

    radius_cells = half_extent_m / cell_size_m
    rounded = round(radius_cells)
    if not isclose(radius_cells, rounded, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("half_extent_m must be an integer multiple of cell_size_m")
    side = 2 * int(rounded) + 1
    return (side, side)


def run_case(
    neighborhood: Neighborhood,
    *,
    neighborhood_name: str,
    shape: tuple[int, int] = (101, 101),
    cell_size_m: float = 30.0,
    head_direction_deg: float = 30.0,
) -> BenchmarkResult:
    """Run one FM1 neighborhood case against the continuous ellipse reference."""

    ignition = (shape[0] // 2, shape[1] // 2)
    wind_from_direction_deg = (head_direction_deg + 180.0) % 360.0
    provider = HomogeneousRothermelDirectionalSpreadRate(
        RothermelModel(),
        _fm1_inputs(wind_from_direction_deg=wind_from_direction_deg),
    )
    solver = StaticArrivalTimeSolver(
        neighborhood=neighborhood,
        cell_size_m=cell_size_m,
        spread_rate_provider=provider,
    )
    domain = np.ones(shape, dtype=bool)
    ignition_times = np.full(shape, np.inf, dtype=np.float64)
    ignition_times[ignition] = 0.0
    observed = solver.solve(domain, ignition_times)

    behavior = provider.behavior_result
    if behavior.spread_direction_deg is None:
        raise RuntimeError("wind-driven benchmark requires a defined head direction")
    reference = analytical_ellipse_arrival_times(
        shape,
        cell_size_m=cell_size_m,
        ignition=ignition,
        head_spread_rate_m_s=behavior.spread_rate_m_s,
        eccentricity=provider.ellipse.eccentricity,
        head_direction_deg=behavior.spread_direction_deg,
    )

    return BenchmarkResult(
        neighborhood=neighborhood_name,
        cell_size_m=cell_size_m,
        head_direction_deg=head_direction_deg,
        shape=shape,
        metrics=arrival_error_metrics(observed, reference),
    )


def run_neighborhood_comparison(
    *,
    shape: tuple[int, int] = (101, 101),
    cell_size_m: float = 30.0,
    head_direction_deg: float = 30.0,
) -> list[BenchmarkResult]:
    """Return VN4 and Moore8 results for one identical physical case."""

    return [
        run_case(
            VonNeumannNeighborhood(),
            neighborhood_name="VN4",
            shape=shape,
            cell_size_m=cell_size_m,
            head_direction_deg=head_direction_deg,
        ),
        run_case(
            MooreNeighborhood(),
            neighborhood_name="Moore8",
            shape=shape,
            cell_size_m=cell_size_m,
            head_direction_deg=head_direction_deg,
        ),
    ]


def run_heading_sweep(
    *,
    headings_deg: tuple[float, ...] = DEFAULT_HEADINGS_DEG,
    shape: tuple[int, int] = (101, 101),
    cell_size_m: float = 30.0,
) -> list[BenchmarkResult]:
    """Sweep physical heading while holding grid, fuel, wind magnitude, and domain fixed."""

    results: list[BenchmarkResult] = []
    for heading in headings_deg:
        results.extend(
            run_neighborhood_comparison(
                shape=shape,
                cell_size_m=cell_size_m,
                head_direction_deg=heading,
            )
        )
    return results


def run_cell_size_sweep(
    *,
    cell_sizes_m: tuple[float, ...] = DEFAULT_CELL_SIZES_M,
    half_extent_m: float = 600.0,
    head_direction_deg: float = 30.0,
) -> list[BenchmarkResult]:
    """Sweep cell size while preserving the same physical center-to-edge extent."""

    results: list[BenchmarkResult] = []
    for cell_size in cell_sizes_m:
        shape = centered_square_shape(
            half_extent_m=half_extent_m,
            cell_size_m=cell_size,
        )
        results.extend(
            run_neighborhood_comparison(
                shape=shape,
                cell_size_m=cell_size,
                head_direction_deg=head_direction_deg,
            )
        )
    return results


def _print_results(results: list[BenchmarkResult]) -> None:
    print("neighborhood,cell_size_m,head_deg,rows,cols,count,mae_s,rmse_s,bias_s,max_abs_s")
    for result in results:
        metrics = result.metrics
        print(
            f"{result.neighborhood},{result.cell_size_m:.1f},{result.head_direction_deg:.1f},"
            f"{result.shape[0]},{result.shape[1]},{metrics.count},"
            f"{metrics.mae_s:.6f},{metrics.rmse_s:.6f},"
            f"{metrics.bias_s:.6f},{metrics.max_abs_error_s:.6f}"
        )


def main() -> None:
    _print_results(run_neighborhood_comparison())


if __name__ == "__main__":
    main()
