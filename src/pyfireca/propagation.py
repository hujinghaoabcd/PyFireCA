"""Physical travel-time helpers between raster CA cell centers.

This module is deliberately narrower than a wildfire spread rule. It converts a
*direction-specific* rate of spread supplied by a behavior/directional-spread
model into travel time across known raster geometry. It does not infer off-axis
spread rates from a head-fire rate.
"""

from __future__ import annotations

from math import hypot, inf, isfinite

from pyfireca.neighborhood import Offset


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")


def square_grid_neighbor_distance_m(offset: Offset, cell_size_m: float) -> float:
    """Return center-to-center distance for one square-raster neighbor offset.

    Parameters
    ----------
    offset
        Integer ``(drow, dcol)`` raster offset. The center offset ``(0, 0)`` is
        rejected because it is not a neighbor.
    cell_size_m
        Square raster cell size in metres.

    Notes
    -----
    This function uses distance only; it makes no north/east bearing assumption
    about raster row/column orientation. Rotated or non-square geospatial grids
    will require an affine-aware distance adapter instead of this helper.
    """

    if (
        not isinstance(offset, tuple)
        or len(offset) != 2
        or isinstance(offset[0], bool)
        or isinstance(offset[1], bool)
        or not isinstance(offset[0], int)
        or not isinstance(offset[1], int)
    ):
        raise TypeError("offset must be a two-integer (drow, dcol) tuple")
    if offset == (0, 0):
        raise ValueError("offset (0, 0) is the center cell, not a neighbor")
    if not isfinite(cell_size_m) or cell_size_m <= 0.0:
        raise ValueError("cell_size_m must be finite and positive")

    drow, dcol = offset
    return hypot(drow, dcol) * cell_size_m


def spread_travel_time_s(distance_m: float, directional_spread_rate_m_s: float) -> float:
    """Convert a known directional spread rate and path distance to seconds.

    A positive distance with zero directional ROS returns positive infinity:
    the target cannot be reached through that segment under the supplied
    behavior state. Zero distance returns zero for any non-negative ROS.
    """

    _require_finite_nonnegative("distance_m", distance_m)
    _require_finite_nonnegative(
        "directional_spread_rate_m_s",
        directional_spread_rate_m_s,
    )

    if distance_m == 0.0:
        return 0.0
    if directional_spread_rate_m_s == 0.0:
        return inf
    return distance_m / directional_spread_rate_m_s


def square_grid_neighbor_travel_time_s(
    offset: Offset,
    cell_size_m: float,
    directional_spread_rate_m_s: float,
) -> float:
    """Return physical travel time from one cell center to a square-grid neighbor."""

    distance_m = square_grid_neighbor_distance_m(offset, cell_size_m)
    return spread_travel_time_s(distance_m, directional_spread_rate_m_s)
