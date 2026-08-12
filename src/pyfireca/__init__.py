"""PyFireCA: extensible cellular automata for wildfire spread research."""

from pyfireca.arrival import (
    ConstantDirectionalSpreadRate,
    DirectionalSpreadRateProvider,
    StaticArrivalTimeSolver,
    arrival_times_to_state,
)
from pyfireca.data import LandscapeInput
from pyfireca.grid import RasterGrid
from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood
from pyfireca.rules import NeighborIgnitionRule
from pyfireca.simulation import Simulation
from pyfireca.state import FireState

__all__ = [
    "ConstantDirectionalSpreadRate",
    "DirectionalSpreadRateProvider",
    "FireState",
    "LandscapeInput",
    "MooreNeighborhood",
    "NeighborIgnitionRule",
    "RasterGrid",
    "Simulation",
    "StaticArrivalTimeSolver",
    "VonNeumannNeighborhood",
    "arrival_times_to_state",
]

__version__ = "0.1.0a0"
