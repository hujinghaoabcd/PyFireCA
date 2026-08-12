"""In-memory spatial and time-varying environmental data for PyFireCA."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

Array2D = NDArray[np.number]
Array3D = NDArray[np.number]


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
        Optional numeric NoData marker carried as metadata. Masking and GIS
        serialization policy are intentionally handled outside CA kernels.
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

        dynamic_sizes = {
            layer.time_size for layer in self.layers.values() if layer.is_dynamic
        }
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
            raise KeyError(f"unknown environmental layer {name!r}; available: {available}") from exc

    def snapshot(self, time_index: int | None = None) -> dict[str, Array2D]:
        """Return aligned ``(Y, X)`` arrays for one simulation time index."""

        return {name: layer.at(time_index) for name, layer in self.layers.items()}
