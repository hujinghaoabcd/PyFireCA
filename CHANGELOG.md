# Changelog

All notable changes to PyFireCA will be documented in this file.

The project follows a pre-1.0 semantic-versioning workflow. During early development, API changes are allowed but should be documented when they affect users, experiments, or scientific interpretation.

## [Unreleased]

### Added

- Initial English and Chinese project README files.
- Modern `pyproject.toml` using a `src/` layout and Hatchling build backend.
- Living design, development, status, validation, handoff, behavior/data, GIS, Rothermel, and static-raster workflow documentation.
- Explicit wildfire `FireState` model and state-array validation.
- `build_initial_state()` for explicit domain-mask and ignition-mask to canonical CA state conversion.
- Moore and Von Neumann neighborhood implementations.
- Boundary-safe raster neighbor indexing with clipped-boundary semantics.
- Minimal `RasterGrid` state container.
- Synchronous `TransitionRule` protocol.
- Minimal synchronous `Simulation` engine with explicit NumPy RNG support.
- Deterministic `NeighborIgnitionRule` architectural baseline.
- Common generic `FireBehaviorModel[InputT]` protocol.
- Immutable `FireBehaviorResult` with explicit spread-rate, direction, intensity, and flame-length units/conventions.
- `SpatialLayer` for static `(Y, X)` and dynamic `(T, Y, X)` numerical environmental data.
- `EnvironmentalData` with shared spatial/time alignment validation and policy-free snapshot access.
- `MissingEnvironmentalDataError` and `EnvironmentalData.require_complete_snapshot()` for explicit fail-fast validation of required dynamic/static inputs without interpolation or domain mutation.
- Explicit `nodata_mask()` utility that uses only declared NoData metadata.
- `build_domain_mask()` for intentionally deriving a persistent simulation domain from selected static layers.
- `LandscapeInput` for one shared `RasterMetadata`, aligned environmental layers, and a validated initial CA state.
- Lightweight `RasterMetadata`, raster-alignment validation, and named multi-layer alignment checks.
- Optional Rasterio `read_raster()` / `write_raster()` adapters with dedicated GIS CI coverage.
- Canonical `write_state_raster()` output using `uint8` fire-state codes and no file-level NoData marker.
- Rothermel six-class `FuelClass` ordering.
- SI-unit `RothermelFuelModel` with burnability and loaded-class physical-property validation.
- `RothermelFuelMoisture` with explicit dry-mass-fraction inputs and six-class expansion.
- `RothermelInputs` with midflame wind, meteorological wind-from direction, slope, and aspect conventions.
- Central `behavior/_units.py` conversions between SI and the ft/lb/Btu/min units used by published Rothermel correlations, with round-trip tests.
- R1 heterogeneous surface-area weighting, characteristic SAV, packing ratio, bulk density, and optimum-packing calculations.
- Hand-computable R1 regression fixtures plus nonburnable/invalid-input tests.
- Albini-adjusted R2 pure functions for combustible loading, size-bin weighted loading, mineral/moisture damping, live moisture of extinction, reaction velocity/intensity, propagating flux, preignition heat, heat sink, and base ROS.
- `BaseSpreadResult` / `compute_base_spread_result()` for carrying validated R2 quantities into later wind/slope stages without recomputing the base chain.
- Pinned Grade B Behave 7 FM1 dead-only and FM2 static live-fuel base-ROS regressions.
- R3 slope-factor implementation with a pinned FM1 30% slope Behave regression.
- R3 wind-factor implementation with a pinned FM1 100 ft/min direct-midflame Behave regression.
- Effective-wind inversion and explicit optional operational wind-speed limiting.
- Non-collinear wind/slope vector composition in `_rothermel_vectors.py`.
- Explicit meteorological wind-from, downwind-push, downslope-aspect, upslope, and geographic-bearing conversion helpers in `_directions.py`.
- Dedicated pinned Behave 7 non-collinear wind/slope maximum-ROS workflow.
- Public `RothermelModel.compute(RothermelInputs) -> FireBehaviorResult` assembly, exported from `pyfireca.behavior`.
- Rothermel diagnostics carrying base ROS, reaction intensity, characteristic SAV, packing ratios, wind/slope factors, effective wind, dynamic transfer, and wind-limit state.
- Operational Scott–Burgan dynamic herbaceous curing/load-transfer stage with pinned Grade B GR1 validation.
- Audited standard-fuel catalogue API with pinned native-source records for FM1, FM2, and GR1.
- Physical edge-distance / directional-ROS travel-time helpers in `pyfireca.propagation`.
- `StaticArrivalTimeSolver` for static directional-edge earliest-arrival propagation.
- `arrival_times_to_state()` for mapping physical arrival fields to canonical fire states using explicit burn duration.
- North-up square-grid offset-to-geographic-bearing conversion.
- Behave-aligned surface-fire length-to-width ratio, eccentricity, backing/flanking ROS, and `FromIgnitionPoint` arbitrary-angle ROS in `_surface_ellipse.py`.
- Dedicated pinned R7 Behave workflow validating FM1 90° off-axis radial ROS at `5.2277130003983068 chains/h`.
- `HomogeneousRothermelDirectionalSpreadRate` for validated directional neighbor ROS from one static Rothermel state.
- `StaticSpatialRothermelDirectionalSpreadRate` for per-source-cell static heterogeneous behavior and cached ellipses.
- `RothermelRasterLayerNames` and `StaticRasterRothermelInputsProvider` for strict raster-layer-to-typed-Rothermel assembly.
- `build_static_raster_rothermel_arrival_solver()` as a thin `LandscapeInput` → static Rothermel arrival factory.
- `docs/STATIC_RASTER_WORKFLOW.md` documenting layer names, units, NoData/domain semantics, grid geometry, and explicit non-goals.
- `examples/static_raster_rothermel.py` demonstrating the in-memory raster → arrival → physical-time state workflow.
- Example smoke testing through `tests/test_examples.py` so public examples fail CI when APIs drift.
- Grade A Albini 1976 worked-example fixtures and pinned Grade B Behave 7 surface regression data with provenance/integrity checks.
- GitHub Actions CI configuration covering quality checks, optional GIS tests, and Python 3.11/3.12/3.13.

### Changed

- The official Behave reference workflow uses stable pinned regressions instead of the abandoned fragile custom C++ wind-limit probe.
- Wind-limit validation is separated into an official Behave ROS-at-boundary regression and Python tests for enable/threshold/capping semantics.
- When the optional wind limit is exceeded, `effective_wind_speed_m_s` now reports the limited effective wind so the surface ellipse uses the operationally capped wind state.
- Zero-wind/zero-slope `RothermelModel` results return `spread_direction_deg=None` rather than inventing a directional head-fire bearing.
- Rothermel fireline intensity and flame length remain unset in the common output until their output equations are separately validated.
- Static physical propagation now consumes direction-specific edge ROS instead of implicitly assigning maximum/head ROS to every neighbor.
- The public static raster workflow now fails closed on rotated, sheared, rectangular, or affine/cell-size-mismatched grids rather than approximating physical edge geometry.

### Design decisions

- Product scope is wildfire CA rather than generic urban/geospatial CA.
- NumPy is the reference implementation; optimization is deferred until profiling.
- Fire-behavior equations remain separate from CA propagation rules and event scheduling.
- Behavior-model outputs are standardized while model-native inputs remain strongly typed and model-specific.
- Common behavior quantities crossing the CA boundary use explicit SI-derived units.
- Environmental data remain array-first; physical time interpolation and xarray/Zarr abstractions are deferred until required.
- NoData remains metadata until a workflow explicitly selects static layers that define the persistent simulation domain.
- Dynamic weather/moisture NoData cannot silently create permanent `UNBURNABLE` cells.
- Required environmental snapshots use an explicit fail-fast completeness check; automatic interpolation/filling remains an external preprocessing decision.
- `LandscapeInput` owns one shared geospatial metadata object while evolving state remains in the propagation/simulation layer.
- State GeoTIFF output uses model state `UNBURNABLE=0` rather than conflating model state with file-level NoData.
- GIS preprocessing may transform inputs intentionally; CA simulation never silently reprojects/resamples/alters its grid.
- Rothermel is the first behavior reference implementation; FBP remains planned for later comparison work.
- The Rothermel public fuel contract uses a stable six-class representation.
- Rothermel receives midflame wind explicitly; canopy/exposure wind-adjustment logic is kept outside the core model input.
- Unit conversion and R1 weighting/base calculations are separated from the R2 reaction/heat-transfer chain.
- The R2 reference variant is explicitly **Albini-adjusted Rothermel** rather than an unlabelled mixture of original Rothermel 1972 and later operational corrections.
- Static heterogeneous R2 base ROS is independently validated against pinned official Behave 7 cases before wind/slope assembly.
- Non-collinear wind and slope are vector-combined; scalar `1 + phi_w + phi_s` is used only where effects are explicitly collinear.
- Meteorological wind-from direction is converted explicitly to a downwind fire-push direction before vector composition.
- The operational wind-speed limit is an explicit option and is disabled by default.
- Physical travel time is `distance / direction-specific ROS`; one synchronous CA step has no hidden physical duration.
- Off-axis arrival propagation uses the pinned Behave/Catchpole `FromIgnitionPoint` ellipse path, not a cosine projection and not `FromPerimeter` rates.
- The first heterogeneous edge baseline is **source-cell controlled outgoing ROS**; source/target averaging is reserved for explicit named research variants.
- Static raster input units are strict and never silently converted.
- NoData outside the simulation domain is permitted; required behavior NoData/non-finite values inside the domain fail fast.
- Static Dijkstra-style arrival and cached static providers are not mutated to imitate time-varying weather.
- External validation values carry evidence grades and pinned provenance.
- PyTorch/JAX/differentiable CA remain outside the current development scope.
