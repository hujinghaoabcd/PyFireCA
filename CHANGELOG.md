# Changelog

All notable changes to PyFireCA will be documented in this file.

The project follows a pre-1.0 semantic-versioning workflow. During early development, API changes are allowed but should be documented when they affect users, experiments, or scientific interpretation.

## [Unreleased]

### Added

- Initial English and Chinese project README files.
- Modern `pyproject.toml` using a `src/` layout and Hatchling build backend.
- Living design, development, status, validation, handoff, behavior/data, and Rothermel reference documentation.
- Explicit wildfire `FireState` model and state-array validation.
- Moore and Von Neumann neighborhood implementations.
- Boundary-safe raster neighbor indexing with clipped-boundary semantics.
- Minimal `RasterGrid` state container.
- Synchronous `TransitionRule` protocol.
- Minimal synchronous `Simulation` engine with explicit NumPy RNG support.
- Deterministic `NeighborIgnitionRule` architectural baseline.
- Common generic `FireBehaviorModel[InputT]` protocol.
- Immutable `FireBehaviorResult` with explicit spread-rate, direction, intensity, and flame-length units/conventions.
- `SpatialLayer` for static `(Y, X)` and dynamic `(T, Y, X)` numerical environmental data.
- `EnvironmentalData` with shared spatial/time alignment validation and snapshot access.
- Rothermel six-class `FuelClass` ordering.
- SI-unit `RothermelFuelModel` with burnability and loaded-class physical-property validation.
- `RothermelFuelMoisture` with explicit dry-mass-fraction inputs and six-class expansion.
- `RothermelInputs` with midflame wind, meteorological wind-from direction, slope, and aspect conventions.
- Dedicated Rothermel input-contract tests and `docs/ROTHERMEL_REFERENCE.md` implementation/validation plan.
- GitHub Actions CI configuration covering quality checks and Python 3.11/3.12/3.13.

### Design decisions

- Product scope is wildfire CA rather than generic urban/geospatial CA.
- NumPy is the reference implementation; optimization is deferred until profiling.
- Fire-behavior equations remain separate from CA propagation rules.
- Behavior-model outputs are standardized while model-native inputs remain strongly typed and model-specific.
- Common behavior quantities crossing the CA boundary use explicit SI-derived units.
- Environmental data remain array-first; physical time interpolation and xarray/Zarr abstractions are deferred until required.
- Rothermel is the first behavior reference implementation; FBP remains planned for Cell2Fire-oriented comparison work.
- The Rothermel public fuel contract uses a stable six-class representation before equation/catalogue implementation.
- Rothermel receives midflame wind explicitly; canopy/exposure wind-adjustment logic is kept outside the core model input.
- PyTorch/JAX/differentiable CA remain outside the current development scope.
