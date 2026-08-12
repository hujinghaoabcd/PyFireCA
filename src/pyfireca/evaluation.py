"""Analytical reference fields and error metrics for CA propagation studies."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite, sqrt
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from pyfireca.behavior._surface_ellipse import spread_rate_from_ignition_point_m_s
from pyfireca.propagation import north_up_square_grid_offset_bearing_deg

ImmediateSquareTopology = Literal["vn4", "moore8"]


@dataclass(frozen=True, slots=True)
class ArrivalErrorMetrics:
    """Summary error statistics for two finite-compatible arrival fields."""

    count: int
    mae_s: float
    rmse_s: float
    bias_s: float
    max_abs_error_s: float


def immediate_square_lattice_path_distance_m(
    drow: int,
    dcol: int,
    *,
    cell_size_m: float,
    topology: ImmediateSquareTopology,
) -> float:
    """Return the exact shortest lattice-path length for VN4 or Moore8.

    ``VN4`` produces the Manhattan path length. ``Moore8`` uses unit cardinal
    edges plus ``sqrt(2)`` diagonal edges and therefore produces the standard
    octile path length.
    """

    if (
        isinstance(drow, bool)
        or isinstance(dcol, bool)
        or not isinstance(drow, int)
        or not isinstance(dcol, int)
    ):
        raise TypeError("drow and dcol must be integers")
    if not isfinite(cell_size_m) or cell_size_m <= 0.0:
        raise ValueError("cell_size_m must be finite and positive")
    if topology not in ("vn4", "moore8"):
        raise ValueError("topology must be 'vn4' or 'moore8'")

    row_steps = abs(drow)
    col_steps = abs(dcol)
    if topology == "vn4":
        return (row_steps + col_steps) * cell_size_m

    diagonal_steps = min(row_steps, col_steps)
    cardinal_steps = max(row_steps, col_steps) - diagonal_steps
    return (cardinal_steps + sqrt(2.0) * diagonal_steps) * cell_size_m


def homogeneous_ellipse_lattice_arrival_error_s(
    drow: int,
    dcol: int,
    *,
    cell_size_m: float,
    head_spread_rate_m_s: float,
    eccentricity: float,
    topology: ImmediateSquareTopology,
) -> float:
    """Return the exact homogeneous ellipse CA arrival error for VN4/Moore8.

    For the pinned Behave/Catchpole ignition-point ellipse,

    ``R(beta) = R_head * (1-e) / (1-e*cos(beta))``.

    Therefore one edge travel time can be written as a path-length term minus a
    heading-direction projection term. When edge times are summed along any
    path between fixed endpoints, the projection term telescopes to the same
    endpoint displacement for every path. The shortest-path solver consequently
    minimizes only geometric lattice path length.

    The exact CA-minus-continuous arrival error is therefore::

        (D_lattice - D_euclidean) / (R_head * (1-e))

    This expression is independent of the fire heading angle. It also shows why
    reducing cell size alone does not guarantee removal of lattice bias when the
    allowed direction set remains fixed at four or eight directions.
    """

    if not isfinite(head_spread_rate_m_s) or head_spread_rate_m_s <= 0.0:
        raise ValueError("head_spread_rate_m_s must be finite and positive")
    if not isfinite(eccentricity) or not 0.0 <= eccentricity < 1.0:
        raise ValueError("eccentricity must be finite and in [0, 1)")

    lattice_distance = immediate_square_lattice_path_distance_m(
        drow,
        dcol,
        cell_size_m=cell_size_m,
        topology=topology,
    )
    euclidean_distance = hypot(drow, dcol) * cell_size_m
    return (lattice_distance - euclidean_distance) / (
        head_spread_rate_m_s * (1.0 - eccentricity)
    )


def analytical_ellipse_arrival_times(
    shape: tuple[int, int],
    *,
    cell_size_m: float,
    ignition: tuple[int, int],
    head_spread_rate_m_s: float,
    eccentricity: float,
    head_direction_deg: float | None,
) -> NDArray[np.float64]:
    """Return continuous ellipse arrival time at north-up square-grid cell centers.

    This function is a mathematical reference for raster-discretization studies,
    not a second CA solver. Every cell center is connected directly to the
    ignition point through the validated Behave/Catchpole ``FromIgnitionPoint``
    radial relation.

    Parameters
    ----------
    shape
        Raster ``(rows, cols)``.
    cell_size_m
        Square cell size in metres.
    ignition
        Ignition cell index ``(row, col)``. Its center is the analytical origin.
    head_spread_rate_m_s
        Maximum/head radial ROS in m/s.
    eccentricity
        Surface-fire ellipse eccentricity in ``[0, 1)``.
    head_direction_deg
        Geographic maximum-spread bearing. May be ``None`` only for a circular
        ellipse (eccentricity zero), where direction is physically irrelevant.
    """

    if (
        not isinstance(shape, tuple)
        or len(shape) != 2
        or isinstance(shape[0], bool)
        or isinstance(shape[1], bool)
        or not isinstance(shape[0], int)
        or not isinstance(shape[1], int)
        or shape[0] < 1
        or shape[1] < 1
    ):
        raise ValueError("shape must contain two positive integers")
    if not isfinite(cell_size_m) or cell_size_m <= 0.0:
        raise ValueError("cell_size_m must be finite and positive")
    if not isfinite(head_spread_rate_m_s) or head_spread_rate_m_s <= 0.0:
        raise ValueError("head_spread_rate_m_s must be finite and positive")
    if not isfinite(eccentricity) or not 0.0 <= eccentricity < 1.0:
        raise ValueError("eccentricity must be finite and in [0, 1)")
    if (
        not isinstance(ignition, tuple)
        or len(ignition) != 2
        or isinstance(ignition[0], bool)
        or isinstance(ignition[1], bool)
        or not isinstance(ignition[0], int)
        or not isinstance(ignition[1], int)
    ):
        raise TypeError("ignition must be a two-integer (row, col) tuple")
    ignition_row, ignition_col = ignition
    if not 0 <= ignition_row < shape[0] or not 0 <= ignition_col < shape[1]:
        raise IndexError(f"ignition {ignition} is outside raster shape {shape}")
    if head_direction_deg is None:
        if eccentricity != 0.0:
            raise ValueError("anisotropic ellipse requires a head_direction_deg")
    elif not isfinite(head_direction_deg):
        raise ValueError("head_direction_deg must be finite or None for a circle")

    arrival = np.empty(shape, dtype=np.float64)
    for row in range(shape[0]):
        for col in range(shape[1]):
            drow = row - ignition_row
            dcol = col - ignition_col
            if drow == 0 and dcol == 0:
                arrival[row, col] = 0.0
                continue

            distance_m = hypot(drow, dcol) * cell_size_m
            if eccentricity == 0.0:
                directional_rate = head_spread_rate_m_s
            else:
                edge_bearing = north_up_square_grid_offset_bearing_deg((drow, dcol))
                angular_offset = (edge_bearing - float(head_direction_deg)) % 360.0
                directional_rate = spread_rate_from_ignition_point_m_s(
                    head_spread_rate_m_s,
                    eccentricity,
                    angular_offset,
                )
            arrival[row, col] = distance_m / directional_rate

    return arrival


def arrival_error_metrics(
    observed_s: NDArray[np.floating],
    reference_s: NDArray[np.floating],
    *,
    evaluation_mask: NDArray[np.bool_] | None = None,
) -> ArrivalErrorMetrics:
    """Return absolute/RMS/bias errors without hiding reachability mismatches.

    Within the evaluation mask, observed and reference arrays must have the same
    finite/infinite reachability pattern. This prevents a metric call from
    silently dropping cells that one propagation method failed to reach.
    """

    observed = np.asarray(observed_s, dtype=np.float64)
    reference = np.asarray(reference_s, dtype=np.float64)
    if observed.ndim != 2 or reference.ndim != 2:
        raise ValueError("arrival fields must be two-dimensional")
    if observed.shape != reference.shape:
        raise ValueError(
            f"observed shape {observed.shape} does not match reference shape {reference.shape}"
        )
    if np.isnan(observed).any() or np.isneginf(observed).any():
        raise ValueError("observed arrival field may contain finite values or +inf only")
    if np.isnan(reference).any() or np.isneginf(reference).any():
        raise ValueError("reference arrival field may contain finite values or +inf only")

    if evaluation_mask is None:
        mask = np.ones(observed.shape, dtype=bool)
    else:
        mask = np.asarray(evaluation_mask)
        if mask.dtype != np.bool_ or mask.ndim != 2 or mask.shape != observed.shape:
            raise TypeError("evaluation_mask must be a boolean array matching arrival shape")

    observed_finite = np.isfinite(observed)
    reference_finite = np.isfinite(reference)
    mismatch = mask & (observed_finite != reference_finite)
    if np.any(mismatch):
        raise ValueError(
            "observed/reference reachability differs inside evaluation_mask; "
            "do not hide unreachable-cell errors in summary metrics"
        )

    finite_mask = mask & observed_finite
    count = int(np.count_nonzero(finite_mask))
    if count == 0:
        raise ValueError("evaluation_mask contains no finite comparable arrival cells")

    error = observed[finite_mask] - reference[finite_mask]
    abs_error = np.abs(error)
    return ArrivalErrorMetrics(
        count=count,
        mae_s=float(np.mean(abs_error)),
        rmse_s=float(np.sqrt(np.mean(error**2))),
        bias_s=float(np.mean(error)),
        max_abs_error_s=float(np.max(abs_error)),
    )
