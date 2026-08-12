"""User-facing assembly for static Canadian FBP wildfire simulations."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from time import perf_counter

import numpy as np
from numpy.typing import NDArray

from pyfireca.behavior.fbp_landscape import build_static_raster_fbp_arrival_solver
from pyfireca.data import LandscapeInput
from pyfireca.neighborhood import MooreNeighborhood, Neighborhood
from pyfireca.simulator import StaticWildfireSimulationResult
from pyfireca.state import FireState


@dataclass(frozen=True, slots=True)
class StaticFBPSimulationRequest:
    """Inputs required to run a static Canadian FBP raster simulation.

    This request deliberately owns FBP-specific scalar parameters rather than
    extending the Rothermel request with ambiguous fields.
    """

    landscape: LandscapeInput
    cell_size_m: float
    ignition_times_s: NDArray[np.floating]
    julian_day: int
    neighborhood: Neighborhood | None = None
    percent_conifer: float = 50.0
    percent_dead_fir: float = 35.0
    grass_fuel_load_kg_m2: float = 0.35
    grass_curing_percent: float = 80.0
    day_of_minimum_foliar_moisture: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.landscape, LandscapeInput):
            raise TypeError("landscape must be LandscapeInput")
        if not isfinite(self.cell_size_m) or self.cell_size_m <= 0.0:
            raise ValueError("cell_size_m must be finite and positive")
        if isinstance(self.julian_day, bool) or not isinstance(self.julian_day, int):
            raise TypeError("julian_day must be an integer")
        if not 1 <= self.julian_day <= 366:
            raise ValueError("julian_day must be in [1, 366]")
        if self.neighborhood is not None and not hasattr(self.neighborhood, "offsets"):
            raise TypeError("neighborhood must implement offsets()")

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


def run_static_fbp_simulation(
    request: StaticFBPSimulationRequest,
) -> StaticWildfireSimulationResult:
    """Run a static Canadian FBP raster simulation with the shared arrival engine."""

    if not isinstance(request, StaticFBPSimulationRequest):
        raise TypeError("request must be StaticFBPSimulationRequest")

    neighborhood = MooreNeighborhood() if request.neighborhood is None else request.neighborhood
    solver = build_static_raster_fbp_arrival_solver(
        request.landscape,
        cell_size_m=request.cell_size_m,
        julian_day=request.julian_day,
        neighborhood=neighborhood,
        percent_conifer=request.percent_conifer,
        percent_dead_fir=request.percent_dead_fir,
        grass_fuel_load_kg_m2=request.grass_fuel_load_kg_m2,
        grass_curing_percent=request.grass_curing_percent,
        day_of_minimum_foliar_moisture=request.day_of_minimum_foliar_moisture,
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
