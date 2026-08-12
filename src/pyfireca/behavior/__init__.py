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
from pyfireca.behavior.rothermel_landscape import build_static_raster_rothermel_arrival_solver
from pyfireca.behavior.rothermel_layers import (
    RothermelRasterLayerNames,
    StaticRasterRothermelInputsProvider,
)
from pyfireca.behavior.rothermel_model import RothermelModel
from pyfireca.behavior.rothermel_spatial import StaticSpatialRothermelDirectionalSpreadRate

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
    "RothermelRasterLayerNames",
    "StandardFuelModelRecord",
    "StaticRasterRothermelInputsProvider",
    "StaticSpatialRothermelDirectionalSpreadRate",
    "available_standard_fuel_model_numbers",
    "build_static_raster_rothermel_arrival_solver",
    "get_standard_fuel_model",
    "get_standard_fuel_model_record",
]
