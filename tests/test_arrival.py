from math import inf, sqrt

import numpy as np
import pytest

from pyfireca.arrival import ConstantDirectionalSpreadRate, StaticArrivalTimeSolver
from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood


def _seed(shape: tuple[int, int], *items: tuple[int, int, float]) -> np.ndarray:
    ignition = np.full(shape, np.inf, dtype=np.float64)
    for row, col, time_s in items:
        ignition[row, col] = time_s
    return ignition


def test_constant_moore_rate_produces_cardinal_and_diagonal_arrival_times() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=MooreNeighborhood(),
        cell_size_m=30.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(0.1),
    )
    domain = np.ones((3, 3), dtype=bool)

    arrival = solver.solve(domain, _seed((3, 3), (1, 1, 0.0)))

    assert arrival[1, 1] == 0.0
    assert arrival[0, 1] == pytest.approx(300.0)
    assert arrival[1, 2] == pytest.approx(300.0)
    assert arrival[0, 0] == pytest.approx(300.0 * sqrt(2.0))


def test_von_neumann_corner_requires_two_cardinal_edges() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=10.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(1.0),
    )
    domain = np.ones((3, 3), dtype=bool)

    arrival = solver.solve(domain, _seed((3, 3), (1, 1, 0.0)))

    assert arrival[0, 0] == pytest.approx(20.0)


def test_domain_barrier_is_respected_but_solver_can_route_around_it() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=1.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(1.0),
    )
    domain = np.ones((3, 3), dtype=bool)
    domain[1, 1] = False

    arrival = solver.solve(domain, _seed((3, 3), (1, 0, 0.0)))

    assert arrival[1, 1] == inf
    assert arrival[1, 2] == pytest.approx(4.0)


def test_multiple_external_ignitions_take_the_earliest_reachable_time() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=10.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(1.0),
    )
    domain = np.ones((1, 5), dtype=bool)
    ignition = _seed((1, 5), (0, 0, 0.0), (0, 4, 5.0))

    arrival = solver.solve(domain, ignition)

    assert arrival.tolist() == pytest.approx([0.0, 10.0, 20.0, 15.0, 5.0])


def test_zero_edge_ros_leaves_unseeded_cells_unreachable() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=MooreNeighborhood(),
        cell_size_m=30.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(0.0),
    )
    domain = np.ones((2, 2), dtype=bool)

    arrival = solver.solve(domain, _seed((2, 2), (0, 0, 0.0)))

    assert arrival[0, 0] == 0.0
    assert np.isinf(arrival[0, 1])
    assert np.isinf(arrival[1, 0])
    assert np.isinf(arrival[1, 1])


def test_no_external_ignitions_returns_all_infinite_arrival_times() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=MooreNeighborhood(),
        cell_size_m=30.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(0.1),
    )
    domain = np.ones((2, 2), dtype=bool)

    arrival = solver.solve(domain, _seed((2, 2)))

    assert np.isinf(arrival).all()


class EastFastProvider:
    def spread_rate_m_s(self, row: int, col: int, offset: tuple[int, int]) -> float:
        del row, col
        if offset == (0, 1):
            return 2.0
        if offset == (0, -1):
            return 0.5
        return 1.0


def test_provider_may_supply_direction_dependent_edge_rates() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=10.0,
        spread_rate_provider=EastFastProvider(),
    )
    domain = np.ones((1, 3), dtype=bool)

    arrival = solver.solve(domain, _seed((1, 3), (0, 1, 0.0)))

    assert arrival[0, 2] == pytest.approx(5.0)
    assert arrival[0, 0] == pytest.approx(20.0)


class InvalidProvider:
    def spread_rate_m_s(self, row: int, col: int, offset: tuple[int, int]) -> float:
        del row, col, offset
        return -1.0


def test_invalid_provider_rate_fails_at_the_exact_edge_evaluation() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=VonNeumannNeighborhood(),
        cell_size_m=10.0,
        spread_rate_provider=InvalidProvider(),
    )
    domain = np.ones((1, 2), dtype=bool)

    with pytest.raises(ValueError, match="non-finite or negative ROS"):
        solver.solve(domain, _seed((1, 2), (0, 0, 0.0)))


def test_finite_ignition_outside_domain_is_rejected() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=MooreNeighborhood(),
        cell_size_m=1.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(1.0),
    )
    domain = np.array([[False, True]], dtype=bool)

    with pytest.raises(ValueError, match="inside the domain"):
        solver.solve(domain, _seed((1, 2), (0, 0, 0.0)))


@pytest.mark.parametrize("bad_value", [-1.0, float("nan"), float("-inf")])
def test_invalid_ignition_times_are_rejected(bad_value: float) -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=MooreNeighborhood(),
        cell_size_m=1.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(1.0),
    )
    domain = np.ones((1, 1), dtype=bool)
    ignition = np.array([[bad_value]], dtype=np.float64)

    with pytest.raises(ValueError):
        solver.solve(domain, ignition)


def test_shape_and_domain_type_contracts_are_explicit() -> None:
    solver = StaticArrivalTimeSolver(
        neighborhood=MooreNeighborhood(),
        cell_size_m=1.0,
        spread_rate_provider=ConstantDirectionalSpreadRate(1.0),
    )

    with pytest.raises(TypeError, match="boolean"):
        solver.solve(np.ones((2, 2), dtype=np.int8), _seed((2, 2)))
    with pytest.raises(ValueError, match="shape"):
        solver.solve(np.ones((2, 2), dtype=bool), _seed((2, 3)))


def test_solver_and_constant_provider_validate_construction() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ConstantDirectionalSpreadRate(-1.0)
    with pytest.raises(ValueError, match="positive"):
        StaticArrivalTimeSolver(
            neighborhood=MooreNeighborhood(),
            cell_size_m=0.0,
            spread_rate_provider=ConstantDirectionalSpreadRate(1.0),
        )
