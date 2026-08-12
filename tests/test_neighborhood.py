import pytest

from pyfireca.neighborhood import (
    MooreNeighborhood,
    VonNeumannNeighborhood,
    valid_neighbor_indices,
)


def test_moore_radius_one_has_eight_unique_offsets() -> None:
    offsets = MooreNeighborhood(radius=1).offsets()
    assert len(offsets) == 8
    assert len(set(offsets)) == 8
    assert (0, 0) not in offsets


def test_von_neumann_radius_one_has_four_unique_offsets() -> None:
    offsets = VonNeumannNeighborhood(radius=1).offsets()
    assert set(offsets) == {(-1, 0), (1, 0), (0, -1), (0, 1)}


@pytest.mark.parametrize("radius", [0, -1, 1.5, True])
def test_invalid_radius_is_rejected(radius: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        MooreNeighborhood(radius=radius)  # type: ignore[arg-type]


def test_boundary_policy_clips_out_of_bounds_neighbors() -> None:
    offsets = MooreNeighborhood(radius=1).offsets()
    neighbors = valid_neighbor_indices(0, 0, (3, 3), offsets)
    assert set(neighbors) == {(0, 1), (1, 0), (1, 1)}


def test_interior_cell_keeps_full_moore_neighborhood() -> None:
    offsets = MooreNeighborhood(radius=1).offsets()
    neighbors = valid_neighbor_indices(1, 1, (3, 3), offsets)
    assert len(neighbors) == 8


def test_neighbor_index_rejects_cell_outside_grid() -> None:
    with pytest.raises(IndexError, match="outside"):
        valid_neighbor_indices(3, 0, (3, 3), MooreNeighborhood().offsets())
