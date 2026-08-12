"""Geographic direction conversions for wildfire behavior inputs.

Angles use compass bearings: 0° north, 90° east, increasing clockwise.
Terrain aspect denotes the downslope-facing direction. Wind direction uses the
meteorological from-direction. These semantics are converted explicitly before
Rothermel vector composition.
"""

from __future__ import annotations

from math import isfinite


def normalize_direction_deg(direction_deg: float) -> float:
    """Normalize one finite direction to the half-open interval [0, 360)."""

    if not isfinite(direction_deg):
        raise ValueError("direction_deg must be finite")
    return direction_deg % 360.0


def upslope_direction_deg(aspect_deg: float) -> float:
    """Convert downslope terrain aspect to the geographic upslope bearing."""

    return (normalize_direction_deg(aspect_deg) + 180.0) % 360.0


def wind_push_direction_deg(wind_from_direction_deg: float) -> float:
    """Convert meteorological wind-from direction to the downwind push bearing."""

    return (normalize_direction_deg(wind_from_direction_deg) + 180.0) % 360.0


def wind_push_relative_to_upslope_deg(
    wind_from_direction_deg: float,
    aspect_deg: float,
) -> float:
    """Return wind-push direction clockwise from the upslope axis."""

    wind_push = wind_push_direction_deg(wind_from_direction_deg)
    upslope = upslope_direction_deg(aspect_deg)
    return (wind_push - upslope) % 360.0


def geographic_direction_from_upslope_relative_deg(
    direction_relative_to_upslope_deg: float,
    aspect_deg: float,
) -> float:
    """Convert a direction relative to upslope back to a geographic bearing."""

    relative = normalize_direction_deg(direction_relative_to_upslope_deg)
    return (upslope_direction_deg(aspect_deg) + relative) % 360.0
