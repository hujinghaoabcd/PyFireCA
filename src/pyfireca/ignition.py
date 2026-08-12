"""User-facing ignition events for physical-time wildfire simulations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class IgnitionEvent:
    """Ignite one raster cell at one physical time in seconds."""

    row: int
    col: int
    time_s: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.row, bool) or not isinstance(self.row, int):
            raise TypeError("row must be an integer")
        if isinstance(self.col, bool) or not isinstance(self.col, int):
            raise TypeError("col must be an integer")
        if not isfinite(self.time_s) or self.time_s < 0.0:
            raise ValueError("time_s must be finite and non-negative")


def build_ignition_times(
    shape: tuple[int, int],
    events: Iterable[IgnitionEvent],
) -> NDArray[np.float64]:
    """Build an ``(Y, X)`` ignition-time field from explicit events.

    Cells without an external ignition receive positive infinity. If multiple
    events target the same cell, the earliest event wins.
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

    resolved_events = tuple(events)
    if not resolved_events:
        raise ValueError("at least one ignition event is required")

    ignition = np.full(shape, np.inf, dtype=np.float64)
    for event in resolved_events:
        if not isinstance(event, IgnitionEvent):
            raise TypeError("events must contain IgnitionEvent instances")
        if not 0 <= event.row < shape[0] or not 0 <= event.col < shape[1]:
            raise IndexError(
                f"ignition event ({event.row}, {event.col}) is outside raster shape {shape}"
            )
        ignition[event.row, event.col] = min(ignition[event.row, event.col], event.time_s)

    return ignition
