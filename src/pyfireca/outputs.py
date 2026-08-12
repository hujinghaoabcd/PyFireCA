"""Stable file outputs for the baseline static wildfire simulator."""

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
    """Paths written for one baseline static simulation result."""

    directory: Path
    arrival_time: Path
    state: Path
    burned_mask: Path
    metrics: Path


def terminal_state_from_result(result: StaticWildfireSimulationResult) -> np.ndarray:
    """Return the deterministic terminal state for a static arrival result."""

    if not isinstance(result, StaticWildfireSimulationResult):
        raise TypeError("result must be StaticWildfireSimulationResult")

    state = np.full(result.metadata.shape, int(FireState.UNBURNABLE), dtype=np.uint8)
    state[result.domain_mask] = int(FireState.UNBURNED)
    state[result.burned_mask] = int(FireState.BURNED)
    return state


def write_static_simulation_outputs(
    result: StaticWildfireSimulationResult,
    directory: str | Path,
) -> StaticSimulationOutputPaths:
    """Write the minimum stable GIS/JSON outputs for one static run.

    ``arrival_time.tif`` stores finite arrival seconds and uses ``-1`` as a
    file-level NoData marker for cells with no finite arrival. Arrival times are
    physically non-negative, so this marker cannot collide with a valid value.
    ``state.tif`` is the terminal canonical state rather than an arbitrary
    physical-time snapshot.
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
        metrics=output_dir / "metrics.json",
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

    paths.metrics.write_text(
        json.dumps(result.summary_metrics(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return paths
