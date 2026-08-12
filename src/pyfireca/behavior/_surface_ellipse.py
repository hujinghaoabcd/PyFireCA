"""Behave-aligned surface-fire ellipse and ignition-point directional spread.

The functions here implement the surface-fire geometry used by the pinned
Behave core after maximum spread rate and effective wind have been resolved.
They do not compute Rothermel reaction/spread factors themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, exp, isfinite, radians, sqrt

from pyfireca.behavior._units import m_s_to_mph

_MAX_SURFACE_LENGTH_TO_WIDTH_RATIO = 8.0


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class SurfaceFireEllipse:
    """Surface-fire ellipse quantities derived from head ROS and effective wind."""

    head_spread_rate_m_s: float
    backing_spread_rate_m_s: float
    flanking_spread_rate_m_s: float
    length_to_width_ratio: float
    eccentricity: float


def compute_surface_length_to_width_ratio(effective_wind_speed_m_s: float) -> float:
    """Return Behave's surface-fire length-to-width ratio.

    Behave evaluates the empirical relation with effective wind speed in mph::

        L/W = 0.936 exp(0.1147 U) + 0.461 exp(-0.0692 U) - 0.397

    and caps surface-fire ``L/W`` at 8.0.
    """

    _require_finite_nonnegative("effective_wind_speed_m_s", effective_wind_speed_m_s)
    wind_mph = m_s_to_mph(effective_wind_speed_m_s)
    ratio = 0.936 * exp(0.1147 * wind_mph) + 0.461 * exp(-0.0692 * wind_mph) - 0.397
    return min(_MAX_SURFACE_LENGTH_TO_WIDTH_RATIO, ratio)


def compute_ellipse_eccentricity(length_to_width_ratio: float) -> float:
    """Return ellipse eccentricity from a length-to-width ratio >= 1."""

    if not isfinite(length_to_width_ratio) or length_to_width_ratio < 1.0:
        raise ValueError("length_to_width_ratio must be finite and at least 1")
    return sqrt(length_to_width_ratio**2 - 1.0) / length_to_width_ratio


def compute_backing_spread_rate_m_s(
    head_spread_rate_m_s: float,
    eccentricity: float,
) -> float:
    """Return backing ROS from head ROS and ellipse eccentricity."""

    _require_finite_nonnegative("head_spread_rate_m_s", head_spread_rate_m_s)
    if not isfinite(eccentricity) or not 0.0 <= eccentricity < 1.0:
        raise ValueError("eccentricity must be finite and in [0, 1)")
    return head_spread_rate_m_s * (1.0 - eccentricity) / (1.0 + eccentricity)


def compute_flanking_spread_rate_m_s(
    head_spread_rate_m_s: float,
    backing_spread_rate_m_s: float,
    length_to_width_ratio: float,
) -> float:
    """Return flanking ROS from Behave's basic ellipse dimensions."""

    _require_finite_nonnegative("head_spread_rate_m_s", head_spread_rate_m_s)
    _require_finite_nonnegative("backing_spread_rate_m_s", backing_spread_rate_m_s)
    if not isfinite(length_to_width_ratio) or length_to_width_ratio < 1.0:
        raise ValueError("length_to_width_ratio must be finite and at least 1")
    return (head_spread_rate_m_s + backing_spread_rate_m_s) / (2.0 * length_to_width_ratio)


def build_surface_fire_ellipse(
    head_spread_rate_m_s: float,
    effective_wind_speed_m_s: float,
) -> SurfaceFireEllipse:
    """Build Behave surface-fire ellipse quantities for one behavior state."""

    _require_finite_nonnegative("head_spread_rate_m_s", head_spread_rate_m_s)
    ratio = compute_surface_length_to_width_ratio(effective_wind_speed_m_s)
    eccentricity = compute_ellipse_eccentricity(ratio)
    backing = compute_backing_spread_rate_m_s(head_spread_rate_m_s, eccentricity)
    flanking = compute_flanking_spread_rate_m_s(head_spread_rate_m_s, backing, ratio)
    return SurfaceFireEllipse(
        head_spread_rate_m_s=head_spread_rate_m_s,
        backing_spread_rate_m_s=backing,
        flanking_spread_rate_m_s=flanking,
        length_to_width_ratio=ratio,
        eccentricity=eccentricity,
    )


def spread_rate_from_ignition_point_m_s(
    head_spread_rate_m_s: float,
    eccentricity: float,
    direction_offset_from_head_deg: float,
) -> float:
    """Return radial ROS from ignition point toward an arbitrary direction.

    ``direction_offset_from_head_deg`` is the angular separation from the
    maximum-spread direction. The pinned Behave ``FromIgnitionPoint`` path
    reduces the Catchpole-style ellipse geometry to::

        R(beta) = R_head * (1 - e) / (1 - e cos(beta))

    where ``beta=0`` is heading and ``beta=180`` is backing.
    """

    _require_finite_nonnegative("head_spread_rate_m_s", head_spread_rate_m_s)
    if not isfinite(eccentricity) or not 0.0 <= eccentricity < 1.0:
        raise ValueError("eccentricity must be finite and in [0, 1)")
    if not isfinite(direction_offset_from_head_deg):
        raise ValueError("direction_offset_from_head_deg must be finite")

    beta = radians(direction_offset_from_head_deg % 360.0)
    denominator = 1.0 - eccentricity * cos(beta)
    return head_spread_rate_m_s * (1.0 - eccentricity) / denominator
