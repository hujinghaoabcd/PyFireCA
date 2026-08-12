"""Wind/slope effects applied after the validated Rothermel base ROS."""

from __future__ import annotations

from math import exp, isfinite, radians, tan

from pyfireca.behavior._units import (
    ft_min_to_m_s,
    m_inv_to_ft_inv,
    m_s_to_ft_min,
    w_m2_to_btu_ft2_min,
)


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")


def _wind_coefficients(
    characteristic_sav_m_inv: float,
) -> tuple[float, float, float]:
    _require_finite_nonnegative("characteristic_sav_m_inv", characteristic_sav_m_inv)
    if characteristic_sav_m_inv == 0.0:
        return 0.0, 0.0, 0.0

    sigma_ft_inv = m_inv_to_ft_inv(characteristic_sav_m_inv)
    coefficient = 7.47 * exp(-0.133 * sigma_ft_inv**0.55)
    exponent_b = 0.02526 * sigma_ft_inv**0.54
    exponent_e = 0.715 * exp(-0.000359 * sigma_ft_inv)
    return coefficient, exponent_b, exponent_e


def compute_slope_factor(slope_deg: float, packing_ratio: float) -> float:
    """Return Rothermel slope factor ``phi_s``.

    The relation is ``5.275 * beta^-0.3 * tan(slope)^2``. PyFireCA receives
    slope in degrees and converts it explicitly. A zero slope or zero packing
    ratio returns zero rather than evaluating a singular empirical term.
    """

    _require_finite_nonnegative("slope_deg", slope_deg)
    _require_finite_nonnegative("packing_ratio", packing_ratio)
    if slope_deg >= 90.0:
        raise ValueError("slope_deg must be less than 90 degrees")
    if slope_deg == 0.0 or packing_ratio == 0.0:
        return 0.0

    slope_tangent = tan(radians(slope_deg))
    return 5.275 * packing_ratio**-0.3 * slope_tangent**2


def compute_wind_factor(
    midflame_wind_speed_m_s: float,
    characteristic_sav_m_inv: float,
    relative_packing_ratio: float,
) -> float:
    """Return Rothermel scalar wind factor ``phi_w``.

    Public inputs use SI units. The empirical wind correlation is evaluated
    using characteristic SAV in inverse feet and midflame wind in feet/minute.

    This function deliberately does not apply wind adjustment, effective-wind
    inversion, wind-speed limiting, or directional vector combination.
    """

    _require_finite_nonnegative("midflame_wind_speed_m_s", midflame_wind_speed_m_s)
    _require_finite_nonnegative("relative_packing_ratio", relative_packing_ratio)
    coefficient, exponent_b, exponent_e = _wind_coefficients(characteristic_sav_m_inv)
    if (
        midflame_wind_speed_m_s == 0.0
        or characteristic_sav_m_inv == 0.0
        or relative_packing_ratio == 0.0
    ):
        return 0.0

    wind_ft_min = m_s_to_ft_min(midflame_wind_speed_m_s)
    return coefficient * wind_ft_min**exponent_b * relative_packing_ratio**-exponent_e


def compute_effective_wind_speed_m_s(
    effective_wind_factor: float,
    characteristic_sav_m_inv: float,
    relative_packing_ratio: float,
) -> float:
    """Invert the wind-factor relation to an effective midflame wind speed.

    Later wind+slope vector combination produces one effective spread factor.
    Behave/Rothermel expresses that factor as an equivalent midflame wind speed
    by algebraically inverting the same ``C/B/E`` wind relation.
    """

    _require_finite_nonnegative("effective_wind_factor", effective_wind_factor)
    _require_finite_nonnegative("relative_packing_ratio", relative_packing_ratio)
    if effective_wind_factor == 0.0:
        return 0.0
    if characteristic_sav_m_inv == 0.0 or relative_packing_ratio == 0.0:
        raise ValueError(
            "positive effective_wind_factor requires positive characteristic SAV "
            "and relative packing ratio"
        )

    coefficient, exponent_b, exponent_e = _wind_coefficients(characteristic_sav_m_inv)
    effective_ft_min = (
        effective_wind_factor * relative_packing_ratio**exponent_e / coefficient
    ) ** (1.0 / exponent_b)
    return ft_min_to_m_s(effective_ft_min)


def compute_wind_speed_limit_m_s(reaction_intensity_w_m2: float) -> float:
    """Return the optional operational maximum effective wind speed in m/s.

    The empirical Behave/Rothermel limit is ``0.9 * I_R`` when reaction
    intensity is expressed in Btu/ft²/min, yielding a wind speed in ft/min.
    PyFireCA performs that native-unit conversion explicitly here.
    """

    _require_finite_nonnegative("reaction_intensity_w_m2", reaction_intensity_w_m2)
    reaction_intensity_btu_ft2_min = w_m2_to_btu_ft2_min(reaction_intensity_w_m2)
    return ft_min_to_m_s(0.9 * reaction_intensity_btu_ft2_min)


def apply_wind_speed_limit(
    base_spread_rate_m_s: float,
    effective_wind_speed_m_s: float,
    wind_speed_limit_m_s: float,
    characteristic_sav_m_inv: float,
    relative_packing_ratio: float,
) -> tuple[float, bool]:
    """Apply an explicitly enabled effective-wind limit to spread magnitude.

    Returns ``(spread_rate_m_s, exceeded)``. The caller decides whether this
    optional operational limit is enabled. When exceeded, spread is recomputed
    from the wind factor associated with the limiting effective wind speed.
    """

    _require_finite_nonnegative("base_spread_rate_m_s", base_spread_rate_m_s)
    _require_finite_nonnegative("effective_wind_speed_m_s", effective_wind_speed_m_s)
    _require_finite_nonnegative("wind_speed_limit_m_s", wind_speed_limit_m_s)

    if effective_wind_speed_m_s <= wind_speed_limit_m_s:
        factor = compute_wind_factor(
            effective_wind_speed_m_s,
            characteristic_sav_m_inv,
            relative_packing_ratio,
        )
        return base_spread_rate_m_s * (1.0 + factor), False

    limited_factor = compute_wind_factor(
        wind_speed_limit_m_s,
        characteristic_sav_m_inv,
        relative_packing_ratio,
    )
    return base_spread_rate_m_s * (1.0 + limited_factor), True


def apply_scalar_spread_factors(
    base_spread_rate_m_s: float,
    *,
    wind_factor: float = 0.0,
    slope_factor: float = 0.0,
) -> float:
    """Apply collinear scalar wind/slope factors to base spread rate.

    This helper is intentionally scalar. It is valid for slope-only, wind-only,
    or explicitly collinear effects. Non-collinear wind/slope direction must be
    handled by the later vector stage rather than by this helper.
    """

    _require_finite_nonnegative("base_spread_rate_m_s", base_spread_rate_m_s)
    _require_finite_nonnegative("wind_factor", wind_factor)
    _require_finite_nonnegative("slope_factor", slope_factor)
    return base_spread_rate_m_s * (1.0 + wind_factor + slope_factor)
