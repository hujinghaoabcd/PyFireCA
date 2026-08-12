# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **D — Validated Rothermel reference implementation (R1 complete / R2 gated)**

## Current position

PyFireCA now has a tested CA reference core, common behavior/data contracts, typed Rothermel inputs, and the first independently testable Rothermel base calculations.

```text
RasterGrid + FireState + Neighborhood + TransitionRule
                         ↓
                     Simulation

EnvironmentalData
      ↓
RothermelInputs
      ↓
R1: units + fuel weighting/base quantities
      ↓
R2: no-wind/no-slope ROS   ← next scientific gate
      ↓
FireBehaviorResult
      ↓
future behavior-informed CA rule
```

The complete Rothermel ROS equation chain is **not** implemented yet. R1 is intentionally separated from R2 so unit/weighting errors can be distinguished from differences among Rothermel/Albini/Andrews equation variants.

## Completed

### Repository / engineering

- modern `src/` package layout;
- Python 3.11+ / Hatchling / NumPy core;
- Ruff lint and format, pre-commit, pytest, coverage;
- GitHub Actions matrix for Python 3.11, 3.12, and 3.13;
- English/Chinese README with runnable CA example;
- `CITATION.cff`, `CHANGELOG.md`, `CONTRIBUTING.md`;
- living design, development, validation, status, handoff, behavior/data, and Rothermel reference documentation.

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

- stable six-class ordering: dead 1-h, dead 10-h, dead 100-h, dead herbaceous, live herbaceous, live woody;
- `RothermelFuelModel` with SI-unit fields and burnability/property validation;
- `RothermelFuelMoisture` with five external moisture inputs and six-class expansion;
- `RothermelInputs` with midflame wind, meteorological wind-from direction, slope, and aspect;
- 10-m/20-ft wind adjustment kept outside the core Rothermel input contract.

Rothermel remains the first reference implementation; FBP is planned later for Cell2Fire-oriented experiments.

### R1 — exact unit conversion layer

Added `src/pyfireca/behavior/_units.py` with centralized conversions for:

```text
m ↔ ft
kg/m² ↔ lb/ft²
kg/m³ ↔ lb/ft³
1/m ↔ 1/ft
J/kg ↔ Btu/lb
m/s ↔ ft/min
```

The conversions are round-trip tested. Published/legacy-unit constants are no longer intended to be scattered through scientific equation functions.

### R1 — base heterogeneous-fuel quantities

Implemented small pure functions in `rothermel.py`:

- `compute_surface_area_weights()`;
- `compute_characteristic_sav_m_inv()`;
- `compute_packing_ratio()`;
- `compute_bulk_density_kg_m3()`;
- `compute_optimum_packing_ratio()`.

The weighting implementation follows the heterogeneous-fuel structure in which per-class relative surface area is proportional to SAV × oven-dry load / particle density, followed by within-dead/live and between-category weighting.

A hand-computable synthetic fuel fixture verifies exact expected values instead of taking another software package as truth.

### Tests / CI

R1 tests cover:

- exact conversion constants and round trips;
- surface-area weights within dead/live categories;
- dead/live category weights;
- characteristic SAV;
- packing ratio;
- oven-dry bulk density;
- optimum packing ratio;
- zero derived quantities for a nonburnable fuel model;
- negative-input rejection.

The R1 scientific tests pass on Python 3.11, 3.12, and 3.13. During this implementation pass, CI failures encountered were Ruff-only style issues in test assertions; the flagged assertions have been corrected and the latest CI is being re-verified after that style fix.

## Key decisions now implemented

1. CA propagation and fire behavior remain separate.
2. Behavior outputs are standardized; model-native inputs remain model-specific.
3. Public behavior/Rothermel contracts use explicit SI-derived units.
4. Environmental data remain array-first and lightweight.
5. Physical time interpolation remains deferred.
6. NoData is not silently imputed.
7. NumPy remains the readable scientific reference path.
8. Rothermel is implemented first for reference/validation; FBP follows for Cell2Fire-oriented comparison.
9. Six fuel classes are fixed before catalogue/equation implementation.
10. Rothermel receives midflame wind explicitly; wind adjustment is external.
11. Legacy-unit conversion is centralized and tested rather than embedded repeatedly in formulas.
12. R1 fuel weighting/base quantities are separate from R2 reaction/heat-transfer equations.

## R2 scientific decision gate

Before implementing no-wind/no-slope ROS, the project must explicitly reconcile the selected reference formulation across:

- original Rothermel 1972 equations;
- Albini 1976 corrections used by later operational implementations;
- Andrews 2018's consolidated explanation;
- live moisture-of-extinction treatment;
- dynamic herbaceous curing boundaries;
- net-fuel-loading convention.

Do not silently combine formulas from different vintages simply because an existing package does so.

## Not implemented yet

### Immediate scientific work

- authoritative numeric R2 reference fixtures;
- selected/documented Albini/Andrews correction set;
- mineral and moisture damping;
- net fuel loading;
- reaction velocity/intensity;
- propagating flux ratio;
- effective heating number / heat of preignition;
- heat source/sink;
- no-wind/no-slope ROS;
- wind/slope effects;
- real `FireBehaviorResult` output from a complete Rothermel calculation.

### GIS/data work

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
- FBP;
- Cell2Fire-like distance accumulation;
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

The next task is **R2 preparation**, not Cell2Fire propagation yet:

```text
primary-source reconciliation
        ↓
freeze named R2 equation/correction set
        ↓
authoritative numeric fixtures
        ↓
small formula-level functions
        ↓
validated no-wind/no-slope ROS
```

Only after one independently validated ROS path exists should PyFireCA build its first physically informed CA rule.
