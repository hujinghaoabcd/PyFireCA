import numpy as np
import pytest

from pyfireca.grid import RasterGrid
from pyfireca.state import FireState


def test_grid_reports_state_shape() -> None:
    grid = RasterGrid(np.full((3, 5), FireState.UNBURNED, dtype=np.uint8))
    assert grid.shape == (3, 5)


def test_grid_rejects_non_positive_cell_size() -> None:
    with pytest.raises(ValueError, match="cell_size"):
        RasterGrid(
            np.full((2, 2), FireState.UNBURNED, dtype=np.uint8),
            cell_size=0.0,
        )


def test_replace_state_requires_matching_shape() -> None:
    grid = RasterGrid(np.full((2, 2), FireState.UNBURNED, dtype=np.uint8))

    with pytest.raises(ValueError, match="does not match"):
        grid.replace_state(np.full((3, 3), FireState.UNBURNED, dtype=np.uint8))


def test_copy_has_independent_state_array() -> None:
    grid = RasterGrid(np.full((2, 2), FireState.UNBURNED, dtype=np.uint8))
    copied = grid.copy()

    copied.state[0, 0] = FireState.BURNING

    assert grid.state[0, 0] == FireState.UNBURNED
    assert copied.state[0, 0] == FireState.BURNING
