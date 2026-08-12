"""Wind/slope effects applied after the validated Rothermel base ROS."""

from __future__ import annotations

from math import exp, isfinite, radians, tan

from pyfireca.behavior._units import m_inv_to_ft_inv, m_s_to_ft_min


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")


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
    using characteristic SAV in inverse feet and midflame wind in feet/minute:

    ``C = 7.47 exp(-0.133 sigma^0.55)``
    ``B = 0.02526 sigma^0.54``
    ``E = 0.715 exp(-0.000359 sigma)``
    ``phi_w = C U^B (beta/beta_op)^(-E)``

    This function deliberately does not apply wind adjustment, effective-wind
    inversion, wind-speed limiting, or directional vector combination.
    """

    _require_finite_nonnegative("midflame_wind_speed_m_s", midflame_wind_speed_m_s)
    _require_finite_nonnegative("characteristic_sav_m_inv", characteristic_sav_m_inv)
    _require_finite_nonnegative("relative_packing_ratio", relative_packing_ratio)
    if (
        midflame_wind_speed_m_s == 0.0
        or characteristic_sav_m_inv == 0.0
        or relative_packing_ratio == 0.0
    ):
        return 0.0

    sigma_ft_inv = m_inv_to_ft_inv(characteristic_sav_m_inv)
    wind_ft_min = m_s_to_ft_min(midflame_wind_speed_m_s)

    coefficient = 7.47 * exp(-0.133 * sigma_ft_inv**0.55)
    exponent_b = 0.02526 * sigma_ft_inv**0.54
    exponent_e = 0.715 * exp(-0.000359 * sigma_ft_inv)
    return coefficient * wind_ft_min**exponent_b * relative_packing_ratio**-exponent_e


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
