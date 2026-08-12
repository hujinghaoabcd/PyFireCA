"""Thin landscape assembly for static raster Rothermel arrival propagation."""

from __future__ import annotations

from math import isclose, isfinite

import numpy as np

from pyfireca.arrival import StaticArrivalTimeSolver
from pyfireca.behavior.rothermel_layers import (
    RothermelRasterLayerNames,
    StaticRasterRothermelInputsProvider,
)
from pyfireca.behavior.rothermel_model import RothermelModel
from pyfireca.behavior.rothermel_spatial import StaticSpatialRothermelDirectionalSpreadRate
from pyfireca.data import LandscapeInput
from pyfireca.neighborhood import MooreNeighborhood, Neighborhood
from pyfireca.state import FireState


def _validate_north_up_square_metric_grid(
    landscape: LandscapeInput,
    cell_size_m: float,
) -> None:
    """Require the current square-grid geometry assumed by the arrival solver.

    ``cell_size_m`` is explicit because :class:`RasterMetadata` intentionally
    stores a CRS string without parsing its linear units. The caller therefore
    asserts that the affine coordinates are metres; this helper verifies only
    the affine geometry and consistency with that declared metric cell size.
    """

    if not isfinite(cell_size_m) or cell_size_m <= 0.0:
        raise ValueError("cell_size_m must be finite and positive")

    a, b, _c, d, e, _f = landscape.metadata.transform
    if not isclose(b, 0.0, rel_tol=0.0, abs_tol=1e-12) or not isclose(
        d,
        0.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("static raster Rothermel arrival currently requires a north-up grid")
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


def build_static_raster_rothermel_arrival_solver(
    landscape: LandscapeInput,
    *,
    cell_size_m: float,
    neighborhood: Neighborhood | None = None,
    model: RothermelModel | None = None,
    names: RothermelRasterLayerNames | None = None,
) -> StaticArrivalTimeSolver:
    """Assemble the validated static raster Rothermel-to-arrival pipeline.

    This is a convenience factory only. It does not infer ignition times,
    mutate landscape state, interpolate weather, or run the solver. The domain
    is the set of cells whose canonical initial state is not ``UNBURNABLE``.
    """

    if not isinstance(landscape, LandscapeInput):
        raise TypeError("landscape must be LandscapeInput")
    _validate_north_up_square_metric_grid(landscape, cell_size_m)

    resolved_neighborhood = MooreNeighborhood() if neighborhood is None else neighborhood
    if not hasattr(resolved_neighborhood, "offsets"):
        raise TypeError("neighborhood must implement offsets()")

    resolved_model = RothermelModel() if model is None else model
    if not isinstance(resolved_model, RothermelModel):
        raise TypeError("model must be RothermelModel")

    resolved_names = RothermelRasterLayerNames() if names is None else names
    if not isinstance(resolved_names, RothermelRasterLayerNames):
        raise TypeError("names must be RothermelRasterLayerNames")

    domain = np.asarray(landscape.initial_state) != int(FireState.UNBURNABLE)
    inputs_provider = StaticRasterRothermelInputsProvider(
        landscape.environment,
        domain,
        resolved_names,
    )
    spread_provider = StaticSpatialRothermelDirectionalSpreadRate(
        resolved_model,
        inputs_provider,
    )
    return StaticArrivalTimeSolver(
        neighborhood=resolved_neighborhood,
        cell_size_m=cell_size_m,
        spread_rate_provider=spread_provider,
    )
