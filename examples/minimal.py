"""Run the minimal deterministic PyFireCA reference cellular automaton."""

import numpy as np

from pyfireca.grid import RasterGrid
from pyfireca.neighborhood import MooreNeighborhood
from pyfireca.rules import NeighborIgnitionRule
from pyfireca.simulation import Simulation
from pyfireca.state import FireState

state = np.full((7, 7), FireState.UNBURNED, dtype=np.uint8)
state[3, 3] = FireState.BURNING

grid = RasterGrid(state=state, cell_size=30.0)
rule = NeighborIgnitionRule(neighborhood=MooreNeighborhood(radius=1))
simulation = Simulation.from_seed(grid=grid, rule=rule, seed=42)

for _ in range(3):
    simulation.step()
    print(f"step={simulation.step_index}")
    print(simulation.grid.state)
