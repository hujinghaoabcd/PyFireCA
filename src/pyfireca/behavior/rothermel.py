"""Typed inputs and reference calculations for Rothermel surface fire.

PyFireCA exposes SI units at the public behavior boundary. Scientific
calculations are introduced incrementally and validated before the complete
rate-of-spread model is assembled.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from math import isfinite

from pyfireca.behavior._units import m_inv_to_ft_inv

FuelClassValues = tuple[float, float, float, float, float, float]
FuelCategoryValues = tuple[float, float]


class FuelClass(IntEnum):
    """Fixed six-class ordering used by the Rothermel fuel representation."""

    DEAD_1H = 0
    DEAD_10H = 1
    DEAD_100H = 2
    DEAD_HERBACEOUS = 3
    LIVE_HERBACEOUS = 4
    LIVE_WOODY = 5


def _validate_finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def _validate_nonnegative(name: str, value: float) -> None:
    _validate_finite(name, value)
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")


def _validate_fraction(name: str, value: float, *, upper_bound: bool = True) -> None:
    _validate_nonnegative(name, value)
    if upper_bound and value > 1.0:
        raise ValueError(f"{name} must be in [0, 1]")


def _validate_six_values(
    name: str,
    values: FuelClassValues,
    *,
    fraction: bool = False,
) -> None:
    if len(values) != len(FuelClass):
        raise ValueError(f"{name} must contain exactly six fuel-class values")

    for index, value in enumerate(values):
        label = f"{name}[{FuelClass(index).name}]"
        if fraction:
            _validate_fraction(label, float(value))
        else:
            _validate_nonnegative(label, float(value))


@dataclass(frozen=True, slots=True)
class RothermelFuelModel:
    """One six-class surface-fuel model expressed in SI units.

    Parameters
    ----------
    code
        Positive model identifier. This may later map to standard Anderson or
        Scott--Burgan model numbers, but the dataclass itself is not tied to a
        specific catalogue.
    depth_m
        Fuel-bed depth in metres.
    dead_moisture_of_extinction_fraction
        Dead-fuel moisture of extinction as dry-mass fraction.
    loads_kg_m2
        Oven-dry fuel load for the six classes, in kg/m².
    sav_ratio_m_inv
        Surface-area-to-volume ratio for each class, in 1/m.
    heat_content_j_kg
        Low heat content for each class, in J/kg.
    particle_density_kg_m3
        Oven-dry particle density for each class, in kg/m³.
    total_mineral_fraction
        Total mineral content as dry-mass fraction for each class.
    effective_mineral_fraction
        Effective mineral content as dry-mass fraction for each class.
    dynamic
        Whether live herbaceous loading may later be redistributed between
        live and dead herbaceous classes by a dynamic-fuel procedure.
    burnable
        Whether the model represents combustible fuel. Nonburnable models may
        contain zero depth/load/property values.
    """

    code: int
    depth_m: float
    dead_moisture_of_extinction_fraction: float
    loads_kg_m2: FuelClassValues
    sav_ratio_m_inv: FuelClassValues
    heat_content_j_kg: FuelClassValues
    particle_density_kg_m3: FuelClassValues
    total_mineral_fraction: FuelClassValues
    effective_mineral_fraction: FuelClassValues
    dynamic: bool = False
    burnable: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.code, bool) or not isinstance(self.code, int) or self.code <= 0:
            raise ValueError("code must be a positive integer")

        _validate_nonnegative("depth_m", self.depth_m)
        _validate_nonnegative(
            "dead_moisture_of_extinction_fraction",
            self.dead_moisture_of_extinction_fraction,
        )
        _validate_six_values("loads_kg_m2", self.loads_kg_m2)
        _validate_six_values("sav_ratio_m_inv", self.sav_ratio_m_inv)
        _validate_six_values("heat_content_j_kg", self.heat_content_j_kg)
        _validate_six_values("particle_density_kg_m3", self.particle_density_kg_m3)
        _validate_six_values(
            "total_mineral_fraction",
            self.total_mineral_fraction,
            fraction=True,
        )
        _validate_six_values(
            "effective_mineral_fraction",
            self.effective_mineral_fraction,
            fraction=True,
        )

        total_load = sum(float(value) for value in self.loads_kg_m2)
        if self.burnable:
            if self.depth_m <= 0.0:
                raise ValueError("a burnable fuel model must have positive depth_m")
            if self.dead_moisture_of_extinction_fraction <= 0.0:
                raise ValueError(
                    "a burnable fuel model must have positive dead moisture of extinction"
                )
            if total_load <= 0.0:
                raise ValueError("a burnable fuel model must have positive total fuel load")

        for fuel_class in FuelClass:
            index = int(fuel_class)
            if self.loads_kg_m2[index] <= 0.0:
                continue
            if self.sav_ratio_m_inv[index] <= 0.0:
                raise ValueError(f"loaded class {fuel_class.name} must have positive SAV ratio")
            if self.heat_content_j_kg[index] <= 0.0:
                raise ValueError(f"loaded class {fuel_class.name} must have positive heat content")
            if self.particle_density_kg_m3[index] <= 0.0:
                raise ValueError(
                    f"loaded class {fuel_class.name} must have positive particle density"
                )


@dataclass(frozen=True, slots=True)
class RothermelFuelMoisture:
    """Fuel-moisture inputs as dry-mass fractions.

    Live fuel moisture may exceed ``1.0`` (100 percent dry-mass basis), so the
    fields are constrained only to finite, non-negative values.
    """

    dead_1h_fraction: float
    dead_10h_fraction: float
    dead_100h_fraction: float
    live_herbaceous_fraction: float
    live_woody_fraction: float

    def __post_init__(self) -> None:
        for name in (
            "dead_1h_fraction",
            "dead_10h_fraction",
            "dead_100h_fraction",
            "live_herbaceous_fraction",
            "live_woody_fraction",
        ):
            _validate_nonnegative(name, getattr(self, name))

    def as_six_class_values(self) -> FuelClassValues:
        """Return moisture values in the fixed six-class fuel ordering.

        The initial dead-herbaceous moisture convention follows dead 1-h fuel.
        Dynamic load redistribution itself is deliberately implemented later.
        """

        return (
            self.dead_1h_fraction,
            self.dead_10h_fraction,
            self.dead_100h_fraction,
            self.dead_1h_fraction,
            self.live_herbaceous_fraction,
            self.live_woody_fraction,
        )


@dataclass(frozen=True, slots=True)
class RothermelInputs:
    """Scalar environmental inputs for one Rothermel behavior calculation.

    Wind is expressed as **midflame** speed. Converting 10-m or 20-ft wind to
    midflame wind belongs in an explicit preprocessing/adjustment layer rather
    than being hidden inside this input contract.
    """

    fuel: RothermelFuelModel
    moisture: RothermelFuelMoisture
    midflame_wind_speed_m_s: float
    wind_from_direction_deg: float
    slope_deg: float
    aspect_deg: float

    def __post_init__(self) -> None:
        if not isinstance(self.fuel, RothermelFuelModel):
            raise TypeError("fuel must be a RothermelFuelModel")
        if not isinstance(self.moisture, RothermelFuelMoisture):
            raise TypeError("moisture must be RothermelFuelMoisture")

        _validate_nonnegative("midflame_wind_speed_m_s", self.midflame_wind_speed_m_s)
        _validate_direction("wind_from_direction_deg", self.wind_from_direction_deg)
        _validate_direction("aspect_deg", self.aspect_deg)
        _validate_finite("slope_deg", self.slope_deg)
        if not 0.0 <= self.slope_deg < 90.0:
            raise ValueError("slope_deg must be in [0, 90)")


def _validate_direction(name: str, value: float) -> None:
    _validate_finite(name, value)
    if not 0.0 <= value < 360.0:
        raise ValueError(f"{name} must be in [0, 360)")


def compute_surface_area_weights(
    fuel: RothermelFuelModel,
) -> tuple[FuelClassValues, FuelCategoryValues]:
    """Compute Rothermel surface-area weighting factors.

    The six within-category weights correspond to ``f_ij`` in Rothermel's
    heterogeneous-fuel formulation. The two category weights correspond to
    dead and live ``f_i`` respectively.
    """

    surface_areas: list[float] = []
    for fuel_class in FuelClass:
        index = int(fuel_class)
        load = fuel.loads_kg_m2[index]
        if load <= 0.0:
            surface_areas.append(0.0)
            continue
        surface_areas.append(
            fuel.sav_ratio_m_inv[index]
            * load
            / fuel.particle_density_kg_m3[index]
        )

    dead_area = sum(surface_areas[:4])
    live_area = sum(surface_areas[4:])
    total_area = dead_area + live_area

    within = tuple(
        area / (dead_area if index < 4 else live_area)
        if (dead_area if index < 4 else live_area) > 0.0
        else 0.0
        for index, area in enumerate(surface_areas)
    )
    categories: FuelCategoryValues
    if total_area > 0.0:
        categories = (dead_area / total_area, live_area / total_area)
    else:
        categories = (0.0, 0.0)

    return within, categories  # type: ignore[return-value]


def compute_characteristic_sav_m_inv(fuel: RothermelFuelModel) -> float:
    """Return the surface-area-weighted characteristic SAV ratio in 1/m."""

    within, categories = compute_surface_area_weights(fuel)
    dead_sav = sum(
        within[index] * fuel.sav_ratio_m_inv[index] for index in range(4)
    )
    live_sav = sum(
        within[index] * fuel.sav_ratio_m_inv[index] for index in range(4, 6)
    )
    return categories[0] * dead_sav + categories[1] * live_sav


def compute_packing_ratio(fuel: RothermelFuelModel) -> float:
    """Return mean fuel-bed packing ratio as a dimensionless fraction."""

    if fuel.depth_m <= 0.0:
        return 0.0

    occupied_depth = 0.0
    for fuel_class in FuelClass:
        index = int(fuel_class)
        load = fuel.loads_kg_m2[index]
        if load > 0.0:
            occupied_depth += load / fuel.particle_density_kg_m3[index]
    return occupied_depth / fuel.depth_m


def compute_bulk_density_kg_m3(fuel: RothermelFuelModel) -> float:
    """Return oven-dry fuel-bed bulk density in kg/m³."""

    if fuel.depth_m <= 0.0:
        return 0.0
    return sum(fuel.loads_kg_m2) / fuel.depth_m


def compute_optimum_packing_ratio(characteristic_sav_m_inv: float) -> float:
    """Return optimum packing ratio from Rothermel's characteristic SAV.

    The published correlation uses inverse feet, so the SI characteristic SAV
    is converted explicitly before evaluating the dimensionless equation.
    """

    _validate_nonnegative("characteristic_sav_m_inv", characteristic_sav_m_inv)
    if characteristic_sav_m_inv == 0.0:
        return 0.0
    sav_ft_inv = m_inv_to_ft_inv(characteristic_sav_m_inv)
    return 3.348 * sav_ft_inv**-0.8189
