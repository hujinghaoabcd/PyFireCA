"""File-based workflow for the complete baseline static wildfire simulator."""

from __future__ import annotations

import hashlib
import json
import os
import platform
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import yaml

from pyfireca.behavior.fuel_catalog import get_standard_fuel_model_record
from pyfireca.behavior.rothermel_landscape import build_static_raster_rothermel_arrival_solver
from pyfireca.behavior.rothermel_model import RothermelModel
from pyfireca.config import StaticRasterInputPaths, StaticRunConfig
from pyfireca.data import EnvironmentalData, LandscapeInput, SpatialLayer
from pyfireca.gis import RasterMetadata, read_raster, validate_raster_alignment
from pyfireca.ignition import build_ignition_times
from pyfireca.outputs import StaticSimulationOutputPaths, write_static_simulation_outputs
from pyfireca.simulator import (
    StaticWildfireSimulationRequest,
    StaticWildfireSimulationResult,
    run_static_wildfire_simulation,
)

_LAYER_UNITS: dict[str, str | None] = {
    "fuel_model": "code",
    "dead_1h_moisture": "fraction",
    "dead_10h_moisture": "fraction",
    "dead_100h_moisture": "fraction",
    "live_herbaceous_moisture": "fraction",
    "live_woody_moisture": "fraction",
    "midflame_wind_speed": "m/s",
    "wind_from_direction": "deg",
    "slope": "deg",
    "aspect": "deg",
}


@dataclass(frozen=True, slots=True)
class StaticRunArtifacts:
    """Files produced by one reproducible baseline run directory."""

    directory: Path
    resolved_config: Path
    metadata: Path
    environment: Path
    metrics: Path
    outputs: StaticSimulationOutputPaths


def _package_version() -> str:
    try:
        return version("pyfireca")
    except PackageNotFoundError:
        return "unknown"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_static_landscape(inputs: StaticRasterInputPaths) -> LandscapeInput:
    """Read, align, and assemble the ten baseline Rothermel GeoTIFF layers."""

    if not isinstance(inputs, StaticRasterInputPaths):
        raise TypeError("inputs must be StaticRasterInputPaths")

    layers: dict[str, SpatialLayer] = {}
    reference_metadata: RasterMetadata | None = None
    for name, path in inputs.named_paths():
        if not path.is_file():
            raise FileNotFoundError(f"required raster {name!r} does not exist: {path}")
        values, metadata = read_raster(path)
        if reference_metadata is None:
            reference_metadata = metadata
        else:
            validate_raster_alignment(reference_metadata, metadata)
        layers[name] = SpatialLayer(values, units=_LAYER_UNITS[name], nodata=metadata.nodata)

    if reference_metadata is None:
        raise RuntimeError("static raster input list unexpectedly contained no layers")

    environment = EnvironmentalData(layers)
    return LandscapeInput.from_domain_layers(
        environment,
        reference_metadata,
        domain_layer_names=("fuel_model",),
    )


def build_static_request_from_config(config: StaticRunConfig) -> StaticWildfireSimulationRequest:
    """Build and fully validate a simulation request from resolved file config."""

    if not isinstance(config, StaticRunConfig):
        raise TypeError("config must be StaticRunConfig")

    landscape = load_static_landscape(config.inputs)
    ignition = build_ignition_times(landscape.metadata.shape, config.ignitions)
    request = StaticWildfireSimulationRequest(
        landscape=landscape,
        cell_size_m=config.cell_size_m,
        ignition_times_s=ignition,
        use_wind_speed_limit=config.use_wind_speed_limit,
    )

    model = RothermelModel(use_wind_speed_limit=config.use_wind_speed_limit)
    build_static_raster_rothermel_arrival_solver(
        landscape,
        cell_size_m=config.cell_size_m,
        model=model,
    )
    return request


def validate_static_run(config: StaticRunConfig) -> None:
    """Validate config, files, alignment, domain, fuel codes, and behavior inputs."""

    build_static_request_from_config(config)


def _run_metadata(
    config: StaticRunConfig,
    result: StaticWildfireSimulationResult,
    landscape: LandscapeInput,
) -> dict[str, object]:
    domain = np.asarray(result.domain_mask)
    fuel_layer = np.asarray(landscape.environment.layer("fuel_model").at())
    fuel_codes = sorted({int(value) for value in np.unique(fuel_layer[domain])})
    fuel_records = [get_standard_fuel_model_record(code) for code in fuel_codes]

    return {
        "raster": {
            "shape": list(result.metadata.shape),
            "crs": result.metadata.crs,
            "transform": list(result.metadata.transform),
            "cell_size_m": result.cell_size_m,
        },
        "ignitions": [
            {"row": event.row, "col": event.col, "time_s": event.time_s}
            for event in config.ignitions
        ],
        "fuel_catalogue": [
            {
                "number": record.number,
                "code": record.code,
                "source_commit": record.source_commit,
            }
            for record in fuel_records
        ],
        "input_sha256": {
            name: _sha256_file(path) for name, path in config.inputs.named_paths()
        },
    }


def _environment_metadata() -> dict[str, object]:
    return {
        "pyfireca_version": _package_version(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": os.environ.get("GITHUB_SHA"),
    }


def run_static_config(
    config: StaticRunConfig,
) -> tuple[StaticWildfireSimulationResult, StaticRunArtifacts]:
    """Execute one resolved config and write a self-contained result directory."""

    if not isinstance(config, StaticRunConfig):
        raise TypeError("config must be StaticRunConfig")

    request = build_static_request_from_config(config)

    run_directory = config.output_directory
    if run_directory.exists() and any(run_directory.iterdir()):
        raise FileExistsError(f"output directory must be empty: {run_directory}")
    run_directory.mkdir(parents=True, exist_ok=True)

    result = run_static_wildfire_simulation(request)

    resolved_config_path = run_directory / "config.resolved.yml"
    metadata_path = run_directory / "metadata.json"
    environment_path = run_directory / "environment.json"
    metrics_path = run_directory / "metrics.json"

    resolved_config_path.write_text(
        yaml.safe_dump(config.to_dict(), sort_keys=False),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            _run_metadata(config, result, request.landscape),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    environment_path.write_text(
        json.dumps(_environment_metadata(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metrics_path.write_text(
        json.dumps(result.summary_metrics(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_paths = write_static_simulation_outputs(result, run_directory / "outputs")

    return result, StaticRunArtifacts(
        directory=run_directory,
        resolved_config=resolved_config_path,
        metadata=metadata_path,
        environment=environment_path,
        metrics=metrics_path,
        outputs=output_paths,
    )
