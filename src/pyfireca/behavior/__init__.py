"""Wildfire behavior interfaces and reference implementations."""

from pyfireca.behavior.base import FireBehaviorModel, FireBehaviorResult
from pyfireca.behavior.rothermel import (
    FuelClass,
    FuelClassValues,
    RothermelFuelModel,
    RothermelFuelMoisture,
    RothermelInputs,
)

__all__ = [
    "FireBehaviorModel",
    "FireBehaviorResult",
    "FuelClass",
    "FuelClassValues",
    "RothermelFuelModel",
    "RothermelFuelMoisture",
    "RothermelInputs",
]
