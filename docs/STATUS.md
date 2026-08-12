# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **D — Validated Rothermel reference implementation (R1 complete / R2 validation-fixture gate)**

## Current position

PyFireCA now has a tested CA reference core, common behavior/data contracts, typed Rothermel inputs, independently testable R1 calculations, an explicitly selected Albini-adjusted R2 formulation, and a formal validation-evidence hierarchy.

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
R2: Albini-adjusted no-wind/no-slope ROS
      ↓
validation-fixture gate   ← current bottleneck
      ↓
FireBehaviorResult
      ↓
future behavior-informed CA rule
```

The complete Rothermel ROS equation chain is **not** implemented yet. This remains deliberate: the project will not manufacture a numerical truth value merely to begin coding R2.

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

### R1 — unit conversions and base heterogeneous-fuel quantities

Implemented and tested:

```text
m ↔ ft
kg/m² ↔ lb/ft²
kg/m³ ↔ lb/ft³
1/m ↔ 1/ft
J/kg ↔ Btu/lb
m/s ↔ ft/min
```

Scientific R1 functions:

- `compute_surface_area_weights()`;
- `compute_characteristic_sav_m_inv()`;
- `compute_packing_ratio()`;
- `compute_bulk_density_kg_m3()`;
- `compute_optimum_packing_ratio()`.

A hand-computable synthetic fuel fixture verifies exact expected weights/derived quantities independently of another software package.

### R2 reference variant

The reference line is explicitly named **Albini-adjusted Rothermel**.

Albini 1976 changes currently locked into the design include:

1. combustible loading uses `W0 * (1 - S_T)` rather than `W0 / (1 + S_T)`;
2. reaction-velocity exponent uses `A = 133 * sigma^-0.7913`;
3. live moisture of extinction uses revised exponentially weighted fine-fuel quantities and is bounded below by dead moisture of extinction;
4. dead and live reaction intensities are added rather than combined by the earlier final category surface-area weighted average.

Andrews 2018 is the modern consolidated consistency reference for this Albini-adjusted line.

### Validation evidence hierarchy

`docs/VALIDATION.md` now grades externally sourced values:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal synthetic/analytical fixture
```

When references conflict, equation variant / units / conventions must be resolved before tolerances are changed.

### Pinned Grade A fixtures

Added:

```text
tests/validation/data/albini1976_worked_examples.csv
```

From Albini 1976, GTR INT-30:

- Example 1: fuel model 3, fuel moisture 5%, 20-ft wind 8 mi/h, level ground → `97 chains/hour`, flame length `12.5 ft`;
- Example 2: fuel model 2, fine dead moisture 8%, live foliage about 50%, calm wind, 70% slope → `34 chains/hour`, flame length `6.2 ft`.

These are strong future R3/R4 whole-model checks, but neither has both wind and slope equal to zero.

### Pinned Grade B fixture

Added:

```text
tests/validation/data/behave7_surface_reference.csv
```

Pinned upstream:

```text
repository: firelab/behave-app
commit: a3cfcd5903188d73445948af16644868225bb9d5
source: behave-lib/test/csv/surface.csv
source blob: 975000d8dc3def0f25a22df0777e4ab70016c996
validator: behave-lib/test/cpp/testSurface.cpp
```

The official test retrieves spread rate in `ChainsPerHour` and compares expected values with `1e-6` tolerance.

Both external snapshots have SHA-based fixture-integrity tests so accidental edits are detected.

### Current R2 validation gap

No precise tabulated **zero-wind AND zero-slope** worked result matching the selected Albini-adjusted reference line has yet been found.

- Albini Example 1: level ground, but nonzero wind;
- Albini Example 2: calm wind, but nonzero slope;
- Rothermel 1972 includes zero-wind theory/graphical curves, but graph reading is not precise enough for a high-accuracy numeric regression fixture;
- current official Behave 7 surface CSV provides whole-model cases but not the dedicated R2 case.

This is intentionally recorded as a validation gap rather than filled with an internally computed value labeled as external truth.

## CI state

The established R1 code baseline is fully green across Ruff, quality pytest, and Python 3.11/3.12/3.13.

The new validation-fixture commits are running through the same CI. The first Grade A fixture-document commit completed successfully; the latest fixture-integrity-test run had Ruff lint/format already passing and Python 3.13 green at the last check, with remaining jobs still completing.

## Key decisions now implemented

1. CA propagation and fire behavior remain separate.
2. Behavior outputs are standardized; model-native inputs remain model-specific.
3. Public behavior/Rothermel contracts use explicit SI-derived units.
4. Environmental data remain array-first and lightweight.
5. Physical time interpolation remains deferred.
6. NoData is not silently imputed.
7. NumPy remains the readable scientific reference path.
8. Rothermel is implemented first; FBP follows for Cell2Fire-oriented comparison.
9. Six fuel classes are fixed before catalogue/equation implementation.
10. Rothermel receives midflame wind explicitly; wind adjustment is external.
11. Legacy-unit conversion is centralized and tested.
12. R1 base quantities remain separate from R2 reaction/heat-transfer equations.
13. R2 follows the named Albini-adjusted Rothermel line.
14. External validation values carry explicit evidence grades and pinned provenance.
15. A missing Grade A/B R2 value is reported as a gap, not silently synthesized.

## Not implemented yet

### Immediate scientific work

- dedicated R2 zero-wind/zero-slope external fixture;
- combustible/net fuel loading function;
- mineral and moisture damping;
- revised live moisture of extinction;
- Albini-adjusted reaction-velocity exponent;
- reaction velocity/intensity;
- propagating flux ratio;
- effective heating number / heat of preignition;
- heat source/sink;
- no-wind/no-slope ROS;
- wind/slope effects;
- real `FireBehaviorResult` from a complete Rothermel calculation.

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

Continue R2 validation before formula assembly:

```text
search/construct pinned external zero-wind+zero-slope reference
        ↓
record exact provenance and evidence grade
        ↓
implement small Albini-adjusted formula functions
        ↓
validated no-wind/no-slope ROS
```

If no suitable Grade A worked value exists, the fallback may be a **Grade B** zero-wind/zero-slope case generated by a pinned official Behave 7 build, but it must remain labeled Grade B and must not be presented as a primary-literature worked value.
