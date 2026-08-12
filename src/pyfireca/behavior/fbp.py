"""Self-contained scalar implementation of the Canadian FBP System.

This module implements the fire-behavior equations needed by PyFireCA directly.
It does not import or call Cell2Fire, cffdrs, Prometheus, or another FBP package.

Scientific basis
----------------
- Forestry Canada Fire Danger Group (1992), *Development and Structure of the
  Canadian Forest Fire Behavior Prediction System*, ST-X-3.
- Wotton, Alexander & Taylor (2009), *Updates and revisions to the 1992 Canadian
  Forest Fire Behavior Prediction System*, GLC-X-10.

The implementation is scalar by design: PyFireCA's spatial layer evaluates and
caches one behavior object per source raster cell. This keeps the equations
readable and testable while avoiding a second vectorized numerical framework.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from math import atan2, cos, exp, hypot, isfinite, log, pi, radians, sin, sqrt

from pyfireca.behavior._fbp_constants import (
    FBP_FFMC_MOISTURE_COEFFICIENT,
    FBP_FUEL_PARAMETERS,
    FBP_GRASS_FUEL_TYPES,
    FBP_NON_CROWNING_FUEL_TYPES,
    FBP_NON_FUEL_TYPES,
)
from pyfireca.behavior.base import FireBehaviorResult


class FBPFireType(IntEnum):
    """Canadian FBP fire-description classes."""

    NO_FIRE = 0
    SURFACE = 1
    INTERMITTENT_CROWN = 2
    ACTIVE_CROWN = 3


def normalize_fbp_fuel_type(value: str) -> str:
    """Return the canonical compact FBP fuel-type code."""

    if not isinstance(value, str) or not value.strip():
        raise TypeError("fuel_type must be a non-empty string")
    code = value.strip().upper().replace("-", "").replace("_", "").replace(" ", "")
    aliases = {
        "O1": "O1A",
        "NONFUEL": "NF",
        "NONFUELTYPE": "NF",
        "WATER": "WA",
    }
    code = aliases.get(code, code)
    if code not in FBP_FUEL_PARAMETERS and code not in FBP_NON_FUEL_TYPES:
        supported = ", ".join((*FBP_FUEL_PARAMETERS, *sorted(FBP_NON_FUEL_TYPES)))
        raise ValueError(f"unsupported FBP fuel type {value!r}; expected one of: {supported}")
    return code


def _finite(name: str, value: float) -> float:
    value = float(value)
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _bounded(name: str, value: float, lower: float, upper: float) -> float:
    value = _finite(name, value)
    if not lower <= value <= upper:
        raise ValueError(f"{name} must be in [{lower}, {upper}]")
    return value


@dataclass(frozen=True, slots=True)
class FBPInputs:
    """Native scalar inputs for the Canadian Fire Behavior Prediction System.

    Notes
    -----
    FBP intentionally owns a different input contract from Rothermel. In
    particular, it uses FFMC/BUI and 10-m wind rather than Rothermel fuel-bed
    moisture classes and midflame wind.
    """

    fuel_type: str
    ffmc: float
    bui: float
    wind_speed_10m_kmh: float
    wind_from_direction_deg: float = 0.0
    slope_percent: float = 0.0
    aspect_deg: float = 0.0
    latitude_deg: float = 55.0
    longitude_deg: float = -120.0
    elevation_m: float = 0.0
    julian_day: int = 180
    percent_conifer: float = 50.0
    percent_dead_fir: float = 35.0
    grass_fuel_load_kg_m2: float = 0.35
    grass_curing_percent: float = 80.0
    day_of_minimum_foliar_moisture: int | None = None
    foliar_moisture_percent: float | None = None
    canopy_base_height_m: float | None = None
    crown_fuel_load_kg_m2: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "fuel_type", normalize_fbp_fuel_type(self.fuel_type))
        _bounded("ffmc", self.ffmc, 0.0, 101.0)
        if _finite("bui", self.bui) < 0.0:
            raise ValueError("bui must be non-negative")
        if _finite("wind_speed_10m_kmh", self.wind_speed_10m_kmh) < 0.0:
            raise ValueError("wind_speed_10m_kmh must be non-negative")
        _bounded("wind_from_direction_deg", self.wind_from_direction_deg, 0.0, 360.0)
        _bounded("slope_percent", self.slope_percent, 0.0, 100.0)
        _bounded("aspect_deg", self.aspect_deg, 0.0, 360.0)
        _bounded("latitude_deg", self.latitude_deg, -90.0, 90.0)
        _bounded("longitude_deg", self.longitude_deg, -180.0, 180.0)
        if _finite("elevation_m", self.elevation_m) < 0.0:
            raise ValueError("elevation_m must be non-negative")
        if isinstance(self.julian_day, bool) or not isinstance(self.julian_day, int):
            raise TypeError("julian_day must be an integer")
        if not 1 <= self.julian_day <= 366:
            raise ValueError("julian_day must be in [1, 366]")
        _bounded("percent_conifer", self.percent_conifer, 0.0, 100.0)
        _bounded("percent_dead_fir", self.percent_dead_fir, 0.0, 100.0)
        if _finite("grass_fuel_load_kg_m2", self.grass_fuel_load_kg_m2) < 0.0:
            raise ValueError("grass_fuel_load_kg_m2 must be non-negative")
        _bounded("grass_curing_percent", self.grass_curing_percent, 0.0, 100.0)

        d0 = self.day_of_minimum_foliar_moisture
        if d0 is not None:
            if isinstance(d0, bool) or not isinstance(d0, int):
                raise TypeError("day_of_minimum_foliar_moisture must be an integer")
            if not 1 <= d0 <= 366:
                raise ValueError("day_of_minimum_foliar_moisture must be in [1, 366]")

        fmc = self.foliar_moisture_percent
        if fmc is not None and _finite("foliar_moisture_percent", fmc) < 0.0:
            raise ValueError("foliar_moisture_percent must be non-negative")
        cbh = self.canopy_base_height_m
        if cbh is not None and _finite("canopy_base_height_m", cbh) < 0.0:
            raise ValueError("canopy_base_height_m must be non-negative")
        cfl = self.crown_fuel_load_kg_m2
        if cfl is not None and _finite("crown_fuel_load_kg_m2", cfl) < 0.0:
            raise ValueError("crown_fuel_load_kg_m2 must be non-negative")


@dataclass(frozen=True, slots=True)
class FBPComputation:
    """Detailed equilibrium FBP result for one uniform source cell."""

    fire_type: FBPFireType
    head_ros_m_min: float
    back_ros_m_min: float
    flank_ros_m_min: float
    spread_direction_deg: float
    net_wind_speed_kmh: float
    length_to_breadth_ratio: float
    surface_fuel_consumption_kg_m2: float
    crown_fuel_consumption_kg_m2: float
    total_fuel_consumption_kg_m2: float
    head_fire_intensity_kw_m: float
    crown_fraction_burned: float
    foliar_moisture_percent: float
    critical_surface_intensity_kw_m: float
    critical_ros_m_min: float
    initial_spread_index: float
    buildup_effect: float
    slope_factor: float

    def to_fire_behavior_result(self) -> FireBehaviorResult:
        """Convert native FBP units to the common PyFireCA behavior contract."""

        return FireBehaviorResult(
            spread_rate_m_s=self.head_ros_m_min / 60.0,
            spread_direction_deg=self.spread_direction_deg % 360.0,
            fireline_intensity_w_m=self.head_fire_intensity_kw_m * 1000.0,
            diagnostics={
                "fire_type": float(self.fire_type),
                "head_ros_m_min": self.head_ros_m_min,
                "back_ros_m_min": self.back_ros_m_min,
                "flank_ros_m_min": self.flank_ros_m_min,
                "net_wind_speed_kmh": self.net_wind_speed_kmh,
                "length_to_breadth_ratio": self.length_to_breadth_ratio,
                "surface_fuel_consumption_kg_m2": self.surface_fuel_consumption_kg_m2,
                "crown_fuel_consumption_kg_m2": self.crown_fuel_consumption_kg_m2,
                "total_fuel_consumption_kg_m2": self.total_fuel_consumption_kg_m2,
                "crown_fraction_burned": self.crown_fraction_burned,
                "foliar_moisture_percent": self.foliar_moisture_percent,
                "critical_surface_intensity_kw_m": self.critical_surface_intensity_kw_m,
                "critical_ros_m_min": self.critical_ros_m_min,
                "initial_spread_index": self.initial_spread_index,
                "buildup_effect": self.buildup_effect,
                "slope_factor": self.slope_factor,
            },
        )


def _simple_rsi(a: float, b: float, c: float, isi: float) -> float:
    return a * (1.0 - exp(-b * isi)) ** c


def _grass_curing_factor(curing_percent: float) -> float:
    if curing_percent < 58.8:
        return 0.005 * (exp(0.061 * curing_percent) - 1.0)
    return 0.176 + 0.02 * (curing_percent - 58.8)


def _final_rsi(
    fuel_type: str,
    isi: float,
    percent_conifer: float,
    percent_dead_fir: float,
    grass_curing_percent: float,
) -> float:
    params = FBP_FUEL_PARAMETERS[fuel_type]
    c2 = FBP_FUEL_PARAMETERS["C2"]
    d1 = FBP_FUEL_PARAMETERS["D1"]

    if fuel_type == "M1":
        return (
            percent_conifer / 100.0 * _simple_rsi(c2.a, c2.b, c2.c, isi)
            + (1.0 - percent_conifer / 100.0) * _simple_rsi(d1.a, d1.b, d1.c, isi)
        )
    if fuel_type == "M2":
        return (
            percent_conifer / 100.0 * _simple_rsi(c2.a, c2.b, c2.c, isi)
            + 0.2
            * (1.0 - percent_conifer / 100.0)
            * _simple_rsi(d1.a, d1.b, d1.c, isi)
        )
    if fuel_type == "M3":
        return (
            percent_dead_fir / 100.0 * _simple_rsi(params.a, params.b, params.c, isi)
            + (1.0 - percent_dead_fir / 100.0) * _simple_rsi(d1.a, d1.b, d1.c, isi)
        )
    if fuel_type == "M4":
        return (
            percent_dead_fir / 100.0 * _simple_rsi(params.a, params.b, params.c, isi)
            + 0.2
            * (1.0 - percent_dead_fir / 100.0)
            * _simple_rsi(d1.a, d1.b, d1.c, isi)
        )

    value = _simple_rsi(params.a, params.b, params.c, isi)
    if fuel_type in FBP_GRASS_FUEL_TYPES:
        value *= _grass_curing_factor(grass_curing_percent)
    return value


def _zero_wind_rsz(
    fuel_type: str,
    isz: float,
    percent_conifer: float,
    grass_curing_percent: float,
) -> float:
    """Return zero-wind/zero-slope ROS used by the FBP slope transformation."""

    params = FBP_FUEL_PARAMETERS[fuel_type]
    c2 = FBP_FUEL_PARAMETERS["C2"]
    d1 = FBP_FUEL_PARAMETERS["D1"]

    if fuel_type == "M1":
        return (
            percent_conifer / 100.0 * _simple_rsi(c2.a, c2.b, c2.c, isz)
            + (1.0 - percent_conifer / 100.0) * _simple_rsi(d1.a, d1.b, d1.c, isz)
        )
    if fuel_type == "M2":
        return (
            percent_conifer / 100.0 * _simple_rsi(c2.a, c2.b, c2.c, isz)
            + 0.2
            * (1.0 - percent_conifer / 100.0)
            * _simple_rsi(d1.a, d1.b, d1.c, isz)
        )

    value = _simple_rsi(params.a, params.b, params.c, isz)
    if fuel_type in FBP_GRASS_FUEL_TYPES:
        value *= _grass_curing_factor(grass_curing_percent)
    return value


def _invert_ros(rate: float, a: float, b: float, c: float) -> float:
    if rate <= 0.0:
        return 0.0
    ratio = max(rate / a, 0.0)
    numerator = 1.0 - ratio ** (1.0 / c)
    return log(max(numerator, 0.01)) / -b


def _slope_adjusted_isf(
    fuel_type: str,
    isz: float,
    slope_factor: float,
    percent_conifer: float,
    percent_dead_fir: float,
    grass_curing_percent: float,
) -> tuple[float, float]:
    """Return slope-adjusted ISI and zero-wind/zero-slope ROS."""

    rsz = _zero_wind_rsz(fuel_type, isz, percent_conifer, grass_curing_percent)
    params = FBP_FUEL_PARAMETERS[fuel_type]
    c2 = FBP_FUEL_PARAMETERS["C2"]
    d1 = FBP_FUEL_PARAMETERS["D1"]

    if fuel_type in {"M1", "M2"}:
        c2_isf = _invert_ros(
            _simple_rsi(c2.a, c2.b, c2.c, isz) * slope_factor,
            c2.a,
            c2.b,
            c2.c,
        )
        d1_isf = _invert_ros(
            _simple_rsi(d1.a, d1.b, d1.c, isz) * slope_factor,
            d1.a,
            d1.b,
            d1.c,
        )
        isf = percent_conifer / 100.0 * c2_isf
        isf += (1.0 - percent_conifer / 100.0) * d1_isf
        return isf, rsz

    if fuel_type in {"M3", "M4"}:
        native_isf = _invert_ros(
            rsz * slope_factor,
            params.a,
            params.b,
            params.c,
        )
        d1_isf = _invert_ros(
            _simple_rsi(d1.a, d1.b, d1.c, isz) * slope_factor,
            d1.a,
            d1.b,
            d1.c,
        )
        isf = percent_dead_fir / 100.0 * native_isf
        isf += (1.0 - percent_dead_fir / 100.0) * d1_isf
        return isf, rsz

    rate = rsz * slope_factor
    if fuel_type in FBP_GRASS_FUEL_TYPES:
        curing = _grass_curing_factor(grass_curing_percent)
        if curing <= 0.0:
            return 0.0, rsz
        numerator = 1.0 - (rate / (params.a * curing)) ** (1.0 / params.c)
        return log(max(numerator, 0.01)) / -params.b, rsz
    return _invert_ros(rate, params.a, params.b, params.c), rsz


def _surface_fuel_consumption(
    fuel_type: str,
    ffmc: float,
    bui: float,
    percent_conifer: float,
    grass_fuel_load_kg_m2: float,
) -> float:
    if fuel_type == "C1":
        if ffmc > 84.0:
            return 0.75 + 0.75 * sqrt(max(0.0, 1.0 - exp(-0.23 * (ffmc - 84.0))))
        return 0.75 - 0.75 * sqrt(max(0.0, 1.0 - exp(0.23 * (ffmc - 84.0))))
    if fuel_type == "C2":
        return 5.0 * (1.0 - exp(-0.0115 * bui))
    if fuel_type in {"C3", "C4"}:
        return 5.0 * (1.0 - exp(-0.0164 * bui)) ** 2.24
    if fuel_type in {"C5", "C6"}:
        return 5.0 * (1.0 - exp(-0.0149 * bui)) ** 2.48
    if fuel_type == "C7":
        forest_floor = max(0.0, 2.0 * (1.0 - exp(-0.104 * (ffmc - 70.0))))
        woody = 1.5 * (1.0 - exp(-0.0201 * bui))
        return forest_floor + woody
    if fuel_type in {"D1", "D2"}:
        return 1.5 * (1.0 - exp(-0.0183 * bui))
    if fuel_type in {"M1", "M2"}:
        c2 = 5.0 * (1.0 - exp(-0.0115 * bui))
        d1 = 1.5 * (1.0 - exp(-0.0183 * bui))
        return percent_conifer / 100.0 * c2 + (1.0 - percent_conifer / 100.0) * d1
    if fuel_type in {"M3", "M4"}:
        return 5.0 * (1.0 - exp(-0.0115 * bui))
    if fuel_type in FBP_GRASS_FUEL_TYPES:
        return grass_fuel_load_kg_m2
    if fuel_type == "S1":
        return 4.0 * (1.0 - exp(-0.025 * bui)) + 4.0 * (1.0 - exp(-0.034 * bui))
    if fuel_type == "S2":
        return 10.0 * (1.0 - exp(-0.013 * bui)) + 6.0 * (1.0 - exp(-0.060 * bui))
    if fuel_type == "S3":
        return 12.0 * (1.0 - exp(-0.0166 * bui)) + 20.0 * (1.0 - exp(-0.021 * bui))
    raise ValueError(f"surface fuel consumption is undefined for {fuel_type}")


def _foliar_moisture(inputs: FBPInputs) -> float:
    if inputs.foliar_moisture_percent is not None:
        return float(inputs.foliar_moisture_percent)

    if inputs.elevation_m > 0.0:
        latn = 43.0 + 33.7 * exp(-0.0351 * (150.0 - abs(inputs.longitude_deg)))
    else:
        latn = 46.0 + 23.4 * exp(-0.036 * (150.0 - abs(inputs.longitude_deg)))

    d0 = inputs.day_of_minimum_foliar_moisture
    if d0 is None:
        if inputs.elevation_m > 0.0:
            d0 = round(
                142.1 * (inputs.latitude_deg / latn)
                + 0.0172 * inputs.elevation_m
            )
        else:
            d0 = round(151.0 * (inputs.latitude_deg / latn))

    nd = abs(inputs.julian_day - d0)
    if nd < 30:
        return 85.0 + 0.0189 * nd**2
    if nd < 50:
        return 32.9 + 3.17 * nd - 0.0288 * nd**2
    return 120.0


def _buildup_effect(fuel_type: str, bui: float) -> float:
    params = FBP_FUEL_PARAMETERS[fuel_type]
    if bui <= 0.0:
        return 0.0
    if params.bui0 is None or params.bui0 <= 0.0:
        return 1.0
    raw = exp(50.0 * log(params.q) * ((1.0 / bui) - (1.0 / params.bui0)))
    return min(raw, params.be_max)


def _length_to_breadth_ratio(fuel_type: str, net_wind_speed_kmh: float) -> float:
    if fuel_type in FBP_GRASS_FUEL_TYPES:
        if net_wind_speed_kmh < 1.0:
            return 1.0
        return 1.1 * net_wind_speed_kmh**0.464
    return 1.0 + 8.729 * (1.0 - exp(-0.030 * net_wind_speed_kmh)) ** 2.155


def _zero_result() -> FBPComputation:
    return FBPComputation(
        fire_type=FBPFireType.NO_FIRE,
        head_ros_m_min=0.0,
        back_ros_m_min=0.0,
        flank_ros_m_min=0.0,
        spread_direction_deg=0.0,
        net_wind_speed_kmh=0.0,
        length_to_breadth_ratio=1.0,
        surface_fuel_consumption_kg_m2=0.0,
        crown_fuel_consumption_kg_m2=0.0,
        total_fuel_consumption_kg_m2=0.0,
        head_fire_intensity_kw_m=0.0,
        crown_fraction_burned=0.0,
        foliar_moisture_percent=0.0,
        critical_surface_intensity_kw_m=0.0,
        critical_ros_m_min=0.0,
        initial_spread_index=0.0,
        buildup_effect=0.0,
        slope_factor=1.0,
    )


class FBPModel:
    """Canadian Fire Behavior Prediction System equilibrium behavior model."""

    def compute_full(self, inputs: FBPInputs) -> FBPComputation:
        """Compute detailed equilibrium behavior for one source cell."""

        if not isinstance(inputs, FBPInputs):
            raise TypeError("inputs must be an FBPInputs instance")
        fuel_type = inputs.fuel_type
        if fuel_type in FBP_NON_FUEL_TYPES:
            return _zero_result()

        moisture = (
            FBP_FFMC_MOISTURE_COEFFICIENT
            * (101.0 - inputs.ffmc)
            / (59.5 + inputs.ffmc)
        )
        fine_fuel_function = 91.9 * exp(-0.1386 * moisture)
        fine_fuel_function *= 1.0 + moisture**5.31 / 49_300_000.0
        isz = 0.208 * fine_fuel_function

        if inputs.slope_percent >= 70.0:
            slope_factor = 10.0
        else:
            slope_factor = exp(3.533 * (inputs.slope_percent / 100.0) ** 1.2)

        isf, _ = _slope_adjusted_isf(
            fuel_type,
            isz,
            slope_factor,
            inputs.percent_conifer,
            inputs.percent_dead_fir,
            inputs.grass_curing_percent,
        )

        ratio = isf / (0.208 * fine_fuel_function) if fine_fuel_function > 0.0 else 1.0
        wse1 = log(max(ratio, 1e-15)) / 0.05039
        threshold = 2.496 * fine_fuel_function
        if threshold > 0.0 and isf < 0.999 * threshold:
            wse2 = 28.0 - log(max(1e-15, 1.0 - isf / threshold)) / 0.0818
        else:
            wse2 = 112.45
        slope_equivalent_wind = wse1 if wse1 <= 40.0 else wse2

        downwind = (inputs.wind_from_direction_deg + 180.0) % 360.0
        upslope = (inputs.aspect_deg + 180.0) % 360.0
        wind_x = inputs.wind_speed_10m_kmh * sin(radians(downwind))
        wind_y = inputs.wind_speed_10m_kmh * cos(radians(downwind))
        slope_x = slope_equivalent_wind * sin(radians(upslope))
        slope_y = slope_equivalent_wind * cos(radians(upslope))
        net_x = wind_x + slope_x
        net_y = wind_y + slope_y
        net_wind_speed = hypot(net_x, net_y)
        if net_wind_speed > 1e-12:
            spread_direction = atan2(net_x, net_y) * 180.0 / pi
            spread_direction %= 360.0
        else:
            spread_direction = 0.0

        if net_wind_speed > 40.0:
            wind_function = 12.0 * (1.0 - exp(-0.0818 * (net_wind_speed - 28.0)))
        else:
            wind_function = exp(0.05039 * net_wind_speed)
        back_wind_function = exp(-0.05039 * net_wind_speed)
        isi = 0.208 * fine_fuel_function * wind_function
        back_isi = 0.208 * fine_fuel_function * back_wind_function

        head_rsi = _final_rsi(
            fuel_type,
            isi,
            inputs.percent_conifer,
            inputs.percent_dead_fir,
            inputs.grass_curing_percent,
        )
        back_rsi = _final_rsi(
            fuel_type,
            back_isi,
            inputs.percent_conifer,
            inputs.percent_dead_fir,
            inputs.grass_curing_percent,
        )
        buildup_effect = _buildup_effect(fuel_type, inputs.bui)
        head_ros = head_rsi * buildup_effect
        back_ros = back_rsi * buildup_effect

        if fuel_type == "D2":
            if inputs.bui < 70.0:
                head_ros = 0.0
                back_ros = 0.0
            else:
                head_ros *= 0.2
                back_ros *= 0.2

        sfc = _surface_fuel_consumption(
            fuel_type,
            inputs.ffmc,
            inputs.bui,
            inputs.percent_conifer,
            inputs.grass_fuel_load_kg_m2,
        )
        fmc = _foliar_moisture(inputs)
        defaults = FBP_FUEL_PARAMETERS[fuel_type]
        cbh = (
            defaults.canopy_base_height_m
            if inputs.canopy_base_height_m is None
            else inputs.canopy_base_height_m
        )
        cfl = (
            defaults.crown_fuel_load_kg_m2
            if inputs.crown_fuel_load_kg_m2 is None
            else inputs.crown_fuel_load_kg_m2
        )

        critical_intensity = (0.01 * cbh * (460.0 + 25.9 * fmc)) ** 1.5 if cbh > 0 else 0.0
        critical_ros = critical_intensity / (300.0 * sfc) if sfc > 0.0 else 0.0

        if fuel_type in FBP_NON_CROWNING_FUEL_TYPES or cfl <= 0.0:
            cfb = 0.0
        elif head_ros <= critical_ros:
            cfb = 0.0
        else:
            cfb = min(1.0, max(0.0, 1.0 - exp(-0.23 * (head_ros - critical_ros))))

        crown_consumption = cfb * cfl
        if fuel_type in {"M1", "M2"}:
            crown_consumption *= inputs.percent_conifer / 100.0
        elif fuel_type in {"M3", "M4"}:
            crown_consumption *= inputs.percent_dead_fir / 100.0

        if fuel_type == "C6":
            surface_ros = head_ros
            fme = 1000.0 * (1.5 - 0.00275 * fmc) ** 4 / (460.0 + 25.9 * fmc)
            crown_ros = 0.0
            if crown_consumption > 0.0:
                crown_ros = 60.0 * (1.0 - exp(-0.0497 * isi)) * (fme / 0.778237)
            head_ros = surface_ros + cfb * (crown_ros - surface_ros)

        total_consumption = sfc + crown_consumption
        head_intensity = 300.0 * head_ros * total_consumption

        if head_ros <= 0.0:
            fire_type = FBPFireType.NO_FIRE
        elif cfb <= 0.1:
            fire_type = FBPFireType.SURFACE
        elif cfb < 0.9:
            fire_type = FBPFireType.INTERMITTENT_CROWN
        else:
            fire_type = FBPFireType.ACTIVE_CROWN

        lb = _length_to_breadth_ratio(fuel_type, net_wind_speed)
        flank_ros = (head_ros + back_ros) / (2.0 * lb) if lb > 0.0 else 0.0

        return FBPComputation(
            fire_type=fire_type,
            head_ros_m_min=max(0.0, head_ros),
            back_ros_m_min=max(0.0, back_ros),
            flank_ros_m_min=max(0.0, flank_ros),
            spread_direction_deg=spread_direction,
            net_wind_speed_kmh=net_wind_speed,
            length_to_breadth_ratio=lb,
            surface_fuel_consumption_kg_m2=sfc,
            crown_fuel_consumption_kg_m2=crown_consumption,
            total_fuel_consumption_kg_m2=total_consumption,
            head_fire_intensity_kw_m=max(0.0, head_intensity),
            crown_fraction_burned=cfb,
            foliar_moisture_percent=fmc,
            critical_surface_intensity_kw_m=critical_intensity,
            critical_ros_m_min=critical_ros,
            initial_spread_index=isi,
            buildup_effect=buildup_effect,
            slope_factor=slope_factor,
        )

    def compute(self, inputs: FBPInputs) -> FireBehaviorResult:
        """Return the model-independent behavior contract used by PyFireCA."""

        return self.compute_full(inputs).to_fire_behavior_result()
