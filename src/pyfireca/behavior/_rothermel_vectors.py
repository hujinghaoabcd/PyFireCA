"""Vector composition for validated scalar Rothermel wind/slope effects."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, isfinite, radians, sin


@dataclass(frozen=True, slots=True)
class CombinedSpreadEffect:
    """Magnitude and direction after combining wind and slope spread effects.

    ``direction_relative_to_upslope_deg`` is clockwise from the upslope axis.
    It is intentionally not a geographic bearing; public direction adapters
    convert between meteorological/geographic conventions separately.
    """

    spread_rate_m_s: float
    direction_relative_to_upslope_deg: float
    effective_factor: float


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")


def combine_wind_slope_effects(
    base_spread_rate_m_s: float,
    *,
    wind_factor: float,
    slope_factor: float,
    wind_push_relative_to_upslope_deg: float,
) -> CombinedSpreadEffect:
    """Combine non-collinear Rothermel wind and slope effects.

    The extra spread-rate vectors are

    ``slope_rate = R0 * phi_s`` along upslope and
    ``wind_rate = R0 * phi_w`` along the wind-push direction.

    Their vector sum determines the additional maximum-spread magnitude and
    direction. The final head-fire spread rate is ``R0 + |vector_sum|``.
    This reduces to ``R0 * (1 + phi_s + phi_w)`` only when both effects are
    collinear in the same direction.
    """

    _require_finite_nonnegative("base_spread_rate_m_s", base_spread_rate_m_s)
    _require_finite_nonnegative("wind_factor", wind_factor)
    _require_finite_nonnegative("slope_factor", slope_factor)
    if not isfinite(wind_push_relative_to_upslope_deg):
        raise ValueError("wind_push_relative_to_upslope_deg must be finite")

    theta = radians(wind_push_relative_to_upslope_deg % 360.0)
    slope_rate = base_spread_rate_m_s * slope_factor
    wind_rate = base_spread_rate_m_s * wind_factor

    x = slope_rate + wind_rate * cos(theta)
    y = wind_rate * sin(theta)
    additional_rate = hypot(x, y)

    direction = (
        0.0 if additional_rate == 0.0 else degrees(atan2(y, x)) % 360.0
    )
    effective_factor = (
        additional_rate / base_spread_rate_m_s if base_spread_rate_m_s > 0.0 else 0.0
    )
    return CombinedSpreadEffect(
        spread_rate_m_s=base_spread_rate_m_s + additional_rate,
        direction_relative_to_upslope_deg=direction,
        effective_factor=effective_factor,
    )
