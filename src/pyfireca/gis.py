"""Lightweight geospatial raster metadata, alignment, and optional GIS I/O.

The CA kernel remains independent of Rasterio/GDAL objects and file paths.
Rasterio is imported only by the optional adapter functions so the numerical
core stays usable with the base dependency set.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from math import hypot, isclose, isfinite
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from pyfireca.state import validate_state_array

AffineTuple = tuple[float, float, float, float, float, float]
RasterArray = NDArray[np.number]


class RasterAlignmentError(ValueError):
    """Raised when raster layers do not describe the same spatial grid."""


@dataclass(frozen=True, slots=True)
class RasterMetadata:
    """Minimal geospatial metadata required to align raster CA inputs.

    Parameters
    ----------
    shape
        Raster shape as ``(height, width)``.
    crs
        Non-empty canonical CRS representation supplied by a GIS adapter.
        PyFireCA does not parse or guess CRS definitions in the numerical core.
    transform
        Six affine coefficients ``(a, b, c, d, e, f)`` following the usual
        raster affine mapping::

            x = a * col + b * row + c
            y = d * col + e * row + f

    nodata
        Optional NoData marker. It is carried as metadata but is not part of
        geometric alignment by default because different source rasters may
        encode the same missing-data mask with different marker values.
    """

    shape: tuple[int, int]
    crs: str
    transform: AffineTuple
    nodata: float | int | None = None

    def __post_init__(self) -> None:
        if len(self.shape) != 2 or any(
            isinstance(size, bool) or not isinstance(size, int) or size < 1 for size in self.shape
        ):
            raise ValueError("shape must contain two positive integer dimensions")

        if not isinstance(self.crs, str) or not self.crs.strip():
            raise ValueError("crs must be a non-empty canonical string")

        if len(self.transform) != 6:
            raise ValueError("transform must contain six affine coefficients")
        if not all(isfinite(float(value)) for value in self.transform):
            raise ValueError("transform coefficients must be finite")

    @property
    def resolution(self) -> tuple[float, float]:
        """Return pixel-axis magnitudes ``(x_resolution, y_resolution)``.

        The calculation also works for rotated affine transforms; it therefore
        uses vector magnitudes instead of assuming ``b == d == 0``.
        """

        a, b, _c, d, e, _f = self.transform
        return hypot(a, d), hypot(b, e)


def _transforms_close(
    left: AffineTuple,
    right: AffineTuple,
    *,
    absolute_tolerance: float,
) -> bool:
    return all(
        isclose(a, b, rel_tol=0.0, abs_tol=absolute_tolerance)
        for a, b in zip(left, right, strict=True)
    )


def validate_raster_alignment(
    reference: RasterMetadata,
    candidate: RasterMetadata,
    *,
    absolute_tolerance: float = 1e-9,
    check_nodata: bool = False,
) -> None:
    """Require two raster metadata objects to describe one spatial grid.

    Alignment checks are explicit and fail closed. This function never
    reprojects, resamples, shifts, or crops a candidate raster.
    """

    if absolute_tolerance < 0.0 or not isfinite(absolute_tolerance):
        raise ValueError("absolute_tolerance must be finite and non-negative")

    mismatches: list[str] = []
    if reference.shape != candidate.shape:
        mismatches.append(f"shape {candidate.shape} != {reference.shape}")
    if reference.crs != candidate.crs:
        mismatches.append(f"crs {candidate.crs!r} != {reference.crs!r}")
    if not _transforms_close(
        reference.transform,
        candidate.transform,
        absolute_tolerance=absolute_tolerance,
    ):
        mismatches.append(
            f"transform {candidate.transform!r} != {reference.transform!r} "
            f"within atol={absolute_tolerance}"
        )
    if check_nodata and reference.nodata != candidate.nodata:
        mismatches.append(f"nodata {candidate.nodata!r} != {reference.nodata!r}")

    if mismatches:
        raise RasterAlignmentError("raster alignment mismatch: " + "; ".join(mismatches))


def validate_named_raster_alignment(
    reference: RasterMetadata,
    candidates: Mapping[str, RasterMetadata],
    *,
    absolute_tolerance: float = 1e-9,
    check_nodata: bool = False,
) -> None:
    """Validate multiple named raster layers against one reference grid."""

    for name, candidate in candidates.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("candidate raster names must be non-empty strings")
        if not isinstance(candidate, RasterMetadata):
            raise TypeError(f"candidate {name!r} must be RasterMetadata")
        try:
            validate_raster_alignment(
                reference,
                candidate,
                absolute_tolerance=absolute_tolerance,
                check_nodata=check_nodata,
            )
        except RasterAlignmentError as exc:
            raise RasterAlignmentError(f"layer {name!r}: {exc}") from exc


def _require_rasterio():
    """Import the optional Rasterio dependency with an actionable error."""

    try:
        import rasterio
        from rasterio import Affine
    except ImportError as exc:
        raise ImportError(
            "Rasterio support is optional; install PyFireCA with the 'gis' extra"
        ) from exc
    return rasterio, Affine


def _metadata_from_rasterio_dataset(dataset) -> RasterMetadata:
    """Convert an open Rasterio dataset to the lightweight metadata contract."""

    if dataset.crs is None:
        raise ValueError("raster dataset must define a CRS")

    transform = dataset.transform
    return RasterMetadata(
        shape=(int(dataset.height), int(dataset.width)),
        crs=dataset.crs.to_string(),
        transform=(
            float(transform.a),
            float(transform.b),
            float(transform.c),
            float(transform.d),
            float(transform.e),
            float(transform.f),
        ),
        nodata=dataset.nodata,
    )


def read_raster(path: str | Path, *, band: int = 1) -> tuple[RasterArray, RasterMetadata]:
    """Read one numeric raster band and return its array plus spatial metadata.

    The adapter reads source values as stored. It does not reproject, resample,
    mask, fill NoData, or change units.
    """

    if isinstance(band, bool) or not isinstance(band, int) or band < 1:
        raise ValueError("band must be a positive integer")

    rasterio, _Affine = _require_rasterio()
    with rasterio.open(path) as dataset:
        if band > dataset.count:
            raise IndexError(f"band {band} is outside raster band range [1, {dataset.count}]")
        metadata = _metadata_from_rasterio_dataset(dataset)
        values = np.asarray(dataset.read(band))

    if not np.issubdtype(values.dtype, np.number):
        raise TypeError("raster band must use a numeric dtype")
    return values, metadata


def write_raster(
    path: str | Path,
    values: RasterArray,
    metadata: RasterMetadata,
) -> None:
    """Write one GeoTIFF band using explicit reference metadata.

    The function requires exact array/metadata shape agreement and preserves
    the supplied CRS, affine transform, dtype, and NoData marker. It does not
    create parent directories or alter grid geometry.
    """

    values = np.asarray(values)
    if values.ndim != 2:
        raise ValueError("values must be a two-dimensional raster array")
    if not np.issubdtype(values.dtype, np.number):
        raise TypeError("values must use a numeric dtype")
    if values.shape != metadata.shape:
        raise ValueError(f"values shape {values.shape} does not match metadata {metadata.shape}")

    rasterio, Affine = _require_rasterio()
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=metadata.shape[0],
        width=metadata.shape[1],
        count=1,
        dtype=values.dtype,
        crs=metadata.crs,
        transform=Affine(*metadata.transform),
        nodata=metadata.nodata,
    ) as dataset:
        dataset.write(values, 1)


def write_state_raster(
    path: str | Path,
    state: NDArray[np.integer],
    metadata: RasterMetadata,
) -> None:
    """Write a canonical wildfire-state GeoTIFF.

    State rasters are complete CA outputs rather than masked source rasters.
    They therefore use the canonical integer state codes as ``uint8`` and set
    GeoTIFF NoData to ``None``. In particular, state code ``0`` remains the
    explicit ``UNBURNABLE`` model state and is never reinterpreted as file-level
    NoData.
    """

    state = np.asarray(state)
    validate_state_array(state)
    if state.shape != metadata.shape:
        raise ValueError(f"state shape {state.shape} does not match metadata {metadata.shape}")

    output_metadata = replace(metadata, nodata=None)
    write_raster(path, state.astype(np.uint8, copy=False), output_metadata)
