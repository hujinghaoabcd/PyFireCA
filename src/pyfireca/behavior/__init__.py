"""Wildfire behavior interfaces and reference implementations."""

from pyfireca.behavior.base import FireBehaviorModel, FireBehaviorResult
from pyfireca.behavior.fuel_catalog import (
    StandardFuelModelRecord,
    available_standard_fuel_model_numbers,
    get_standard_fuel_model,
    get_standard_fuel_model_record,
)
from pyfireca.behavior.rothermel import (
    FuelClass,
    FuelClassValues,
    RothermelFuelModel,
    RothermelFuelMoisture,
    RothermelInputs,
)
from pyfireca.behavior.rothermel_directional import HomogeneousRothermelDirectionalSpreadRate
from pyfireca.behavior.rothermel_model import RothermelModel

__all__ = [
    "FireBehaviorModel",
    "FireBehaviorResult",
    "FuelClass",
    "FuelClassValues",
    "HomogeneousRothermelDirectionalSpreadRate",
    "RothermelFuelModel",
    "RothermelFuelMoisture",
    "RothermelInputs",
    "RothermelModel",
    "StandardFuelModelRecord",
    "available_standard_fuel_model_numbers",
    "get_standard_fuel_model",
    "get_standard_fuel_model_record",
]
