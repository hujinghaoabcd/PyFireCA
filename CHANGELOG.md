# Changelog

All notable changes to PyFireCA will be documented in this file.

The project follows a pre-1.0 semantic-versioning workflow. During early development, API changes are allowed but should be documented when they affect users, experiments, or scientific interpretation.

## [Unreleased]

### Added

- Initial English and Chinese project README files.
- Modern `pyproject.toml` using a `src/` layout and Hatchling build backend.
- Living design, development, status, validation, handoff, and behavior/data contract documentation.
- Explicit wildfire `FireState` model and state-array validation.
- Moore and Von Neumann neighborhood implementations.
- Boundary-safe raster neighbor indexing with initial clipped-boundary semantics.
- Minimal `RasterGrid` state container.
- Synchronous `TransitionRule` protocol.
- Minimal synchronous `Simulation` engine with explicit NumPy RNG support.
- Deterministic `NeighborIgnitionRule` architectural baseline.
- Common generic `FireBehaviorModel[InputT]` protocol.
- Immutable `FireBehaviorResult` with explicit spread-rate, direction, intensity, and flame-length units/conventions.
- `SpatialLayer` for static `(Y, X)` and dynamic `(T, Y, X)` numerical environmental data.
- `EnvironmentalData` with shared spatial/time alignment validation and snapshot access.
- Unit tests for CA semantics, behavior-result validation, and static/dynamic environmental data contracts.
- GitHub Actions CI configuration covering quality checks and Python 3.11/3.12/3.13.

### Design decisions

- Product scope is wildfire CA rather than generic urban/geospatial CA.
- NumPy is the reference implementation; optimization is deferred until profiling.
- Fire-behavior equations remain separate from CA propagation rules.
- Behavior-model outputs are standardized while model-native inputs remain strongly typed and model-specific.
- Common behavior quantities crossing the CA boundary use explicit SI-derived units.
- Environmental data remain array-first; physical time interpolation and xarray/Zarr abstractions are deferred until required.
- PyTorch/JAX/differentiable CA are outside the current development scope.
