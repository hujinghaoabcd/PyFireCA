"""Reference constants for the self-contained Canadian FBP implementation.

The numerical parameters follow the Canadian Forest Fire Behavior Prediction
System (FCFDG 1992) with the revisions documented by Wotton, Alexander, and
Taylor (2009).  PyFireCA keeps its own runtime tables; no external FBP package
is imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class FBPFuelParameters:
    """Fuel-type coefficients used by the scalar FBP equations."""

    a: float | None
    b: float | None
    c: float | None
    q: float
    bui0: float | None
    be_max: float
    canopy_base_height_m: float
    crown_fuel_load_kg_m2: float
    stand_height_m: float


_FUEL_PARAMETERS = {
    "C1": FBPFuelParameters(90.0, 0.0649, 4.5, 0.90, 72.0, 1.076, 2.0, 0.75, 10.0),
    "C2": FBPFuelParameters(110.0, 0.0282, 1.5, 0.70, 64.0, 1.321, 3.0, 0.80, 7.0),
    "C3": FBPFuelParameters(110.0, 0.0444, 3.0, 0.75, 62.0, 1.261, 8.0, 1.15, 18.0),
    "C4": FBPFuelParameters(110.0, 0.0293, 1.5, 0.80, 66.0, 1.184, 4.0, 1.20, 10.0),
    "C5": FBPFuelParameters(30.0, 0.0697, 4.0, 0.80, 56.0, 1.220, 18.0, 1.20, 25.0),
    "C6": FBPFuelParameters(30.0, 0.0800, 3.0, 0.80, 62.0, 1.197, 7.0, 1.80, 14.0),
    "C7": FBPFuelParameters(45.0, 0.0305, 2.0, 0.85, 106.0, 1.134, 10.0, 0.50, 20.0),
    "D1": FBPFuelParameters(30.0, 0.0232, 1.6, 0.90, 32.0, 1.179, 0.0, 0.0, 0.0),
    "D2": FBPFuelParameters(30.0, 0.0232, 1.6, 0.90, 32.0, 1.179, 0.0, 0.0, 0.0),
    "M1": FBPFuelParameters(None, None, None, 0.80, 50.0, 1.250, 6.0, 0.80, 13.0),
    "M2": FBPFuelParameters(None, None, None, 0.80, 50.0, 1.250, 6.0, 0.80, 13.0),
    "M3": FBPFuelParameters(120.0, 0.0572, 1.4, 0.80, 50.0, 1.250, 6.0, 0.80, 8.0),
    "M4": FBPFuelParameters(100.0, 0.0404, 1.48, 0.80, 50.0, 1.250, 6.0, 0.80, 8.0),
    "O1A": FBPFuelParameters(190.0, 0.0310, 1.4, 1.00, None, 1.000, 0.0, 0.0, 0.0),
    "O1B": FBPFuelParameters(250.0, 0.0350, 1.7, 1.00, None, 1.000, 0.0, 0.0, 0.0),
    "S1": FBPFuelParameters(75.0, 0.0297, 1.3, 0.75, 38.0, 1.460, 0.0, 0.0, 0.0),
    "S2": FBPFuelParameters(40.0, 0.0438, 1.7, 0.75, 63.0, 1.256, 0.0, 0.0, 0.0),
    "S3": FBPFuelParameters(55.0, 0.0829, 3.2, 0.75, 31.0, 1.590, 0.0, 0.0, 0.0),
}

FBP_FUEL_PARAMETERS = MappingProxyType(_FUEL_PARAMETERS)

FBP_FUEL_TYPES = tuple(_FUEL_PARAMETERS)
FBP_NON_CROWNING_FUEL_TYPES = frozenset({"D1", "D2", "O1A", "O1B", "S1", "S2", "S3"})
FBP_GRASS_FUEL_TYPES = frozenset({"O1A", "O1B"})
FBP_NON_FUEL_TYPES = frozenset({"NF", "WA"})

# Exact coefficient used in the FBP/FWI FFMC moisture-content conversion.
FBP_FFMC_MOISTURE_COEFFICIENT = 250.0 * (59.5 / 101.0)
