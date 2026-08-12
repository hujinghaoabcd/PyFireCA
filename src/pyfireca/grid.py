"""Raster grid container for PyFireCA state arrays."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from pyfireca.state import validate_state_array


@dataclass(slots=True)
class RasterGrid:
    """A minimal raster lattice holding the current wildfire CA state.

    Parameters
    ----------
    state
        Two-dimensional integer array with shape ``(H, W)``.
    cell_size
        Optional cell size in model distance units. Geospatial transform/CRS
        metadata will be introduced with the GIS data contract rather than
        being guessed here.
    """

    state: NDArray[np.integer]
    cell_size: float | None = None

    def __post_init__(self) -> None:
        self.state = np.asarray(self.state)
        validate_state_array(self.state)
        if self.cell_size is not None and self.cell_size <= 0:
            raise ValueError("cell_size must be positive when provided")

    @property
    def shape(self) -> tuple[int, int]:
        """Return raster shape as ``(height, width)``."""

        height, width = self.state.shape
        return int(height), int(width)

    def replace_state(self, state: NDArray[np.integer]) -> None:
        """Replace the current state after validating shape and state codes."""

        state = np.asarray(state)
        validate_state_array(state)
        if state.shape != self.state.shape:
            raise ValueError(
                "replacement state shape "
                f"{state.shape} does not match grid shape {self.state.shape}"
            )
        self.state = state

    def copy(self) -> RasterGrid:
        """Return an independent copy of the grid and its state array."""

        return RasterGrid(state=self.state.copy(), cell_size=self.cell_size)
