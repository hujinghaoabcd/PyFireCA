"""PyFireCA: extensible cellular automata for wildfire spread research."""

from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood
from pyfireca.state import FireState

__all__ = ["FireState", "MooreNeighborhood", "VonNeumannNeighborhood"]

__version__ = "0.1.0a0"
