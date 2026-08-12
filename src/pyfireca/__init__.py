"""PyFireCA: extensible cellular automata for wildfire spread research."""

from pyfireca.arrival import (
    ConstantDirectionalSpreadRate,
    DirectionalSpreadRateProvider,
    StaticArrivalTimeSolver,
    arrival_times_to_state,
)
from pyfireca.behavior.rothermel_landscape import build_static_raster_rothermel_arrival_solver
from pyfireca.data import LandscapeInput
from pyfireca.edge_coupling import HalfCellInterfaceDirectionalSpreadRate
from pyfireca.grid import RasterGrid
from pyfireca.ignition import IgnitionEvent, build_ignition_times
from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood
from pyfireca.rules import NeighborIgnitionRule
from pyfireca.simulation import Simulation
from pyfireca.simulator import (
    StaticWildfireSimulationRequest,
    StaticWildfireSimulationResult,
    run_static_wildfire_simulation,
)
from pyfireca.state import FireState

__all__ = [
    "ConstantDirectionalSpreadRate",
    "DirectionalSpreadRateProvider",
    "FireState",
    "HalfCellInterfaceDirectionalSpreadRate",
    "IgnitionEvent",
    "LandscapeInput",
    "MooreNeighborhood",
    "NeighborIgnitionRule",
    "RasterGrid",
    "Simulation",
    "StaticArrivalTimeSolver",
    "StaticWildfireSimulationRequest",
    "StaticWildfireSimulationResult",
    "VonNeumannNeighborhood",
    "arrival_times_to_state",
    "build_ignition_times",
    "build_static_raster_rothermel_arrival_solver",
    "run_static_wildfire_simulation",
]

__version__ = "0.1.0a0"
