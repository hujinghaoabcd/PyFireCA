# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **C — Wildfire data and behavior boundary**

## Current position

PyFireCA now has a tested CA reference core, a common fire-behavior/data boundary, and the first real behavior-family input contract.

```text
RasterGrid + FireState + Neighborhood + TransitionRule
                         ↓
                     Simulation

EnvironmentalData
      ↓
RothermelInputs
      ↓
future Rothermel reference implementation
      ↓
FireBehaviorResult
      ↓
future behavior-informed CA rule
```

The Rothermel scientific equation chain has **not** been implemented yet. This is intentional: the input/fuel/unit conventions are being stabilized and tested first.

## Completed

### Repository / engineering

- modern `src/` package layout;
- Python 3.11+ / Hatchling / NumPy core;
- Ruff lint and format, pre-commit, pytest, coverage;
- GitHub Actions matrix for Python 3.11, 3.12, and 3.13;
- English/Chinese README with runnable CA example;
- `CITATION.cff`, `CHANGELOG.md`, `CONTRIBUTING.md`;
- living design, development, validation, status, and handoff documentation.

### CA reference core

- `FireState` and state-array validation;
- `RasterGrid`;
- replaceable `Neighborhood` protocol;
- Moore and Von Neumann neighborhoods;
- clipped boundary semantics;
- synchronous `TransitionRule` protocol;
- explicit `numpy.random.Generator`;
- `Simulation.step()` / `run()`;
- deterministic `NeighborIgnitionRule` baseline;
- no-cascade synchronous-update regression test.

### Common fire-behavior/data boundary

- generic `FireBehaviorModel[InputT]` protocol;
- immutable `FireBehaviorResult`;
- common SI-derived output fields for spread rate, direction, fireline intensity, and flame length;
- direction convention: clockwise from geographic north;
- `SpatialLayer` for `(Y, X)` and `(T, Y, X)` data;
- `EnvironmentalData` with spatial/time-length alignment validation;
- integer-index dynamic snapshots;
- explicit units/NoData metadata without hidden conversion or imputation.

### Rothermel input/fuel contract

Implemented in `src/pyfireca/behavior/rothermel.py`:

- fixed six-class fuel ordering:
  - `DEAD_1H`;
  - `DEAD_10H`;
  - `DEAD_100H`;
  - `DEAD_HERBACEOUS`;
  - `LIVE_HERBACEOUS`;
  - `LIVE_WOODY`;
- `RothermelFuelModel` with explicit SI-unit fields;
- burnable/nonburnable validation;
- per-loaded-class SAV/heat-content/particle-density validation;
- `RothermelFuelMoisture` with five external moisture inputs;
- six-class moisture expansion with dead-herbaceous moisture initially following dead 1-h moisture;
- live fuel moisture values above 1.0 allowed on a dry-mass basis;
- `RothermelInputs` with:
  - midflame wind speed;
  - explicit meteorological `wind_from_direction_deg`;
  - slope;
  - aspect;
- 10-m/20-ft to midflame wind adjustment intentionally kept outside the core Rothermel input contract.

The first behavior implementation is therefore sequenced as **Rothermel reference first**, while FBP remains planned for later Cell2Fire-oriented work. This is a development-order decision rather than a product-level preference.

### Rothermel documentation

Added `docs/ROTHERMEL_REFERENCE.md`, which records:

- primary scientific references;
- six-class fuel ordering;
- SI public-unit policy;
- moisture conventions;
- wind/slope/aspect conventions;
- independent-implementation/license rule;
- staged implementation plan R1–R6;
- validation strategy against authoritative references plus independent software implementations.

### Tests / CI

New Rothermel contract tests cover:

- stable six-class ordering;
- valid burnable fuel models;
- invalid depth/extinction/load conditions;
- loaded-class physical-property requirements;
- nonburnable zero-valued fuel models;
- six-value tuple length/fraction validation;
- moisture expansion and live moisture > 1.0;
- wind/slope/direction input validation.

Latest CI run for the formatted Rothermel contract is fully green across quality checks and Python 3.11/3.12/3.13.

## Key decisions now implemented

1. CA propagation and fire behavior remain separate.
2. Behavior outputs are standardized; model-native inputs remain model-specific.
3. Public behavior/Rothermel contracts use explicit SI-derived units.
4. Environmental data remain array-first and lightweight.
5. Physical time interpolation remains deferred.
6. NoData is not silently imputed.
7. NumPy remains the readable scientific reference path.
8. Rothermel is implemented first for reference/validation; FBP follows for Cell2Fire-oriented comparison.
9. The six-class fuel representation is fixed before equation implementation so later Scott--Burgan-style dynamic fuels do not require a public-API redesign.
10. Wind input to Rothermel is explicitly midflame wind; wind-adjustment-factor logic belongs outside the core equation contract.

## Not implemented yet

### Immediate scientific work

- Rothermel legacy/native-unit conversion helpers and tests;
- R1 base fuel quantities;
- R2 no-wind/no-slope ROS;
- authoritative numeric reference fixtures;
- complete Rothermel wind/slope effects;
- conversion to `FireBehaviorResult` from a real model calculation.

### Milestone C GIS/data work

- CRS/transform/extent alignment validation;
- optional Rasterio read/write adapter;
- GIS NoData-to-unburnable policy;
- physical weather timestamps/interpolation.

### Later CA research

- first behavior-informed CA transition rule;
- probabilistic rules;
- directional/adaptive neighborhoods;
- asynchronous/event-driven scheduling;
- active/sparse updates;
- Cell2Fire-like distance accumulation;
- FBP;
- arrival time;
- crown fire / spotting / suppression;
- Monte Carlo experiment layer;
- profiling-led Numba optimization.

## Scope boundaries that remain fixed

- wildfire CA product, not urban CA product;
- urban CA projects remain engineering/GIS references only;
- PyTorchFire/differentiable CA deferred;
- Level Set/front tracking are comparison methods only;
- GIS file I/O stays outside numerical kernels;
- no plugin/backend/platform architecture without demonstrated need.

## Immediate next target

Continue the Rothermel reference implementation in small validated stages:

```text
R1  explicit unit conversions + base fuel quantities
 ↓
R2  no-wind / no-slope surface ROS
 ↓
R3  wind + slope effects
 ↓
R4  FireBehaviorResult
 ↓
R5  independently verified standard fuel catalogues
 ↓
R6  behavior-informed CA integration
```

Do not begin Cell2Fire-like distance accumulation until at least one fire-behavior path can produce independently validated ROS values.
