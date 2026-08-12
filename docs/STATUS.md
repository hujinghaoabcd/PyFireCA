# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **B — Minimal CA reference core**

## Current position

The repository foundation is now established and PyFireCA has a working minimal synchronous cellular automaton. The project has moved from pure scaffold work into the first executable CA milestone.

Current architecture:

```text
RasterGrid
   +
FireState
   +
Neighborhood
   +
TransitionRule
   ↓
Simulation
```

The first reference rule is intentionally simple and deterministic. It exists to validate the CA architecture before Rothermel/FBP fire-behavior equations are introduced.

## Completed

### Repository / engineering

- Repository `hujinghaoabcd/PyFireCA` initialized.
- English and Chinese README files created and updated with a runnable CA workflow.
- `src/` package layout established.
- `pyproject.toml` created with Python 3.11+, Hatchling, NumPy, optional GIS/dev dependencies, Ruff and pytest configuration.
- `.gitignore` and pre-commit configuration added.
- GitHub Actions CI added.
- CI test matrix covers Python 3.11, 3.12, and 3.13.
- `CITATION.cff`, `CHANGELOG.md`, and `CONTRIBUTING.md` added.
- Detailed design, development, validation, status, and handoff documents created.

### CA core

- `FireState` enum:
  - `UNBURNABLE`;
  - `UNBURNED`;
  - `BURNING`;
  - `BURNED`.
- state-array validation implemented;
- `RasterGrid` implemented with shape/state validation and independent copying;
- `Neighborhood` protocol established;
- `MooreNeighborhood` implemented;
- `VonNeumannNeighborhood` implemented;
- clipped raster boundary semantics implemented for neighbor lookup;
- synchronous `TransitionRule` protocol established;
- synchronous `Simulation.step()` / `run()` implemented;
- explicit `numpy.random.Generator` construction through `Simulation.from_seed()`;
- `NeighborIgnitionRule` implemented as a transparent deterministic wildfire CA baseline;
- runnable `examples/minimal.py` added.

### Tests

Current test coverage includes:

- state codes and validation;
- Moore/Von Neumann neighborhood invariants;
- boundary clipping;
- grid shape/copy/replace-state behavior;
- simulation state replacement and invalid rule output;
- deterministic Moore/Von Neumann ignition behavior;
- unburnable-cell preservation;
- explicit test that synchronous updates do not cascade within one time step.

The Python 3.11/3.12/3.13 test jobs have passed in CI. Initial quality-job failures were formatting-only issues caught by Ruff and were corrected. The latest documentation-only CI run is being used as the final bootstrap verification.

## Key decisions now implemented

1. **Synchronous update semantics are explicit.** A rule computes a complete next-state array from the current grid, then `Simulation` applies it.
2. **Current boundary policy is clipping.** Off-grid neighbors are omitted. Periodic/padded policies are deferred.
3. **Neighborhood is replaceable independently of the simulation loop.**
4. **The first reference rule contains no fire-behavior physics.** This keeps CA mechanics independently testable.
5. **NumPy remains the reference path.** No Numba optimization has been introduced yet.

## Not implemented yet

### CA research extensions

- probabilistic rule;
- radius/directional/adaptive neighborhood variants;
- asynchronous/event-driven scheduler;
- sparse/active-cell update representation;
- distance-accumulation / Cell2Fire-like rule.

### Wildfire science

- common fire-behavior result contract;
- fuel representation;
- Rothermel model;
- FBP model;
- moisture/environment coupling;
- arrival time;
- crown fire;
- spotting;
- suppression.

### GIS/data

- static/dynamic layer containers;
- Rasterio read/write adapter;
- raster alignment contract implementation;
- YAML run configuration;
- GeoTIFF outputs.

### Validation

- deterministic regression artifact beyond unit-scale cases;
- scientific fire-behavior reference cases;
- Cell2Fire comparison scenarios;
- grid/time-step/directional-bias experiments.

## Scope boundaries that remain fixed

- PyFireCA is a wildfire CA project, not an urban CA product.
- UrbanVCA/PLUS/intPLUS/Mesa-Geo remain engineering references only.
- PyTorchFire/differentiable CA is deferred.
- Level Set and front-tracking propagation are comparison methods, not core implementations.
- Fire behavior and CA transition mechanics must remain separate.
- GIS I/O must remain outside numerical CA kernels.
- Do not create plugin/backend/platform abstractions until a concrete need appears.

## Immediate next target

The next implementation target is **the wildfire data/behavior boundary**, not a complex spread model yet:

```text
FireBehaviorResult
      ↓
FireBehaviorModel protocol
      ↓
minimal environmental data contract
      ↓
reference behavior tests
```

Before implementing complete Rothermel/FBP equations, define units, return fields, and validation strategy so both models can plug into the same CA rule without special-case branches.
