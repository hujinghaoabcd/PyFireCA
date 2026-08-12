"""Thin landscape assembly for static raster Canadian FBP arrival propagation."""

from __future__ import annotations

from math import isclose, isfinite

import numpy as np

from pyfireca.arrival import StaticArrivalTimeSolver
from pyfireca.behavior.fbp import FBPModel
from pyfireca.behavior.fbp_layers import FBPRasterLayerNames, StaticRasterFBPInputsProvider
from pyfireca.behavior.fbp_spatial import StaticSpatialFBPDirectionalSpreadRate
from pyfireca.data import LandscapeInput
from pyfireca.neighborhood import MooreNeighborhood, Neighborhood
from pyfireca.state import FireState


def _validate_fbp_north_up_square_metric_grid(
    landscape: LandscapeInput,
    cell_size_m: float,
) -> None:
    """Validate the raster geometry assumed by the current FBP arrival solver."""

    if not isfinite(cell_size_m) or cell_size_m <= 0.0:
        raise ValueError("cell_size_m must be finite and positive")

    a, b, _c, d, e, _f = landscape.metadata.transform
    if not isclose(b, 0.0, rel_tol=0.0, abs_tol=1e-12) or not isclose(
        d,
        0.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("static raster FBP arrival currently requires a north-up grid")
    if a <= 0.0 or e >= 0.0:
        raise ValueError("north-up raster transform must have positive x step and negative y step")
    if not isclose(a, cell_size_m, rel_tol=0.0, abs_tol=1e-9) or not isclose(
        -e,
        cell_size_m,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError(
            "landscape affine pixel size does not match the declared square cell_size_m"
        )


def build_static_raster_fbp_arrival_solver(
    landscape: LandscapeInput,
    *,
    cell_size_m: float,
    julian_day: int,
    neighborhood: Neighborhood | None = None,
    model: FBPModel | None = None,
    names: FBPRasterLayerNames | None = None,
    percent_conifer: float = 50.0,
    percent_dead_fir: float = 35.0,
    grass_fuel_load_kg_m2: float = 0.35,
    grass_curing_percent: float = 80.0,
    day_of_minimum_foliar_moisture: int | None = None,
) -> StaticArrivalTimeSolver:
    """Assemble the self-contained static raster FBP-to-arrival pipeline.

    The factory does not infer FBP variables from Rothermel layers. The
    landscape must already contain the explicit layers named by
    :class:`FBPRasterLayerNames`.
    """

    if not isinstance(landscape, LandscapeInput):
        raise TypeError("landscape must be LandscapeInput")
    _validate_fbp_north_up_square_metric_grid(landscape, cell_size_m)

    resolved_neighborhood = MooreNeighborhood() if neighborhood is None else neighborhood
    if not hasattr(resolved_neighborhood, "offsets"):
        raise TypeError("neighborhood must implement offsets()")

    resolved_model = FBPModel() if model is None else model
    if not isinstance(resolved_model, FBPModel):
        raise TypeError("model must be FBPModel")

    resolved_names = FBPRasterLayerNames() if names is None else names
    if not isinstance(resolved_names, FBPRasterLayerNames):
        raise TypeError("names must be FBPRasterLayerNames")

    domain = np.asarray(landscape.initial_state) != int(FireState.UNBURNABLE)
    inputs_provider = StaticRasterFBPInputsProvider(
        environment=landscape.environment,
        domain_mask=domain,
        julian_day=julian_day,
        names=resolved_names,
        percent_conifer=percent_conifer,
        percent_dead_fir=percent_dead_fir,
        grass_fuel_load_kg_m2=grass_fuel_load_kg_m2,
        grass_curing_percent=grass_curing_percent,
        day_of_minimum_foliar_moisture=day_of_minimum_foliar_moisture,
    )
    spread_provider = StaticSpatialFBPDirectionalSpreadRate(
        model=resolved_model,
        inputs_provider=inputs_provider,
    )
    return StaticArrivalTimeSolver(
        neighborhood=resolved_neighborhood,
        cell_size_m=cell_size_m,
        spread_rate_provider=spread_provider,
    )
