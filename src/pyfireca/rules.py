"""Transition-rule contracts for cellular-automata updates."""

from __future__ import annotations

from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from pyfireca.grid import RasterGrid


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
