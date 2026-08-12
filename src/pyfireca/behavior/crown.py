"""Self-contained Van Wagner + Cruz crown-fire behavior equations.

This module is intentionally independent from Pyretechnics and other wildfire
packages. The equations are implemented directly so the PyFireCA runtime remains
self-contained.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from math import exp, isfinite

from pyfireca.behavior.base import FireBehaviorResult


class CrownFireType(IntEnum):
    """Crown-fire regime returned by the Cruz model."""

    NONE = 0
    PASSIVE = 2
    ACTIVE = 3


def van_wagner_critical_fireline_intensity_w_m(
    canopy_base_height_m: float,
    foliar_moisture_fraction: float,
) -> float:
    """Return Van Wagner critical surface intensity for crown initiation.

    Parameters use metres and kg water per kg oven-dry foliage. The returned
    intensity is kW/m numerically converted to W/m.
    """

    if canopy_base_height_m < 0.0 or not isfinite(canopy_base_height_m):
        raise ValueError("canopy_base_height_m must be finite and non-negative")
    if foliar_moisture_fraction < 0.0 or not isfinite(foliar_moisture_fraction):
        raise ValueError("foliar_moisture_fraction must be finite and non-negative")

    heat_of_ignition_kj_kg = 460.0 + 2600.0 * foliar_moisture_fraction
    term = 0.01 * canopy_base_height_m * heat_of_ignition_kj_kg
    critical_kw_m = term * term**0.5
    return critical_kw_m * 1000.0


def van_wagner_crown_fire_initiates(
    surface_fireline_intensity_w_m: float,
    canopy_cover_fraction: float,
    canopy_base_height_m: float,
    foliar_moisture_fraction: float,
) -> bool:
    """Return whether a surface fire reaches the crown-initiation threshold."""

    if not isfinite(surface_fireline_intensity_w_m) or surface_fireline_intensity_w_m < 0.0:
        raise ValueError("surface_fireline_intensity_w_m must be finite and non-negative")
    if not isfinite(canopy_cover_fraction) or not 0.0 <= canopy_cover_fraction <= 1.0:
        raise ValueError("canopy_cover_fraction must be in [0, 1]")
    if canopy_cover_fraction <= 0.4 or surface_fireline_intensity_w_m <= 0.0:
        return False
    critical = van_wagner_critical_fireline_intensity_w_m(
        canopy_base_height_m,
        foliar_moisture_fraction,
    )
    return surface_fireline_intensity_w_m >= critical


def cruz_active_crown_ros_m_min(
    wind_speed_10m_kmh: float,
    canopy_bulk_density_kg_m3: float,
    fine_fuel_moisture_fraction: float,
) -> float:
    """Return Cruz et al. active crown-fire rate of spread in m/min."""

    if wind_speed_10m_kmh < 0.0 or not isfinite(wind_speed_10m_kmh):
        raise ValueError("wind_speed_10m_kmh must be finite and non-negative")
    if canopy_bulk_density_kg_m3 <= 0.0 or not isfinite(canopy_bulk_density_kg_m3):
        raise ValueError("canopy_bulk_density_kg_m3 must be finite and positive")
    if fine_fuel_moisture_fraction < 0.0 or not isfinite(fine_fuel_moisture_fraction):
        raise ValueError("fine_fuel_moisture_fraction must be finite and non-negative")
    return (
        11.02
        * wind_speed_10m_kmh**0.90
        * canopy_bulk_density_kg_m3**0.19
        * exp(-17.0 * fine_fuel_moisture_fraction)
    )


def van_wagner_critical_crown_ros_m_min(canopy_bulk_density_kg_m3: float) -> float:
    """Return critical ROS required to sustain active crown fire."""

    if canopy_bulk_density_kg_m3 <= 0.0 or not isfinite(canopy_bulk_density_kg_m3):
        raise ValueError("canopy_bulk_density_kg_m3 must be finite and positive")
    return 3.0 / canopy_bulk_density_kg_m3


def cruz_passive_crown_ros_m_min(
    active_crown_ros_m_min: float,
    critical_crown_ros_m_min: float,
) -> float:
    """Return passive-crown ROS from active and critical crown ROS."""

    if active_crown_ros_m_min < 0.0 or not isfinite(active_crown_ros_m_min):
        raise ValueError("active_crown_ros_m_min must be finite and non-negative")
    if critical_crown_ros_m_min <= 0.0 or not isfinite(critical_crown_ros_m_min):
        raise ValueError("critical_crown_ros_m_min must be finite and positive")
    return active_crown_ros_m_min * exp(-active_crown_ros_m_min / critical_crown_ros_m_min)


@dataclass(frozen=True, slots=True)
class CruzCrownInputs:
    """Native inputs for the Van Wagner/Cruz crown-fire behavior model."""

    surface_fireline_intensity_w_m: float
    canopy_cover_fraction: float
    canopy_base_height_m: float
    canopy_height_m: float
    canopy_bulk_density_kg_m3: float
    foliar_moisture_fraction: float
    fine_fuel_moisture_fraction: float
    wind_speed_10m_kmh: float
    downwind_direction_deg: float
    heat_of_combustion_kj_kg: float = 18_000.0

    def __post_init__(self) -> None:
        values = {
            "surface_fireline_intensity_w_m": self.surface_fireline_intensity_w_m,
            "canopy_cover_fraction": self.canopy_cover_fraction,
            "canopy_base_height_m": self.canopy_base_height_m,
            "canopy_height_m": self.canopy_height_m,
            "canopy_bulk_density_kg_m3": self.canopy_bulk_density_kg_m3,
            "foliar_moisture_fraction": self.foliar_moisture_fraction,
            "fine_fuel_moisture_fraction": self.fine_fuel_moisture_fraction,
            "wind_speed_10m_kmh": self.wind_speed_10m_kmh,
            "downwind_direction_deg": self.downwind_direction_deg,
            "heat_of_combustion_kj_kg": self.heat_of_combustion_kj_kg,
        }
        if not all(isfinite(float(value)) for value in values.values()):
            raise ValueError("all CruzCrownInputs values must be finite")
        if self.surface_fireline_intensity_w_m < 0.0:
            raise ValueError("surface_fireline_intensity_w_m must be non-negative")
        if not 0.0 <= self.canopy_cover_fraction <= 1.0:
            raise ValueError("canopy_cover_fraction must be in [0, 1]")
        if self.canopy_base_height_m < 0.0:
            raise ValueError("canopy_base_height_m must be non-negative")
        if self.canopy_height_m < self.canopy_base_height_m:
            raise ValueError("canopy_height_m must be >= canopy_base_height_m")
        if self.canopy_bulk_density_kg_m3 <= 0.0:
            raise ValueError("canopy_bulk_density_kg_m3 must be positive")
        if self.foliar_moisture_fraction < 0.0:
            raise ValueError("foliar_moisture_fraction must be non-negative")
        if self.fine_fuel_moisture_fraction < 0.0:
            raise ValueError("fine_fuel_moisture_fraction must be non-negative")
        if self.wind_speed_10m_kmh < 0.0:
            raise ValueError("wind_speed_10m_kmh must be non-negative")
        if not 0.0 <= self.downwind_direction_deg <= 360.0:
            raise ValueError("downwind_direction_deg must be in [0, 360]")
        if self.heat_of_combustion_kj_kg <= 0.0:
            raise ValueError("heat_of_combustion_kj_kg must be positive")


class CruzCrownFireModel:
    """Crown-fire model combining Van Wagner initiation and Cruz spread."""

    def compute(self, inputs: CruzCrownInputs) -> FireBehaviorResult:
        """Return crown spread when crown initiation is possible."""

        if not isinstance(inputs, CruzCrownInputs):
            raise TypeError("inputs must be a CruzCrownInputs instance")

        critical_intensity_w_m = van_wagner_critical_fireline_intensity_w_m(
            inputs.canopy_base_height_m,
            inputs.foliar_moisture_fraction,
        )
        initiates = van_wagner_crown_fire_initiates(
            inputs.surface_fireline_intensity_w_m,
            inputs.canopy_cover_fraction,
            inputs.canopy_base_height_m,
            inputs.foliar_moisture_fraction,
        )
        if not initiates:
            return FireBehaviorResult(
                spread_rate_m_s=0.0,
                spread_direction_deg=inputs.downwind_direction_deg % 360.0,
                fireline_intensity_w_m=0.0,
                diagnostics={
                    "fire_type": float(CrownFireType.NONE),
                    "critical_surface_intensity_w_m": critical_intensity_w_m,
                    "active_crown_ros_m_min": 0.0,
                    "critical_crown_ros_m_min": 0.0,
                },
            )

        active_ros = cruz_active_crown_ros_m_min(
            inputs.wind_speed_10m_kmh,
            inputs.canopy_bulk_density_kg_m3,
            inputs.fine_fuel_moisture_fraction,
        )
        critical_ros = van_wagner_critical_crown_ros_m_min(inputs.canopy_bulk_density_kg_m3)
        if active_ros > critical_ros:
            fire_type = CrownFireType.ACTIVE
            crown_ros = active_ros
        else:
            fire_type = CrownFireType.PASSIVE
            crown_ros = cruz_passive_crown_ros_m_min(active_ros, critical_ros)

        canopy_depth = inputs.canopy_height_m - inputs.canopy_base_height_m
        intensity_kw_m = (
            crown_ros
            * inputs.canopy_bulk_density_kg_m3
            * canopy_depth
            * inputs.heat_of_combustion_kj_kg
            / 60.0
        )

        return FireBehaviorResult(
            spread_rate_m_s=crown_ros / 60.0,
            spread_direction_deg=inputs.downwind_direction_deg % 360.0,
            fireline_intensity_w_m=intensity_kw_m * 1000.0,
            diagnostics={
                "fire_type": float(fire_type),
                "critical_surface_intensity_w_m": critical_intensity_w_m,
                "active_crown_ros_m_min": active_ros,
                "critical_crown_ros_m_min": critical_ros,
                "crown_ros_m_min": crown_ros,
            },
        )
