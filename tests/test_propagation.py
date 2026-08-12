from math import inf, sqrt

import pytest

from pyfireca.propagation import (
    spread_travel_time_s,
    square_grid_neighbor_distance_m,
    square_grid_neighbor_travel_time_s,
)


def test_cardinal_neighbor_distance_equals_one_cell_size() -> None:
    for offset in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        assert square_grid_neighbor_distance_m(offset, 30.0) == pytest.approx(30.0)


def test_diagonal_neighbor_distance_uses_euclidean_geometry() -> None:
    for offset in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        assert square_grid_neighbor_distance_m(offset, 30.0) == pytest.approx(30.0 * sqrt(2.0))


def test_larger_neighborhood_offset_preserves_physical_distance() -> None:
    assert square_grid_neighbor_distance_m((2, -1), 20.0) == pytest.approx(20.0 * sqrt(5.0))


def test_travel_time_is_distance_divided_by_directional_ros() -> None:
    assert spread_travel_time_s(30.0, 0.1) == pytest.approx(300.0)
    assert square_grid_neighbor_travel_time_s((1, 1), 30.0, 0.1) == pytest.approx(300.0 * sqrt(2.0))


def test_zero_directional_ros_makes_positive_distance_unreachable() -> None:
    assert spread_travel_time_s(30.0, 0.0) == inf
    assert square_grid_neighbor_travel_time_s((0, 1), 30.0, 0.0) == inf


def test_zero_distance_has_zero_travel_time_even_with_zero_ros() -> None:
    assert spread_travel_time_s(0.0, 0.0) == 0.0


@pytest.mark.parametrize(
    ("distance", "rate"),
    [
        (-1.0, 0.1),
        (1.0, -0.1),
        (float("nan"), 0.1),
        (1.0, float("inf")),
    ],
)
def test_travel_time_rejects_invalid_physical_inputs(distance: float, rate: float) -> None:
    with pytest.raises(ValueError):
        spread_travel_time_s(distance, rate)


@pytest.mark.parametrize(
    "offset",
    [
        (0, 0),
    ],
)
def test_neighbor_distance_rejects_center(offset: tuple[int, int]) -> None:
    with pytest.raises(ValueError, match="center"):
        square_grid_neighbor_distance_m(offset, 30.0)


@pytest.mark.parametrize(
    "offset",
    [
        [1, 0],
        (1.0, 0),
        (True, 0),
        (1,),
    ],
)
def test_neighbor_distance_rejects_non_integer_offset_contract(offset: object) -> None:
    with pytest.raises(TypeError, match="two-integer"):
        square_grid_neighbor_distance_m(offset, 30.0)  # type: ignore[arg-type]


@pytest.mark.parametrize("cell_size", [0.0, -1.0, float("inf"), float("nan")])
def test_neighbor_distance_requires_positive_finite_cell_size(cell_size: float) -> None:
    with pytest.raises(ValueError, match="positive"):
        square_grid_neighbor_distance_m((0, 1), cell_size)
