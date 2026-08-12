import numpy as np
import pytest

from pyfireca.grid import RasterGrid
from pyfireca.simulation import Simulation
from pyfireca.state import FireState


class BurnEverythingRule:
    def next_state(
        self,
        grid: RasterGrid,
        *,
        rng: np.random.Generator,
    ) -> np.ndarray:
        next_state = grid.state.copy()
        next_state[next_state == FireState.UNBURNED] = FireState.BURNING
        return next_state


class BadShapeRule:
    def next_state(
        self,
        grid: RasterGrid,
        *,
        rng: np.random.Generator,
    ) -> np.ndarray:
        return np.zeros((1, 1), dtype=np.uint8)


def test_simulation_applies_one_synchronous_state_replacement() -> None:
    grid = RasterGrid(np.full((2, 2), FireState.UNBURNED, dtype=np.uint8))
    sim = Simulation.from_seed(grid, BurnEverythingRule(), seed=42)

    sim.step()

    assert sim.step_index == 1
    assert np.all(sim.grid.state == FireState.BURNING)


def test_run_rejects_negative_steps() -> None:
    grid = RasterGrid(np.full((2, 2), FireState.UNBURNED, dtype=np.uint8))
    sim = Simulation.from_seed(grid, BurnEverythingRule(), seed=42)

    with pytest.raises(ValueError, match="non-negative"):
        sim.run(-1)


def test_rule_output_shape_is_validated() -> None:
    grid = RasterGrid(np.full((2, 2), FireState.UNBURNED, dtype=np.uint8))
    sim = Simulation.from_seed(grid, BadShapeRule(), seed=42)

    with pytest.raises(ValueError, match="expected grid shape"):
        sim.step()
