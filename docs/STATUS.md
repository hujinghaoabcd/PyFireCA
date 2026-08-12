# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **C — Wildfire data and behavior boundary**

## Current position

PyFireCA now has two stable layers:

```text
Milestone B
CA reference core

RasterGrid + FireState + Neighborhood + TransitionRule
                         ↓
                     Simulation

Milestone C
Behavior/data boundary

EnvironmentalData
      ↓
model-specific behavior inputs
      ↓
FireBehaviorModel
      ↓
FireBehaviorResult
      ↓
future behavior-informed CA rule
```

The project still intentionally avoids complete Rothermel/FBP equations at this point. The current goal is to make the contracts around those models explicit before scientific formulas are added.

## Completed

### Repository / engineering

- modern `src/` package layout;
- `pyproject.toml` with Python 3.11+, Hatchling, NumPy, optional GIS/dev dependencies;
- Ruff lint/format, pre-commit, pytest, coverage;
- GitHub Actions CI for Python 3.11, 3.12, and 3.13;
- English and Chinese README with runnable reference CA example;
- `CITATION.cff`, `CHANGELOG.md`, `CONTRIBUTING.md`;
- living design/development/status/handoff/validation documentation.

### CA reference core

- `FireState` enum and array validation;
- `RasterGrid` state/shape contract;
- `Neighborhood` protocol;
- Moore and Von Neumann neighborhoods;
- clipped-boundary neighbor lookup;
- synchronous `TransitionRule` contract;
- explicit RNG through `numpy.random.Generator`;
- `Simulation.step()` / `run()`;
- deterministic `NeighborIgnitionRule` reference baseline;
- explicit test that synchronous updates do not cascade within a single step.

### Fire-behavior boundary

Implemented in `src/pyfireca/behavior/`:

- generic `FireBehaviorModel[InputT]` protocol;
- immutable `FireBehaviorResult`;
- required common `spread_rate_m_s`;
- optional `spread_direction_deg`;
- optional `fireline_intensity_w_m`;
- optional `flame_length_m`;
- optional model-specific scalar diagnostics;
- finite/non-negative validation where scientifically appropriate;
- direction convention fixed to degrees clockwise from geographic north in `[0, 360)`.

Important design decision: Rothermel and FBP are **not** forced to share one oversized input dataclass. Each model may define its own strongly typed inputs while returning the same CA-facing `FireBehaviorResult`.

### Environmental data boundary

Implemented in `src/pyfireca/data.py`:

- `SpatialLayer` for static `(Y, X)` arrays;
- `SpatialLayer` for dynamic `(T, Y, X)` arrays;
- optional `units` metadata;
- optional `nodata` metadata;
- uniform `at(time_index)` access;
- `EnvironmentalData` named layer collection;
- shared spatial-shape validation;
- shared dynamic time-length validation;
- aligned `snapshot(time_index)` output.

The initial temporal contract uses integer time indices only. Physical datetimes/interpolation are intentionally deferred until a concrete weather-data integration is implemented.

### Documentation added in Milestone C

- `docs/BEHAVIOR_DATA_CONTRACT.md` — exact behavior/data interface, unit policy, direction convention, NoData policy, temporal design, and deferred items;
- `docs/DESIGN.md` updated with decisions D007/D008;
- `docs/DEVELOPMENT.md` updated to reflect Milestone C progress.

### Tests / CI

New tests cover:

- valid/invalid `FireBehaviorResult` values;
- model-specific input compatibility through a dummy behavior implementation;
- static/dynamic `SpatialLayer` behavior;
- invalid layer dimensions/dtypes;
- environmental spatial alignment;
- dynamic time-length alignment;
- missing layer errors;
- static + dynamic snapshot behavior.

After Ruff-driven style corrections, the latest quality job passes lint, format checking, and tests. Python 3.12/3.13 jobs are green; Python 3.11 tests also passed and the workflow was completing its final cleanup at the last check.

## Key decisions now implemented

1. **CA propagation and fire behavior stay separate.**
2. **Behavior outputs are standardized; model-native inputs are not artificially unified.**
3. **Common behavior quantities use explicit SI-derived units in field names.**
4. **Common spread direction is clockwise from geographic north.**
5. **Environmental data remain array-first and lightweight.**
6. **Static `(Y, X)` and dynamic `(T, Y, X)` data share one access pattern.**
7. **Physical time interpolation is deferred rather than guessed.**
8. **NoData is metadata only at this stage; the numerical kernel does not silently impute missing data.**
9. **NumPy remains the scientific reference path.**

## Not implemented yet

### Milestone C remaining work

- first real model-specific behavior input dataclass;
- initial fuel representation;
- first scientifically validated fire-behavior implementation;
- GIS CRS / transform / extent alignment validation;
- optional Rasterio read/write adapter;
- explicit mapping from GIS NoData to wildfire/unburnable state;
- physical weather time-coordinate policy.

### CA research extensions

- probabilistic rule;
- directional/adaptive neighborhoods;
- asynchronous/event-driven scheduler;
- sparse/active-cell update representation;
- distance accumulation / Cell2Fire-like rule.

### Wildfire processes

- validated Rothermel implementation;
- validated FBP implementation;
- arrival time;
- crown fire;
- spotting;
- suppression;
- Monte Carlo experiment layer.

### Scientific validation

- independent Rothermel/FBP reference calculations;
- Cell2Fire controlled comparison scenarios;
- grid-size/time-step sensitivity;
- directional/lattice-bias experiments.

## Scope boundaries that remain fixed

- PyFireCA is wildfire-specific, not an urban CA product.
- UrbanVCA / PLUS / intPLUS / Mesa-Geo remain engineering references only.
- PyTorchFire-style differentiable CA remains deferred.
- Level Set / front tracking remain comparison methods, not core engines.
- GIS file I/O stays outside numerical CA kernels.
- Do not introduce plugin/backend/platform abstractions without a concrete requirement.

## Immediate next target

The next implementation target is to select and formalize the **first real behavior-model input contract and fuel representation** before adding a full equation set.

Recommended order:

```text
1. choose first reference behavior family
2. define its typed input dataclass
3. define fuel-model representation needed by that family
4. document source variables + units
5. add validation/reference fixtures
6. then implement equations
```

For a Cell2Fire-oriented research line, FBP is strategically important; for a simpler independent surface-fire reference path, Rothermel is also useful. The choice should be made based on which reference calculations can be validated most rigorously first, not on implementation convenience alone.
