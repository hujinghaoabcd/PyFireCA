"""PyFireCA: extensible cellular automata for wildfire spread research."""

from pyfireca.arrival import (
    ConstantDirectionalSpreadRate,
    DirectionalSpreadRateProvider,
    StaticArrivalTimeSolver,
    arrival_times_to_state,
)
from pyfireca.behavior.crown import CruzCrownFireModel, CruzCrownInputs
from pyfireca.behavior.fbp import FBPComputation, FBPInputs, FBPModel
from pyfireca.behavior.fbp_directional import HomogeneousFBPDirectionalSpreadRate
from pyfireca.behavior.rothermel_landscape import build_static_raster_rothermel_arrival_solver
from pyfireca.config import StaticRasterInputPaths, StaticRunConfig, load_static_run_config
from pyfireca.data import LandscapeInput
from pyfireca.edge_coupling import HalfCellInterfaceDirectionalSpreadRate
from pyfireca.grid import RasterGrid
from pyfireca.ignition import IgnitionEvent, build_ignition_times
from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood
from pyfireca.outputs import (
    StaticSimulationOutputPaths,
    terminal_state_from_result,
    write_burned_perimeter_geojson,
    write_static_simulation_outputs,
)
from pyfireca.rules import NeighborIgnitionRule
from pyfireca.simulation import Simulation
from pyfireca.simulator import (
    StaticWildfireSimulationRequest,
    StaticWildfireSimulationResult,
    run_static_wildfire_simulation,
)
from pyfireca.state import FireState
from pyfireca.workflow import StaticRunArtifacts, run_static_config, validate_static_run

__all__ = [
    "ConstantDirectionalSpreadRate",
    "CruzCrownFireModel",
    "CruzCrownInputs",
    "DirectionalSpreadRateProvider",
    "FBPComputation",
    "FBPInputs",
    "FBPModel",
    "FireState",
    "HalfCellInterfaceDirectionalSpreadRate",
    "HomogeneousFBPDirectionalSpreadRate",
    "IgnitionEvent",
    "LandscapeInput",
    "MooreNeighborhood",
    "NeighborIgnitionRule",
    "RasterGrid",
    "Simulation",
    "StaticArrivalTimeSolver",
    "StaticRasterInputPaths",
    "StaticRunArtifacts",
    "StaticRunConfig",
    "StaticSimulationOutputPaths",
    "StaticWildfireSimulationRequest",
    "StaticWildfireSimulationResult",
    "VonNeumannNeighborhood",
    "arrival_times_to_state",
    "build_ignition_times",
    "build_static_raster_rothermel_arrival_solver",
    "load_static_run_config",
    "run_static_config",
    "run_static_wildfire_simulation",
    "terminal_state_from_result",
    "validate_static_run",
    "write_burned_perimeter_geojson",
    "write_static_simulation_outputs",
]

__version__ = "0.1.0a0"
