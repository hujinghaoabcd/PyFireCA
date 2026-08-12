"""User-facing assembly for the first complete static wildfire simulator."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from time import perf_counter

import numpy as np
from numpy.typing import NDArray

from pyfireca.arrival import arrival_times_to_state
from pyfireca.behavior.rothermel_landscape import build_static_raster_rothermel_arrival_solver
from pyfireca.behavior.rothermel_model import RothermelModel
from pyfireca.data import LandscapeInput
from pyfireca.gis import RasterMetadata
from pyfireca.neighborhood import MooreNeighborhood, Neighborhood
from pyfireca.state import FireState


@dataclass(frozen=True, slots=True)
class StaticWildfireSimulationRequest:
    """Inputs required to run the validated static wildfire baseline.

    ``ignition_times_s`` uses finite non-negative seconds for explicit ignition
    events and positive infinity elsewhere. The default neighborhood is the
    immediate Moore-8 stencil used by the current physical baseline.
    """

    landscape: LandscapeInput
    cell_size_m: float
    ignition_times_s: NDArray[np.floating]
    neighborhood: Neighborhood | None = None
    use_wind_speed_limit: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.landscape, LandscapeInput):
            raise TypeError("landscape must be LandscapeInput")
        if not isfinite(self.cell_size_m) or self.cell_size_m <= 0.0:
            raise ValueError("cell_size_m must be finite and positive")
        if self.neighborhood is not None and not hasattr(self.neighborhood, "offsets"):
            raise TypeError("neighborhood must implement offsets()")
        if not isinstance(self.use_wind_speed_limit, bool):
            raise TypeError("use_wind_speed_limit must be a bool")

        ignition = np.asarray(self.ignition_times_s, dtype=np.float64)
        if ignition.ndim != 2 or ignition.shape != self.landscape.metadata.shape:
            raise ValueError(
                "ignition_times_s must be a two-dimensional array matching landscape shape"
            )
        if np.isnan(ignition).any() or np.isneginf(ignition).any():
            raise ValueError("ignition_times_s may contain finite values or +inf, not NaN/-inf")
        finite = np.isfinite(ignition)
        if not np.any(finite):
            raise ValueError("at least one finite ignition time is required")
        if np.any(ignition[finite] < 0.0):
            raise ValueError("finite ignition times must be non-negative")

        domain = np.asarray(self.landscape.initial_state) != int(FireState.UNBURNABLE)
        if np.any(finite & ~domain):
            raise ValueError("finite ignition times must lie inside the burnable domain")

        object.__setattr__(self, "ignition_times_s", ignition.copy())


@dataclass(frozen=True, slots=True)
class StaticWildfireSimulationResult:
    """Deterministic outputs from one static wildfire simulation run."""

    arrival_times_s: NDArray[np.float64]
    domain_mask: NDArray[np.bool_]
    metadata: RasterMetadata
    cell_size_m: float
    runtime_s: float

    def __post_init__(self) -> None:
        arrival = np.asarray(self.arrival_times_s, dtype=np.float64)
        domain = np.asarray(self.domain_mask)
        if arrival.ndim != 2:
            raise ValueError("arrival_times_s must be two-dimensional")
        if domain.ndim != 2 or domain.dtype != np.bool_:
            raise TypeError("domain_mask must be a two-dimensional boolean array")
        if arrival.shape != domain.shape or arrival.shape != self.metadata.shape:
            raise ValueError("arrival, domain, and raster metadata shapes must match")
        if np.isnan(arrival).any() or np.isneginf(arrival).any():
            raise ValueError("arrival_times_s may contain finite values or +inf, not NaN/-inf")
        if not isfinite(self.cell_size_m) or self.cell_size_m <= 0.0:
            raise ValueError("cell_size_m must be finite and positive")
        if not isfinite(self.runtime_s) or self.runtime_s < 0.0:
            raise ValueError("runtime_s must be finite and non-negative")

        object.__setattr__(self, "arrival_times_s", arrival.copy())
        object.__setattr__(self, "domain_mask", domain.copy())

    @property
    def burned_mask(self) -> NDArray[np.bool_]:
        """Return the eventual reachable/burned footprint of the static run."""

        return self.domain_mask & np.isfinite(self.arrival_times_s)

    @property
    def burned_cell_count(self) -> int:
        """Return the number of cells eventually reached by fire."""

        return int(np.count_nonzero(self.burned_mask))

    @property
    def burned_area_m2(self) -> float:
        """Return eventual burned raster area in square metres."""

        return self.burned_cell_count * self.cell_size_m**2

    @property
    def first_arrival_s(self) -> float:
        """Return the earliest finite arrival time."""

        return float(np.min(self.arrival_times_s[self.burned_mask]))

    @property
    def last_arrival_s(self) -> float:
        """Return the latest finite arrival time in the eventual footprint."""

        return float(np.max(self.arrival_times_s[self.burned_mask]))

    @property
    def unreachable_domain_cell_count(self) -> int:
        """Return burnable-domain cells not reachable from supplied ignitions."""

        return int(np.count_nonzero(self.domain_mask & ~self.burned_mask))

    def state_at(self, *, time_s: float, burn_duration_s: float) -> NDArray[np.uint8]:
        """Render canonical ``FireState`` values at one physical query time."""

        return arrival_times_to_state(
            self.domain_mask,
            self.arrival_times_s,
            time_s=time_s,
            burn_duration_s=burn_duration_s,
        )

    def burned_mask_at(self, time_s: float) -> NDArray[np.bool_]:
        """Return cells reached by fire at or before ``time_s``."""

        if not isfinite(time_s) or time_s < 0.0:
            raise ValueError("time_s must be finite and non-negative")
        finite_arrival = np.isfinite(self.arrival_times_s)
        reached_by_time = self.arrival_times_s <= time_s
        return self.domain_mask & finite_arrival & reached_by_time

    def summary_metrics(self) -> dict[str, int | float]:
        """Return stable baseline summary statistics for reporting/output."""

        return {
            "domain_cell_count": int(np.count_nonzero(self.domain_mask)),
            "burned_cell_count": self.burned_cell_count,
            "unreachable_domain_cell_count": self.unreachable_domain_cell_count,
            "burned_area_m2": self.burned_area_m2,
            "first_arrival_s": self.first_arrival_s,
            "last_arrival_s": self.last_arrival_s,
            "runtime_s": self.runtime_s,
        }


def run_static_wildfire_simulation(
    request: StaticWildfireSimulationRequest,
) -> StaticWildfireSimulationResult:
    """Run the validated static raster Rothermel wildfire baseline."""

    if not isinstance(request, StaticWildfireSimulationRequest):
        raise TypeError("request must be StaticWildfireSimulationRequest")

    neighborhood = MooreNeighborhood() if request.neighborhood is None else request.neighborhood
    model = RothermelModel(use_wind_speed_limit=request.use_wind_speed_limit)
    solver = build_static_raster_rothermel_arrival_solver(
        request.landscape,
        cell_size_m=request.cell_size_m,
        neighborhood=neighborhood,
        model=model,
    )
    domain = np.asarray(request.landscape.initial_state) != int(FireState.UNBURNABLE)

    started = perf_counter()
    arrival = solver.solve(domain, request.ignition_times_s)
    runtime_s = perf_counter() - started

    return StaticWildfireSimulationResult(
        arrival_times_s=arrival,
        domain_mask=domain,
        metadata=request.landscape.metadata,
        cell_size_m=request.cell_size_m,
        runtime_s=runtime_s,
    )
