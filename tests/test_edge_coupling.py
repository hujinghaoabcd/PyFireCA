from dataclasses import dataclass

import numpy as np
import pytest

from pyfireca.arrival import ConstantDirectionalSpreadRate, StaticArrivalTimeSolver
from pyfireca.edge_coupling import HalfCellInterfaceDirectionalSpreadRate
from pyfireca.neighborhood import VonNeumannNeighborhood


@dataclass(frozen=True, slots=True)
class ColumnDirectionalRate:
    rates_m_s: tuple[float, ...]

    def spread_rate_m_s(self, row: int, col: int, offset: tuple[int, int]) -> float:
        del row, offset
        return self.rates_m_s[col]


def test_half_cell_interface_returns_harmonic_mean_of_directional_rates() -> None:
    provider = HalfCellInterfaceDirectionalSpreadRate(ColumnDirectionalRate((2.0, 0.5)))

    observed = provider.spread_rate_m_s(0, 0, (0, 1))

    assert observed == pytest.approx(0.8)


def test_half_cell_interface_matches_sum_of_two_half_segment_travel_times() -> None:
    cell_size_m = 30.0
    source_rate = 2.0
    target_rate = 0.5
    provider = HalfCellInterfaceDirectionalSpreadRate(
        ColumnDirectionalRate((source_rate, target_rate))
    )
    equivalent_rate = provider.spread_rate_m_s(0, 0, (0, 1))

    via_equivalent_rate = cell_size_m / equivalent_rate
    via_two_half_segments = (cell_size_m / 2.0) / source_rate + (
        cell_size_m / 2.0
    ) / target_rate

    assert via_equivalent_rate == pytest.approx(via_two_half_segments)


def test_half_cell_interface_zero_rate_makes_edge_unreachable() -> None:
    provider = HalfCellInterfaceDirectionalSpreadRate(ColumnDirectionalRate((2.0, 0.0)))

    assert provider.spread_rate_m_s(0, 0, (0, 1)) == 0.0


def test_half_cell_interface_preserves_homogeneous_directional_rate() -> None:
    provider = HalfCellInterfaceDirectionalSpreadRate(ConstantDirectionalSpreadRate(0.25))

    assert provider.spread_rate_m_s(2, 3, (-1, 0)) == pytest.approx(0.25)


def test_arrival_solver_uses_interface_coupled_travel_time() -> None:
    domain = np.ones((1, 2), dtype=bool)
    ignition = np.array([[0.0, np.inf]], dtype=np.float64)
    provider = HalfCellInterfaceDirectionalSpreadRate(ColumnDirectionalRate((2.0, 0.5)))
    solver = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=30.0,
        spread_rate_provider=provider,
    )

    arrival = solver.solve(domain, ignition)

    assert arrival[0, 1] == pytest.approx(37.5)
