"""Minimal synchronous cellular-automata simulation orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from pyfireca.grid import RasterGrid
from pyfireca.rules import TransitionRule
from pyfireca.state import validate_state_array


@dataclass(slots=True)
class Simulation:
    """Run a synchronous cellular automaton on a :class:`RasterGrid`.

    The simulation owns orchestration state only: grid, transition rule,
    explicit RNG, and step counter. Scientific spread equations belong in
    rule/behavior modules rather than this class.
    """

    grid: RasterGrid
    rule: TransitionRule
    rng: np.random.Generator = field(default_factory=np.random.default_rng)
    step_index: int = 0

    @classmethod
    def from_seed(
        cls,
        grid: RasterGrid,
        rule: TransitionRule,
        *,
        seed: int | None = None,
    ) -> Simulation:
        """Construct a simulation with an explicit reproducible RNG seed."""

        return cls(grid=grid, rule=rule, rng=np.random.default_rng(seed))

    def step(self) -> None:
        """Advance the CA by exactly one synchronous update."""

        next_state = np.asarray(self.rule.next_state(self.grid, rng=self.rng))
        validate_state_array(next_state)
        if next_state.shape != self.grid.shape:
            raise ValueError(
                f"rule returned shape {next_state.shape}; expected grid shape {self.grid.shape}"
            )

        # Copy to prevent a rule-owned working array from becoming hidden
        # mutable simulation state after this method returns.
        self.grid.replace_state(next_state.copy())
        self.step_index += 1

    def run(self, steps: int) -> RasterGrid:
        """Run ``steps`` updates and return the mutated grid."""

        if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
            raise ValueError("steps must be a non-negative integer")

        for _ in range(steps):
            self.step()
        return self.grid
