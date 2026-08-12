"""In-memory spatial, environmental, and landscape data for PyFireCA."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from pyfireca.gis import RasterMetadata
from pyfireca.grid import RasterGrid
from pyfireca.state import build_initial_state, validate_state_array

Array2D = NDArray[np.number]
Array3D = NDArray[np.number]
BooleanMask = NDArray[np.bool_]


@dataclass(slots=True)
class SpatialLayer:
    """One static ``(Y, X)`` or dynamic ``(T, Y, X)`` numerical layer.

    Parameters
    ----------
    values
        Numeric NumPy-compatible array. Two dimensions represent a static
        layer; three dimensions represent a time-varying layer.
    units
        Optional explicit unit label. PyFireCA does not guess or silently
        convert layer units at this generic data boundary.
    nodata
        Optional numeric NoData marker carried as metadata. It is not silently
        converted to a CA state. Domain semantics are applied explicitly by
        :func:`build_domain_mask` and :class:`LandscapeInput`.
    """

    values: Array2D | Array3D
    units: str | None = None
    nodata: float | int | None = None

    def __post_init__(self) -> None:
        self.values = np.asarray(self.values)
        if self.values.ndim not in (2, 3):
            raise ValueError("SpatialLayer values must have shape (Y, X) or (T, Y, X)")
        if not np.issubdtype(self.values.dtype, np.number):
            raise TypeError("SpatialLayer values must use a numeric dtype")
        if any(size < 1 for size in self.values.shape):
            raise ValueError("SpatialLayer dimensions must be non-empty")
        if self.units is not None and not self.units.strip():
            raise ValueError("units must be a non-empty string when provided")
        if isinstance(self.nodata, bool):
            raise TypeError("nodata must be numeric when provided")
        if self.nodata is not None and not isinstance(self.nodata, (int, float, np.number)):
            raise TypeError("nodata must be numeric when provided")
        if self.nodata is not None and np.isinf(float(self.nodata)):
            raise ValueError("nodata may be finite or NaN, but not infinite")

    @property
    def is_dynamic(self) -> bool:
        """Return whether the layer has an explicit time dimension."""

        return self.values.ndim == 3

    @property
    def spatial_shape(self) -> tuple[int, int]:
        """Return the common spatial shape ``(Y, X)``."""

        return int(self.values.shape[-2]), int(self.values.shape[-1])

    @property
    def time_size(self) -> int | None:
        """Return the number of time slices for a dynamic layer."""

        if not self.is_dynamic:
            return None
        return int(self.values.shape[0])

    def at(self, time_index: int | None = None) -> Array2D:
        """Return one ``(Y, X)`` view at the requested simulation time index.

        Static layers ignore ``time_index`` so callers can request a uniform
        snapshot across a mixture of static and dynamic layers. Dynamic layers
        require an explicit index.
        """

        if not self.is_dynamic:
            return self.values
        if time_index is None:
            raise ValueError("time_index is required for a dynamic SpatialLayer")
        if isinstance(time_index, bool) or not isinstance(time_index, int):
            raise TypeError("time_index must be an integer")
        if not 0 <= time_index < self.values.shape[0]:
            raise IndexError(
                f"time_index {time_index} is outside dynamic layer range "
                f"[0, {self.values.shape[0]})"
            )
        return self.values[time_index]


@dataclass(slots=True)
class EnvironmentalData:
    """Aligned in-memory environmental layers used by wildfire calculations.

    All layers must share one spatial ``(Y, X)`` shape. Dynamic layers must
    also share one time length in the initial index-based data contract.
    Physical time coordinates and interpolation are deferred until the project
    has a concrete weather-source requirement.
    """

    layers: Mapping[str, SpatialLayer]

    def __post_init__(self) -> None:
        self.layers = dict(self.layers)
        if not self.layers:
            raise ValueError("EnvironmentalData requires at least one layer")

        for name, layer in self.layers.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("environmental layer names must be non-empty strings")
            if not isinstance(layer, SpatialLayer):
                raise TypeError(f"layer {name!r} must be a SpatialLayer")

        spatial_shapes = {layer.spatial_shape for layer in self.layers.values()}
        if len(spatial_shapes) != 1:
            raise ValueError("all environmental layers must share one spatial shape")

        dynamic_sizes = {layer.time_size for layer in self.layers.values() if layer.is_dynamic}
        if len(dynamic_sizes) > 1:
            raise ValueError("all dynamic environmental layers must share one time size")

    @property
    def spatial_shape(self) -> tuple[int, int]:
        """Return the shared spatial shape of all layers."""

        first = next(iter(self.layers.values()))
        return first.spatial_shape

    @property
    def time_size(self) -> int | None:
        """Return the common dynamic time length, or ``None`` if all are static."""

        for layer in self.layers.values():
            if layer.is_dynamic:
                return layer.time_size
        return None

    def layer(self, name: str) -> SpatialLayer:
        """Return one named layer with a clear error for missing data."""

        try:
            return self.layers[name]
        except KeyError as exc:
            available = ", ".join(sorted(self.layers))
            message = f"unknown environmental layer {name!r}; available: {available}"
            raise KeyError(message) from exc

    def snapshot(self, time_index: int | None = None) -> dict[str, Array2D]:
        """Return aligned ``(Y, X)`` arrays for one simulation time index."""

        return {name: layer.at(time_index) for name, layer in self.layers.items()}


def nodata_mask(layer: SpatialLayer, *, time_index: int | None = None) -> BooleanMask:
    """Return cells equal to the layer's explicit NoData marker.

    This helper deliberately checks only the declared ``layer.nodata`` value.
    It does not infer that arbitrary NaN/non-finite values are NoData when no
    marker was supplied. A NaN marker is supported explicitly.
    """

    values = layer.at(time_index)
    if layer.nodata is None:
        return np.zeros(values.shape, dtype=bool)

    marker = float(layer.nodata)
    if np.isnan(marker):
        return np.isnan(values)
    return np.equal(values, layer.nodata)


def build_domain_mask(
    environment: EnvironmentalData,
    layer_names: Iterable[str],
) -> BooleanMask:
    """Build a persistent valid-domain mask from selected static NoData layers.

    Only explicitly selected **static** layers participate. A cell is inside the
    domain when none of those layers contains its declared NoData marker there.
    Dynamic weather/moisture layers are rejected because transient missing data
    must not silently turn a cell into a permanently unburnable location.
    """

    names = tuple(layer_names)
    if not names:
        raise ValueError("at least one static layer must define the simulation domain")
    if len(set(names)) != len(names):
        raise ValueError("domain layer names must be unique")

    domain = np.ones(environment.spatial_shape, dtype=bool)
    for name in names:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("domain layer names must be non-empty strings")
        layer = environment.layer(name)
        if layer.is_dynamic:
            raise ValueError(f"dynamic layer {name!r} cannot define a persistent domain mask")
        domain &= ~nodata_mask(layer)
    return domain


@dataclass(slots=True)
class LandscapeInput:
    """One validated geospatial input package for starting a CA simulation.

    The object owns one shared :class:`RasterMetadata`, aligned environmental
    arrays, and an immutable-by-convention initial state snapshot. It does not
    perform GIS reprojection/resampling and does not evolve state itself.
    """

    environment: EnvironmentalData
    metadata: RasterMetadata
    initial_state: NDArray[np.integer]

    def __post_init__(self) -> None:
        if not isinstance(self.environment, EnvironmentalData):
            raise TypeError("environment must be EnvironmentalData")
        if not isinstance(self.metadata, RasterMetadata):
            raise TypeError("metadata must be RasterMetadata")

        self.initial_state = np.asarray(self.initial_state)
        validate_state_array(self.initial_state)

        if self.environment.spatial_shape != self.metadata.shape:
            raise ValueError(
                f"environment shape {self.environment.spatial_shape} "
                f"does not match raster metadata shape {self.metadata.shape}"
            )
        if self.initial_state.shape != self.metadata.shape:
            raise ValueError(
                f"initial_state shape {self.initial_state.shape} "
                f"does not match raster metadata shape {self.metadata.shape}"
            )

    @classmethod
    def from_domain_layers(
        cls,
        environment: EnvironmentalData,
        metadata: RasterMetadata,
        *,
        domain_layer_names: Iterable[str],
        ignition_mask: BooleanMask | None = None,
    ) -> LandscapeInput:
        """Assemble a landscape using explicit static-layer NoData semantics."""

        if environment.spatial_shape != metadata.shape:
            raise ValueError(
                f"environment shape {environment.spatial_shape} "
                f"does not match raster metadata shape {metadata.shape}"
            )
        domain = build_domain_mask(environment, domain_layer_names)
        initial_state = build_initial_state(domain, ignition_mask)
        return cls(environment=environment, metadata=metadata, initial_state=initial_state)

    def make_grid(self) -> RasterGrid:
        """Create an independent CA grid from the stored initial state.

        ``RasterGrid.cell_size`` is intentionally left unset because a shared
        scalar cell size cannot safely represent every valid affine transform
        (for example rectangular or rotated pixels). Spatial metadata remains
        owned by this landscape input object.
        """

        return RasterGrid(state=self.initial_state.copy())
