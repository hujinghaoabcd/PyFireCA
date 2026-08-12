"""Static event-driven arrival-time propagation for wildfire raster cells.

This is the first physical-time propagation baseline in PyFireCA. It is kept
separate from the original synchronous :class:`Simulation`: callers provide a
direction-specific rate of spread for each source-cell/neighbor edge, and this
module computes earliest arrival times from those physical edge travel times.
"""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import isfinite
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from pyfireca.neighborhood import Neighborhood, Offset, valid_neighbor_indices
from pyfireca.propagation import square_grid_neighbor_travel_time_s
from pyfireca.state import FireState


class DirectionalSpreadRateProvider(Protocol):
    """Supply one already-resolved directional ROS for a raster edge."""

    def spread_rate_m_s(self, row: int, col: int, offset: Offset) -> float:
        """Return ROS from source ``(row, col)`` toward ``offset`` in m/s."""
        ...


@dataclass(frozen=True, slots=True)
class ConstantDirectionalSpreadRate:
    """Isotropic constant directional ROS used as a transparent baseline."""

    rate_m_s: float

    def __post_init__(self) -> None:
        if not isfinite(self.rate_m_s) or self.rate_m_s < 0.0:
            raise ValueError("rate_m_s must be finite and non-negative")

    def spread_rate_m_s(self, row: int, col: int, offset: Offset) -> float:
        """Return the same directional ROS for every source and neighbor."""

        del row, col, offset
        return self.rate_m_s


@dataclass(frozen=True, slots=True)
class StaticArrivalTimeSolver:
    """Compute earliest arrival times for static directional edge spread rates.

    Parameters
    ----------
    neighborhood
        Raster neighbor topology used to generate candidate spread edges.
    cell_size_m
        Square cell size in metres.
    spread_rate_provider
        Supplies the directional ROS for each source cell and neighbor offset.
        This solver never derives off-axis ROS from a head-fire value.

    Notes
    -----
    This is a Dijkstra-style event baseline for *static* edge travel times. A
    future time-dependent scheduler is required when weather/fuel moisture makes
    an edge ROS change while a fire is travelling across that edge.
    """

    neighborhood: Neighborhood
    cell_size_m: float
    spread_rate_provider: DirectionalSpreadRateProvider

    def __post_init__(self) -> None:
        if not isfinite(self.cell_size_m) or self.cell_size_m <= 0.0:
            raise ValueError("cell_size_m must be finite and positive")
        if not hasattr(self.spread_rate_provider, "spread_rate_m_s"):
            raise TypeError("spread_rate_provider must implement spread_rate_m_s()")

    def solve(
        self,
        domain_mask: NDArray[np.bool_],
        ignition_times_s: NDArray[np.floating],
    ) -> NDArray[np.float64]:
        """Return earliest physical arrival time at every raster cell.

        ``domain_mask=True`` marks cells through which fire may propagate.
        ``ignition_times_s`` uses finite non-negative seconds for externally
        seeded ignition times and positive infinity for cells with no initial
        ignition. Finite ignition outside the domain is rejected.
        """

        domain = np.asarray(domain_mask)
        ignition = np.asarray(ignition_times_s, dtype=np.float64)
        if domain.ndim != 2 or domain.dtype != np.bool_:
            raise TypeError("domain_mask must be a two-dimensional boolean array")
        if ignition.ndim != 2:
            raise ValueError("ignition_times_s must be two-dimensional")
        if ignition.shape != domain.shape:
            raise ValueError(
                f"ignition_times_s shape {ignition.shape} does not match domain {domain.shape}"
            )
        if np.isnan(ignition).any() or np.isneginf(ignition).any():
            raise ValueError("ignition_times_s may contain finite values or +inf, not NaN/-inf")
        finite_ignitions = np.isfinite(ignition)
        if (ignition[finite_ignitions] < 0.0).any():
            raise ValueError("finite ignition_times_s values must be non-negative")
        if np.any(finite_ignitions & ~domain):
            raise ValueError("finite ignition_times_s values must lie inside the domain")

        arrival = np.full(domain.shape, np.inf, dtype=np.float64)
        queue: list[tuple[float, int, int]] = []
        for row, col in np.argwhere(finite_ignitions):
            row_i = int(row)
            col_i = int(col)
            time_s = float(ignition[row_i, col_i])
            arrival[row_i, col_i] = time_s
            heappush(queue, (time_s, row_i, col_i))

        offsets = self.neighborhood.offsets()
        while queue:
            current_time, row, col = heappop(queue)
            if current_time != arrival[row, col]:
                continue

            for target_row, target_col in valid_neighbor_indices(
                row,
                col,
                domain.shape,
                offsets,
            ):
                if not domain[target_row, target_col]:
                    continue

                offset = (target_row - row, target_col - col)
                rate = self.spread_rate_provider.spread_rate_m_s(row, col, offset)
                if not isfinite(rate) or rate < 0.0:
                    raise ValueError(
                        "spread_rate_provider returned a non-finite or negative ROS "
                        f"at source ({row}, {col}) offset {offset}: {rate}"
                    )
                travel_time = square_grid_neighbor_travel_time_s(
                    offset,
                    self.cell_size_m,
                    rate,
                )
                candidate = current_time + travel_time
                if candidate < arrival[target_row, target_col]:
                    arrival[target_row, target_col] = candidate
                    heappush(queue, (candidate, target_row, target_col))

        return arrival


def arrival_times_to_state(
    domain_mask: NDArray[np.bool_],
    arrival_times_s: NDArray[np.floating],
    *,
    time_s: float,
    burn_duration_s: float,
) -> NDArray[np.uint8]:
    """Render canonical wildfire CA state at one physical query time.

    Valid-domain cells are ``UNBURNED`` before arrival, ``BURNING`` from their
    arrival time up to but excluding ``arrival + burn_duration``, and ``BURNED``
    thereafter. Cells outside the domain remain ``UNBURNABLE``.

    The burn duration is deliberately explicit: arrival time alone cannot
    distinguish ``BURNING`` from ``BURNED``.
    """

    domain = np.asarray(domain_mask)
    arrival = np.asarray(arrival_times_s, dtype=np.float64)
    if domain.ndim != 2 or domain.dtype != np.bool_:
        raise TypeError("domain_mask must be a two-dimensional boolean array")
    if arrival.ndim != 2:
        raise ValueError("arrival_times_s must be two-dimensional")
    if arrival.shape != domain.shape:
        raise ValueError(
            f"arrival_times_s shape {arrival.shape} does not match domain {domain.shape}"
        )
    if np.isnan(arrival).any() or np.isneginf(arrival).any():
        raise ValueError("arrival_times_s may contain finite values or +inf, not NaN/-inf")
    finite_arrivals = np.isfinite(arrival)
    if (arrival[finite_arrivals] < 0.0).any():
        raise ValueError("finite arrival_times_s values must be non-negative")
    if np.any(finite_arrivals & ~domain):
        raise ValueError("finite arrival_times_s values must lie inside the domain")
    if not isfinite(time_s) or time_s < 0.0:
        raise ValueError("time_s must be finite and non-negative")
    if not isfinite(burn_duration_s) or burn_duration_s <= 0.0:
        raise ValueError("burn_duration_s must be finite and positive")

    state = np.full(domain.shape, int(FireState.UNBURNABLE), dtype=np.uint8)
    state[domain] = int(FireState.UNBURNED)

    arrived = finite_arrivals & (arrival <= time_s)
    burning = arrived & (time_s < arrival + burn_duration_s)
    burned = arrived & ~burning
    state[burning] = int(FireState.BURNING)
    state[burned] = int(FireState.BURNED)
    return state
