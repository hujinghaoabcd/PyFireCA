# Changelog

All notable changes to PyFireCA are documented here.

PyFireCA is pre-1.0 research software. API changes are allowed during alpha development, but changes that affect users, experiments, reproducibility, licensing, or scientific interpretation must be recorded.

## [Unreleased]

### Added — simulator workflow

- User-facing `IgnitionEvent` and `build_ignition_times()` helpers supporting single, multiple, delayed, and duplicate ignition events.
- `StaticWildfireSimulationRequest`, `StaticWildfireSimulationResult`, and `run_static_wildfire_simulation()` as the first complete programmatic static wildfire simulator API.
- Stable result helpers for burned footprint, burned area, first/last arrival, unreachable-domain count, physical-time state snapshots, and summary metrics.
- Strict version-1 YAML configuration through `StaticRasterInputPaths`, `StaticRunConfig`, and `load_static_run_config()`.
- Runtime YAML support through the small `PyYAML` dependency; CLI remains standard-library `argparse`.
- Console entry point:
  - `pyfireca validate config.yml`
  - `pyfireca run config.yml`
- File-based workflow that resolves YAML paths relative to the config file, reads the ten required GeoTIFFs, validates alignment/data contracts, assembles the existing validated simulator, and writes a reproducible run directory.
- Reproducible run artifacts:
  - `config.resolved.yml`
  - `metadata.json`
  - `environment.json`
  - `metrics.json`
  - `log.txt`
- Input SHA-256 recording and encountered-fuel provenance in `metadata.json`.
- Stable spatial outputs:
  - `outputs/arrival_time.tif`
  - `outputs/state.tif`
  - `outputs/burned_mask.tif`
  - `outputs/perimeter.geojson`
- Final burned-footprint polygonization with source-CRS → WGS84 transformation before GeoJSON serialization.
- `examples/static_run.yml` as the version-1 file-workflow configuration example.
- `docs/RUNNING_SIMULATOR.md` as the detailed baseline user manual.
- `docs/RELEASE_CHECKLIST.md` as the release-readiness gate for the first frozen baseline.

### Added — scientific baseline

- Explicit wildfire `FireState`, `RasterGrid`, Moore/Von Neumann neighborhoods, synchronous `TransitionRule`, `Simulation`, and deterministic `NeighborIgnitionRule` reference CA path.
- Generic `FireBehaviorModel` / `FireBehaviorResult` contracts.
- `SpatialLayer`, `EnvironmentalData`, `LandscapeInput`, NoData/domain helpers, and fail-fast environmental completeness checks.
- Lightweight `RasterMetadata`, full raster-alignment validation, optional Rasterio `read_raster()` / `write_raster()`, and canonical state-raster output.
- SI/native-unit Rothermel conversions and six-class fuel contract.
- Albini-adjusted Rothermel base-spread equations and validated `RothermelModel.compute()` assembly.
- Wind, slope, effective-wind inversion, optional wind-speed limiting, and non-collinear wind/slope vector composition.
- Dynamic Scott–Burgan herbaceous curing/load transfer with pinned GR1 regression.
- Behave/Catchpole surface-fire ellipse, backing/flanking spread, and arbitrary-angle `FromIgnitionPoint` radial ROS.
- Physical edge-distance / direction-specific-ROS travel-time helpers.
- `StaticArrivalTimeSolver` and `arrival_times_to_state()` for static physical earliest-arrival propagation.
- Homogeneous and heterogeneous static directional Rothermel spread providers.
- Strict raster-layer-to-Rothermel adapter and `build_static_raster_rothermel_arrival_solver()` landscape factory.
- Audited Anderson standard fuel catalogue **FM1–FM13** from pinned USFS Fire Lab Behave source, plus Scott–Burgan **GR1 (101)**.
- Pinned Grade B Behave regression workflows for base ROS, wind/slope behavior, dynamic GR1, and off-axis directional surface spread.

### Added — testing, packaging, and engineering

- Python 3.11/3.12/3.13 CI matrix.
- Ruff lint/format quality gate, pytest, coverage, and pre-commit support.
- Dedicated optional GIS CI job with Rasterio.
- Real GeoTIFF integration tests covering output round trips, file-based simulation workflow, and CLI validate/run behavior.
- Package CI gate that builds wheel + sdist, clean-installs the built wheel, exercises `pyfireca --help`, clean-installs the built wheel with the `[gis]` extra, and runs the installed GIS wheel end to end.
- Distribution audit that verifies `License-Expression: MIT`, the packaged wheel license file, and the sdist `LICENSE` file.
- MIT license at the repository root with copyright `2026 Jinghao Hu`.
- PEP 639 package metadata with `license = "MIT"`, `license-files = ["LICENSE"]`, and a minimum Hatchling version of 1.27.
- English and Chinese README files plus living design, development, validation, status, handoff, roadmap, session-log, and research-deferment documents.

### Changed

- Project priority is now **baseline simulator freeze before new PyFireCA-specific CA innovations**. Lattice/interface/neighborhood research ideas remain documented in `docs/FUTURE_RESEARCH.md` but are not default implementation work.
- The official operational Rothermel reference line is explicitly **Albini-adjusted Rothermel**, not an unlabelled mixture of Rothermel 1972 and later corrections.
- Static physical propagation consumes direction-specific neighbor ROS rather than assigning maximum/head ROS to every neighbor.
- Off-axis arrival propagation uses the pinned Behave/Catchpole `FromIgnitionPoint` ellipse path rather than cosine projection or `FromPerimeter` rates.
- The first heterogeneous physical baseline explicitly uses **source-cell-controlled outgoing ROS**. Interface averaging/resistance remains a named future research variant.
- Physical arrival propagation is restricted to immediate-neighbor edges so larger neighborhoods cannot silently skip intermediate barriers.
- Static raster geometry fails closed on rotated, sheared, non-square, or cell-size-mismatched grids.
- Static input units are strict; percentage moisture, percent slope, 10-m/20-ft wind, radians, or misaligned rasters are not silently converted.
- Zero-wind/zero-slope Rothermel results return `spread_direction_deg=None` instead of inventing a head direction.
- Fireline intensity and flame length remain unset in the validated baseline output until separately validated.
- Run-level metrics now have one canonical location at the run root rather than a duplicate copy under `outputs/`.
- English and Chinese README files now describe the real end-to-end simulator instead of the older architecture-only bootstrap state.

### Scientific/design decisions retained

- Product scope is wildfire CA, not a generic urban/geospatial CA engine.
- NumPy remains the readable scientific reference implementation; optimization follows profiling.
- Fire behavior, propagation, GIS I/O, configuration, and experiment/research variants remain separate responsibilities.
- One synchronous CA step has no hidden physical duration.
- Dynamic weather will require an explicitly designed time-dependent scheduler rather than mutating the static Dijkstra/provider path.
- External scientific reference values carry evidence grades and pinned provenance.
- GPU/Torch/JAX/differentiable CA, WRF coupling, FBP, crown fire, spotting, suppression, Monte Carlo, and new PyFireCA-specific CA methods remain beyond the first static baseline release gate.
