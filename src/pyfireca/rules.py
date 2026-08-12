"""Transition-rule contracts and reference wildfire CA rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from pyfireca.grid import RasterGrid
from pyfireca.neighborhood import Neighborhood, valid_neighbor_indices
from pyfireca.state import FireState


class TransitionRule(Protocol):
    """Protocol implemented by one synchronous CA transition rule.

    A rule reads the current grid and returns a complete next-state array.
    The simulation applies the returned array only after the rule finishes,
    which gives the initial reference engine explicit synchronous semantics.

    Future optimized/sparse rule APIs may be added only with regression tests
    showing equivalent model behavior.
    """

    def next_state(
        self,
        grid: RasterGrid,
        *,
        rng: np.random.Generator,
    ) -> NDArray[np.integer]:
        """Compute the next state without mutating ``grid.state``."""
        ...


@dataclass(frozen=True, slots=True)
class NeighborIgnitionRule:
    """Minimal deterministic wildfire CA rule used as a reference baseline.

    Each currently burning cell becomes burned. Every unburned neighbor of a
    currently burning cell becomes burning in the returned next-state array.
    Because all updates are computed from ``grid.state`` before replacement,
    newly ignited cells cannot ignite additional cells within the same step.

    This rule intentionally contains no Rothermel/FBP physics. Its purpose is
    to validate the CA architecture and provide a transparent regression
    baseline before scientifically richer spread rules are introduced.
    """

    neighborhood: Neighborhood

    def next_state(
        self,
        grid: RasterGrid,
        *,
        rng: np.random.Generator,
    ) -> NDArray[np.integer]:
        """Return one deterministic synchronous wildfire state update."""

        del rng  # Rule is deterministic but keeps the common rule signature.

        current = grid.state
        next_state = current.copy()
        burning_cells = np.argwhere(current == FireState.BURNING)

        for row, col in burning_cells:
            row_i = int(row)
            col_i = int(col)
            next_state[row_i, col_i] = FireState.BURNED

            for nr, nc in valid_neighbor_indices(
                row_i,
                col_i,
                grid.shape,
                self.neighborhood.offsets(),
            ):
                if current[nr, nc] == FireState.UNBURNED:
                    next_state[nr, nc] = FireState.BURNING

        return next_state
