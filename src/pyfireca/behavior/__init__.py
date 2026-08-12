"""Wildfire behavior interfaces and reference implementations."""

from pyfireca.behavior.base import FireBehaviorModel, FireBehaviorResult
from pyfireca.behavior.crown import (
    CrownFireType,
    CruzCrownFireModel,
    CruzCrownInputs,
    cruz_active_crown_ros_m_min,
    cruz_passive_crown_ros_m_min,
    van_wagner_critical_crown_ros_m_min,
    van_wagner_critical_fireline_intensity_w_m,
)
from pyfireca.behavior.fbp import (
    FBPComputation,
    FBPFireType,
    FBPInputs,
    FBPModel,
    normalize_fbp_fuel_type,
)
from pyfireca.behavior.fbp_directional import (
    FBPEllipse,
    HomogeneousFBPDirectionalSpreadRate,
)
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
    "CrownFireType",
    "CruzCrownFireModel",
    "CruzCrownInputs",
    "FBPComputation",
    "FBPEllipse",
    "FBPFireType",
    "FBPInputs",
    "FBPModel",
    "FireBehaviorModel",
    "FireBehaviorResult",
    "FuelClass",
    "FuelClassValues",
    "HomogeneousFBPDirectionalSpreadRate",
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
    "cruz_active_crown_ros_m_min",
    "cruz_passive_crown_ros_m_min",
    "get_standard_fuel_model",
    "get_standard_fuel_model_record",
    "normalize_fbp_fuel_type",
    "van_wagner_critical_crown_ros_m_min",
    "van_wagner_critical_fireline_intensity_w_m",
]
