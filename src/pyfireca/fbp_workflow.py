"""File workflow for self-contained static Canadian FBP simulations."""

from __future__ import annotations

import json

import numpy as np
import yaml

from pyfireca.behavior.fbp_landscape import build_static_raster_fbp_arrival_solver
from pyfireca.data import EnvironmentalData, LandscapeInput, SpatialLayer, nodata_mask
from pyfireca.fbp_config import StaticFBPRasterInputPaths, StaticFBPRunConfig
from pyfireca.fbp_simulator import StaticFBPSimulationRequest, run_static_fbp_simulation
from pyfireca.gis import RasterMetadata, read_raster, validate_raster_alignment
from pyfireca.ignition import build_ignition_times
from pyfireca.outputs import write_static_simulation_outputs
from pyfireca.simulator import StaticWildfireSimulationResult
from pyfireca.state import build_initial_state
from pyfireca.workflow import (
    StaticRunArtifacts,
    _environment_metadata,
    _run_log,
    _sha256_file,
)

_FBP_LAYER_UNITS: dict[str, str | None] = {
    "fbp_fuel_type": "code",
    "ffmc": "code",
    "bui": "index",
    "wind_speed_10m": "km/h",
    "wind_from_direction": "deg",
    "slope_percent": "percent",
    "aspect": "deg",
    "latitude": "deg",
    "longitude": "deg",
    "elevation": "m",
}


def load_static_fbp_landscape(inputs: StaticFBPRasterInputPaths) -> LandscapeInput:
    """Read, align, and assemble the ten static Canadian FBP GeoTIFF layers."""

    if not isinstance(inputs, StaticFBPRasterInputPaths):
        raise TypeError("inputs must be StaticFBPRasterInputPaths")

    layers: dict[str, SpatialLayer] = {}
    reference_metadata: RasterMetadata | None = None
    for name, path in inputs.named_paths():
        if not path.is_file():
            raise FileNotFoundError(f"required FBP raster {name!r} does not exist: {path}")
        values, metadata = read_raster(path)
        if reference_metadata is None:
            reference_metadata = metadata
        else:
            validate_raster_alignment(reference_metadata, metadata)
        layers[name] = SpatialLayer(
            values,
            units=_FBP_LAYER_UNITS[name],
            nodata=metadata.nodata,
        )

    if reference_metadata is None:
        raise RuntimeError("FBP raster input list unexpectedly contained no layers")

    environment = EnvironmentalData(layers)
    fuel_layer = environment.layer("fbp_fuel_type")
    fuel_values = np.asarray(fuel_layer.at())
    valid_fuel_cells = ~nodata_mask(fuel_layer) & np.isfinite(fuel_values)
    nonfuel = np.isin(fuel_values, (19, 20))
    domain = valid_fuel_cells & ~nonfuel
    initial_state = build_initial_state(domain)
    return LandscapeInput(
        environment=environment,
        metadata=reference_metadata,
        initial_state=initial_state,
    )


def build_static_fbp_request_from_config(config: StaticFBPRunConfig) -> StaticFBPSimulationRequest:
    """Build a simulation request from one resolved FBP file configuration."""

    if not isinstance(config, StaticFBPRunConfig):
        raise TypeError("config must be StaticFBPRunConfig")
    landscape = load_static_fbp_landscape(config.inputs)
    ignition = build_ignition_times(landscape.metadata.shape, config.ignitions)
    return StaticFBPSimulationRequest(
        landscape=landscape,
        cell_size_m=config.cell_size_m,
        ignition_times_s=ignition,
        julian_day=config.julian_day,
        percent_conifer=config.percent_conifer,
        percent_dead_fir=config.percent_dead_fir,
        grass_fuel_load_kg_m2=config.grass_fuel_load_kg_m2,
        grass_curing_percent=config.grass_curing_percent,
        day_of_minimum_foliar_moisture=config.day_of_minimum_foliar_moisture,
    )


def _validate_fbp_request(request: StaticFBPSimulationRequest) -> None:
    """Validate FBP layers, units, fuel codes, and raster geometry without propagation."""

    build_static_raster_fbp_arrival_solver(
        request.landscape,
        cell_size_m=request.cell_size_m,
        julian_day=request.julian_day,
        neighborhood=request.neighborhood,
        percent_conifer=request.percent_conifer,
        percent_dead_fir=request.percent_dead_fir,
        grass_fuel_load_kg_m2=request.grass_fuel_load_kg_m2,
        grass_curing_percent=request.grass_curing_percent,
        day_of_minimum_foliar_moisture=request.day_of_minimum_foliar_moisture,
    )


def validate_static_fbp_run(config: StaticFBPRunConfig) -> None:
    """Validate FBP config, files, alignment, domain, units, and behavior inputs."""

    _validate_fbp_request(build_static_fbp_request_from_config(config))


def _fbp_metadata(
    config: StaticFBPRunConfig,
    result: StaticWildfireSimulationResult,
    landscape: LandscapeInput,
) -> dict[str, object]:
    domain = np.asarray(result.domain_mask)
    fuel_values = np.asarray(landscape.environment.layer("fbp_fuel_type").at())
    fuel_codes = sorted({int(value) for value in np.unique(fuel_values[domain])})
    return {
        "behavior": {
            "model": "canadian_fbp",
            "scientific_reference": [
                "Forestry Canada Fire Danger Group (1992), ST-X-3",
                "Wotton, Alexander & Taylor (2009), GLC-X-10",
            ],
            "julian_day": config.julian_day,
            "fuel_codes": fuel_codes,
            "implementation": "self-contained PyFireCA runtime",
        },
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
        "input_sha256": {
            name: _sha256_file(path) for name, path in config.inputs.named_paths()
        },
    }


def run_static_fbp_config(
    config: StaticFBPRunConfig,
) -> tuple[StaticWildfireSimulationResult, StaticRunArtifacts]:
    """Execute one FBP config and write the common reproducible run directory."""

    if not isinstance(config, StaticFBPRunConfig):
        raise TypeError("config must be StaticFBPRunConfig")

    request = build_static_fbp_request_from_config(config)
    _validate_fbp_request(request)

    run_directory = config.output_directory
    if run_directory.exists() and any(run_directory.iterdir()):
        raise FileExistsError(f"output directory must be empty: {run_directory}")
    run_directory.mkdir(parents=True, exist_ok=True)

    result = run_static_fbp_simulation(request)
    resolved_config_path = run_directory / "config.resolved.yml"
    metadata_path = run_directory / "metadata.json"
    environment_path = run_directory / "environment.json"
    metrics_path = run_directory / "metrics.json"
    log_path = run_directory / "log.txt"

    resolved_config_path.write_text(
        yaml.safe_dump(config.to_dict(), sort_keys=False),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(_fbp_metadata(config, result, request.landscape), indent=2, sort_keys=True)
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
    log_path.write_text(_run_log(result), encoding="utf-8")
    output_paths = write_static_simulation_outputs(result, run_directory / "outputs")

    return result, StaticRunArtifacts(
        directory=run_directory,
        resolved_config=resolved_config_path,
        metadata=metadata_path,
        environment=environment_path,
        metrics=metrics_path,
        log=log_path,
        outputs=output_paths,
    )
