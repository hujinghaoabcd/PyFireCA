"""Explicit edge-coupling strategies for static raster wildfire propagation."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from pyfireca.arrival import DirectionalSpreadRateProvider
from pyfireca.neighborhood import Offset


@dataclass(frozen=True, slots=True)
class HalfCellInterfaceDirectionalSpreadRate:
    """Couple source and target behavior through two equal half-cell segments.

    For an edge from source cell ``i`` to target cell ``j``, the wrapped
    provider is evaluated in the same propagation direction at both cells::

        R_i = R(source=i, direction=i→j)
        R_j = R(source=j, direction=i→j)

    The center-to-center travel time is then interpreted as two equal half-edge
    segments::

        t_ij = (d/2)/R_i + (d/2)/R_j

    For positive rates this is equivalent to the harmonic-mean edge rate::

        R_ij = 2 / (1/R_i + 1/R_j)

    If either directional rate is zero, the interface is unreachable under
    this model and the returned edge ROS is zero.

    This class is intentionally a separate strategy. It does not alter the
    existing source-cell-controlled spatial provider, so both assumptions can
    be compared in controlled CA experiments.
    """

    provider: DirectionalSpreadRateProvider

    def __post_init__(self) -> None:
        if not hasattr(self.provider, "spread_rate_m_s"):
            raise TypeError("provider must implement spread_rate_m_s()")

    def spread_rate_m_s(self, row: int, col: int, offset: Offset) -> float:
        """Return the equal-half-segment equivalent directional edge ROS."""

        drow, dcol = offset
        source_rate = self.provider.spread_rate_m_s(row, col, offset)
        target_rate = self.provider.spread_rate_m_s(row + drow, col + dcol, offset)

        for name, rate in (("source", source_rate), ("target", target_rate)):
            if not isfinite(rate) or rate < 0.0:
                raise ValueError(
                    f"wrapped provider returned invalid {name} directional ROS {rate} "
                    f"for edge source ({row}, {col}) offset {offset}"
                )

        if source_rate == 0.0 or target_rate == 0.0:
            return 0.0
        return 2.0 / (1.0 / source_rate + 1.0 / target_rate)
