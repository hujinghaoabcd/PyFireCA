import numpy as np

from pyfireca.grid import RasterGrid
from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood
from pyfireca.rules import NeighborIgnitionRule
from pyfireca.simulation import Simulation
from pyfireca.state import FireState


def _center_ignition_grid() -> RasterGrid:
    state = np.full((3, 3), FireState.UNBURNED, dtype=np.uint8)
    state[1, 1] = FireState.BURNING
    return RasterGrid(state)


def test_moore_reference_rule_ignites_all_eight_neighbors() -> None:
    sim = Simulation.from_seed(
        _center_ignition_grid(),
        NeighborIgnitionRule(MooreNeighborhood()),
        seed=42,
    )

    sim.step()

    assert sim.grid.state[1, 1] == FireState.BURNED
    assert np.count_nonzero(sim.grid.state == FireState.BURNING) == 8


def test_von_neumann_reference_rule_ignites_four_neighbors() -> None:
    sim = Simulation.from_seed(
        _center_ignition_grid(),
        NeighborIgnitionRule(VonNeumannNeighborhood()),
        seed=42,
    )

    sim.step()

    assert sim.grid.state[1, 1] == FireState.BURNED
    assert np.count_nonzero(sim.grid.state == FireState.BURNING) == 4
    assert sim.grid.state[0, 0] == FireState.UNBURNED


def test_unburnable_cell_is_not_ignited() -> None:
    grid = _center_ignition_grid()
    grid.state[0, 0] = FireState.UNBURNABLE

    sim = Simulation.from_seed(
        grid,
        NeighborIgnitionRule(MooreNeighborhood()),
        seed=42,
    )
    sim.step()

    assert sim.grid.state[0, 0] == FireState.UNBURNABLE


def test_synchronous_update_prevents_same_step_cascade() -> None:
    state = np.full((1, 5), FireState.UNBURNED, dtype=np.uint8)
    state[0, 0] = FireState.BURNING
    sim = Simulation.from_seed(
        RasterGrid(state),
        NeighborIgnitionRule(VonNeumannNeighborhood()),
        seed=42,
    )

    sim.step()

    assert np.array_equal(
        sim.grid.state,
        np.array(
            [
                [
                    FireState.BURNED,
                    FireState.BURNING,
                    FireState.UNBURNED,
                    FireState.UNBURNED,
                    FireState.UNBURNED,
                ]
            ],
            dtype=np.uint8,
        ),
    )
