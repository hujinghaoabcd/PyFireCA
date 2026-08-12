# Changelog

All notable changes to PyFireCA will be documented in this file.

The project follows a pre-1.0 semantic-versioning workflow. During early development, API changes are allowed but should be documented when they affect users, experiments, or scientific interpretation.

## [Unreleased]

### Added

- Initial English and Chinese project README files.
- Modern `pyproject.toml` using a `src/` layout and Hatchling build backend.
- Living design, development, status, validation, and handoff documentation.
- Explicit wildfire `FireState` model and state-array validation.
- Moore and Von Neumann neighborhood implementations.
- Boundary-safe raster neighbor indexing with initial clipped-boundary semantics.
- Minimal `RasterGrid` state container.
- Synchronous `TransitionRule` protocol.
- Minimal synchronous `Simulation` engine with explicit NumPy RNG support.
- Initial unit tests and GitHub Actions CI configuration.

### Design decisions

- Product scope is wildfire CA rather than generic urban/geospatial CA.
- NumPy is the reference implementation; optimization is deferred until profiling.
- Fire-behavior equations will remain separate from CA propagation rules.
- PyTorch/JAX/differentiable CA are outside the current development scope.
