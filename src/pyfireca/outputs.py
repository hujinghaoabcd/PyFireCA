"""Stable spatial outputs for the baseline static wildfire simulator."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from pyfireca.gis import write_raster, write_state_raster
from pyfireca.simulator import StaticWildfireSimulationResult
from pyfireca.state import FireState

_ARRIVAL_NODATA_S = -1.0


@dataclass(frozen=True, slots=True)
class StaticSimulationOutputPaths:
    """Spatial paths written for one baseline static simulation result."""

    directory: Path
    arrival_time: Path
    state: Path
    burned_mask: Path
    perimeter: Path


def terminal_state_from_result(result: StaticWildfireSimulationResult) -> np.ndarray:
    """Return the deterministic terminal state for a static arrival result."""

    if not isinstance(result, StaticWildfireSimulationResult):
        raise TypeError("result must be StaticWildfireSimulationResult")

    state = np.full(result.metadata.shape, int(FireState.UNBURNABLE), dtype=np.uint8)
    state[result.domain_mask] = int(FireState.UNBURNED)
    state[result.burned_mask] = int(FireState.BURNED)
    return state


def write_burned_perimeter_geojson(
    result: StaticWildfireSimulationResult,
    path: str | Path,
) -> Path:
    """Polygonize the eventual burned footprint and write RFC-7946 GeoJSON.

    Raster cells are polygonized in the source raster CRS and then transformed
    to WGS84 before serialization. This avoids writing projected coordinates
    into a file format whose interoperable coordinate system is longitude/
    latitude WGS84.
    """

    if not isinstance(result, StaticWildfireSimulationResult):
        raise TypeError("result must be StaticWildfireSimulationResult")

    try:
        from rasterio.features import shapes
        from rasterio.transform import Affine
        from rasterio.warp import transform_geom
    except ImportError as exc:
        raise ImportError(
            "burned perimeter output requires the optional GIS dependency; "
            "install PyFireCA with the 'gis' extra"
        ) from exc

    burned = result.burned_mask.astype(np.uint8, copy=False)
    affine = Affine(*result.metadata.transform)
    features = []
    for index, (geometry, value) in enumerate(
        shapes(burned, mask=result.burned_mask, transform=affine),
        start=1,
    ):
        if int(value) != 1:
            continue
        wgs84_geometry = transform_geom(
            result.metadata.crs,
            "EPSG:4326",
            geometry,
            antimeridian_cutting=True,
            precision=12,
        )
        features.append(
            {
                "type": "Feature",
                "id": index,
                "properties": {"burned": 1},
                "geometry": wgs84_geometry,
            }
        )

    output = Path(path)
    output.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def write_static_simulation_outputs(
    result: StaticWildfireSimulationResult,
    directory: str | Path,
) -> StaticSimulationOutputPaths:
    """Write the stable spatial outputs for one static run.

    ``arrival_time.tif`` stores finite arrival seconds and uses ``-1`` as a
    file-level NoData marker for cells with no finite arrival. Arrival times are
    physically non-negative, so this marker cannot collide with a valid value.
    ``state.tif`` is the terminal canonical state rather than an arbitrary
    physical-time snapshot. Run-level statistics belong to the run directory's
    single root ``metrics.json`` and are not duplicated here.
    """

    if not isinstance(result, StaticWildfireSimulationResult):
        raise TypeError("result must be StaticWildfireSimulationResult")

    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = StaticSimulationOutputPaths(
        directory=output_dir,
        arrival_time=output_dir / "arrival_time.tif",
        state=output_dir / "state.tif",
        burned_mask=output_dir / "burned_mask.tif",
        perimeter=output_dir / "perimeter.geojson",
    )

    arrival = np.where(
        np.isfinite(result.arrival_times_s),
        result.arrival_times_s,
        _ARRIVAL_NODATA_S,
    ).astype(np.float64, copy=False)
    arrival_metadata = replace(result.metadata, nodata=_ARRIVAL_NODATA_S)
    write_raster(paths.arrival_time, arrival, arrival_metadata)

    write_state_raster(paths.state, terminal_state_from_result(result), result.metadata)

    burned = result.burned_mask.astype(np.uint8, copy=False)
    burned_metadata = replace(result.metadata, nodata=None)
    write_raster(paths.burned_mask, burned, burned_metadata)
    write_burned_perimeter_geojson(result, paths.perimeter)
    return paths
