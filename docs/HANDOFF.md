# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: allow the next development session or contributor to continue immediately without reconstructing design context from chat history.

## 1. Project identity and protected scope

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. UrbanVCA / PLUS / intPLUS / Mesa-Geo are engineering/GIS references only; they are not supported simulation domains.

Primary research interest: **modify and study the CA itself**.

Protected CA extension points:

```text
State
Neighborhood
Transition Rule
Time stepping / scheduler
```

Fire behavior and GIS support the CA but do not define the simulation engine.

Do not casually reverse these decisions without updating `docs/DESIGN.md` and explaining the scientific/engineering reason:

1. wildfire-specific product scope;
2. NumPy is the readable scientific reference path;
3. Numba only after profiling;
4. PyTorch/JAX/GPU/differentiable CA deferred;
5. Level Set/front tracking are comparison methods only;
6. fire behavior and CA propagation stay separate;
7. GIS file I/O stays outside numerical kernels;
8. compact package tree until real complexity justifies splitting;
9. behavior outputs standardized, model-native inputs strongly typed/model-specific;
10. Rothermel first, FBP later for Cell2Fire-oriented comparison;
11. Rothermel public contract uses SI units and explicit midflame wind;
12. R1 base calculations stay separate from R2 reaction/heat-transfer equations;
13. R2 follows a named **Albini-adjusted Rothermel** line;
14. external numerical references carry explicit evidence grades and pinned provenance.

## 2. Current implemented tree

```text
src/pyfireca/
├── __init__.py
├── state.py
├── grid.py
├── neighborhood.py
├── rules.py
├── simulation.py
├── data.py
└── behavior/
    ├── __init__.py
    ├── base.py
    ├── _units.py
    └── rothermel.py
```

Core tests plus validation assets now include:

```text
tests/
├── test_behavior_base.py
├── test_behavior_units.py
├── test_data.py
├── test_grid.py
├── test_neighborhood.py
├── test_rothermel_inputs.py
├── test_rothermel_r1.py
├── test_rules.py
├── test_simulation.py
├── test_state.py
└── validation/
    ├── README.md
    ├── test_albini1976_fixture.py
    ├── test_behave7_fixture.py
    └── data/
        ├── albini1976_worked_examples.csv
        └── behave7_surface_reference.csv
```

Do not create empty `gis.py`, `config.py`, `metrics.py`, `fbp.py`, or plugin/backend packages merely to match an architecture diagram.

## 3. CA core truth

### State

```text
UNBURNABLE = 0
UNBURNED   = 1
BURNING    = 2
BURNED     = 3
```

### Grid / neighborhood

Implemented:

- `RasterGrid`;
- `Neighborhood` protocol;
- `MooreNeighborhood`;
- `VonNeumannNeighborhood`;
- `valid_neighbor_indices()`;
- clipped edge semantics.

### Transition semantics

`TransitionRule.next_state(grid, *, rng)` reads the current full state and returns a complete next-state array. `Simulation` applies it only after rule evaluation finishes.

The reference engine is therefore explicitly **synchronous**; newly ignited cells do not propagate again in the same step.

`NeighborIgnitionRule` is an architectural baseline only and contains no physical fire behavior.

## 4. Common behavior/data contract

`FireBehaviorResult` provides the stable CA-facing output:

```text
spread_rate_m_s            required
spread_direction_deg       optional, [0, 360), clockwise from north
fireline_intensity_w_m     optional
flame_length_m              optional
diagnostics                 optional model-specific scalar mapping
```

`FireBehaviorModel[InputT]` deliberately leaves the input type model-specific.

`SpatialLayer` supports:

```text
static   (Y, X)
dynamic  (T, Y, X)
```

with optional units/NoData metadata. `EnvironmentalData` requires shared spatial shape and dynamic time length. Physical datetime interpolation, CRS/affine metadata, masking, xarray, and Zarr remain deferred until concrete requirements arise.

## 5. Rothermel input contract

Fixed six-class order:

```text
0 DEAD_1H
1 DEAD_10H
2 DEAD_100H
3 DEAD_HERBACEOUS
4 LIVE_HERBACEOUS
5 LIVE_WOODY
```

`RothermelFuelModel` SI fields:

```text
code
depth_m
dead_moisture_of_extinction_fraction
loads_kg_m2[6]
sav_ratio_m_inv[6]
heat_content_j_kg[6]
particle_density_kg_m3[6]
total_mineral_fraction[6]
effective_mineral_fraction[6]
dynamic
burnable
```

`RothermelFuelMoisture` external inputs:

```text
dead_1h_fraction
dead_10h_fraction
dead_100h_fraction
live_herbaceous_fraction
live_woody_fraction
```

`RothermelInputs`:

```text
fuel
moisture
midflame_wind_speed_m_s
wind_from_direction_deg
slope_deg
aspect_deg
```

Wind direction is meteorological **from** direction. 10-m/20-ft → midflame adjustment belongs outside the core Rothermel input contract.

## 6. R1 implementation — stable baseline

`behavior/_units.py` centralizes tested conversions:

```text
m ↔ ft
kg/m² ↔ lb/ft²
kg/m³ ↔ lb/ft³
1/m ↔ 1/ft
J/kg ↔ Btu/lb
m/s ↔ ft/min
```

Implemented scientific R1 functions:

```text
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
```

The heterogeneous-fuel surface-area measure is proportional to:

```text
SAV × oven-dry load / particle density
```

The hand-computable synthetic regression fixture locks:

```text
dead 1-h within dead = 1/3
dead 10-h within dead = 2/3
live herb within live = 1
dead category = 3/7
live category = 4/7
characteristic SAV = 300 1/m
packing ratio = 0.003
bulk density = 3 kg/m³
```

R1 code baseline commit `793c393` is fully green across Ruff, quality pytest, and Python 3.11/3.12/3.13.

Do not redesign R1 simply to make R2 implementation shorter.

## 7. R2 reference variant — fixed

PyFireCA's R2 target is **Albini-adjusted Rothermel surface fire**, not an unlabelled mixture of 1972 and later formulas.

Albini 1976 changes already locked into the design:

1. combustible loading: `W0 * (1 - S_T)` rather than `W0 / (1 + S_T)`;
2. reaction-velocity exponent: `A = 133 * sigma^-0.7913`;
3. revised exponentially weighted live moisture-of-extinction calculation, bounded below by dead moisture of extinction;
4. dead and live reaction intensities are added rather than final-combined by the earlier category surface-area weighted average.

Andrews 2018 is the modern consistency reference because it explicitly describes operational Rothermel use with Albini 1976 adjustments.

## 8. Validation evidence policy

`docs/VALIDATION.md` now defines:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal synthetic/analytical fixture
```

Rules:

- a Grade C implementation never becomes scientific truth merely because it agrees with another package;
- when references disagree, resolve equation variant/units/conventions first;
- never weaken tolerances to hide a formulation mismatch;
- external fixtures record provenance and are protected from accidental edits.

## 9. Pinned validation fixtures

### Grade A — Albini 1976

`tests/validation/data/albini1976_worked_examples.csv`

Source: Albini 1976, USDA Forest Service GTR INT-30, worked examples.

Pinned outputs:

```text
Example 1
fuel model 3
fuel moisture 5%
20-ft wind 8 mi/h
level ground
→ spread rate 97 chains/hour
→ flame length 12.5 ft

Example 2
fuel model 2
fine dead moisture 8%
live foliage about 50%
calm wind
70% slope
→ spread rate 34 chains/hour
→ flame length 6.2 ft
```

These are future R3/R4 whole-model validation cases. They are **not** R2 fixtures because neither has both wind and slope equal to zero.

### Grade B — official Behave 7

`tests/validation/data/behave7_surface_reference.csv`

Pinned provenance:

```text
repository: firelab/behave-app
commit: a3cfcd5903188d73445948af16644868225bb9d5
source: behave-lib/test/csv/surface.csv
source blob: 975000d8dc3def0f25a22df0777e4ab70016c996
validator: behave-lib/test/cpp/testSurface.cpp
```

The official validator retrieves spread rate in `ChainsPerHour` and checks expected values with `1e-6` tolerance.

Both external snapshots have SHA-based integrity tests.

## 10. Current R2 validation gap

A precise tabulated **zero-wind AND zero-slope** external worked value matching the selected Albini-adjusted R2 formulation has not yet been located.

Known candidates are insufficient for this exact gate:

- Albini Example 1: level ground but nonzero wind;
- Albini Example 2: calm wind but nonzero slope;
- Rothermel 1972 includes no-wind theory and graphical curves, but graph reading is not precise enough for a high-accuracy regression constant;
- current official Behave 7 regression CSV has whole-surface cases but no dedicated zero-wind/zero-slope case.

**Do not fabricate an A-grade fixture from PyFireCA's own equations.**

If no suitable Grade A worked value exists, the acceptable fallback is to generate a **Grade B** zero-wind/zero-slope case from a pinned official Behave 7 build, record the exact build/input/output provenance, and keep it labeled Grade B.

## 11. CI state at this handoff

The R1 baseline is fully green.

The new validation infrastructure is running through the same CI. At the last check of run `31560693835`:

- Ruff lint: success;
- Ruff format: success;
- Python 3.13: success;
- Python 3.11 test step: success, workflow cleanup still completing;
- quality pytest: in progress;
- Python 3.12: still starting.

A preceding fixture-document run completed successfully. If the next session begins after CI completion, inspect the newest run and update this section rather than assuming failure/success.

## 12. Exact next implementation target

Do **not** jump to Cell2Fire-like propagation or wind/slope equations yet.

Next sequence:

```text
R2b finish external fixture strategy
 ↓
if needed, generate pinned Grade B zero-wind+zero-slope Behave 7 case
 ↓
R2c implement small Albini-adjusted pure functions
 ↓
R2d assemble validated no-wind/no-slope ROS
```

Planned R2c functions:

```text
combustible/net fuel loading
mineral damping
moisture damping
live moisture of extinction
Albini reaction-velocity exponent
maximum/actual reaction velocity
dead/live reaction intensity
propagating flux ratio
effective heating number
heat of preignition
heat source/sink
base ROS
```

Each function gets source/equation provenance and direct tests before the full ROS chain is assembled.

## 13. Later work — do not pull forward prematurely

After validated R2:

```text
R3  wind + slope
R4  RothermelModel.compute() → FireBehaviorResult
R5  verified Anderson/Scott-Burgan catalogues
E   first behavior-informed CA rule
F   FBP + Cell2Fire-like distance accumulation
G   Monte Carlo / crown / spotting / suppression
H   profiling-led Numba
```

Open later design questions include physical weather timestamps, GIS NoData execution policy, sparse/active-cell transitions, asynchronous scheduling, Cell2Fire distance state, GeoTIFF arrival-time conventions, and Monte Carlo RNG stream strategy.

## 14. Handoff discipline

Every development session must leave this file answering:

- what changed;
- what tests/CI pass;
- what remains incomplete;
- what scientific assumptions/variants are active;
- what design decisions were made;
- what exact file/function comes next;
- what must not be changed accidentally.

The handoff describes repository truth, not planned work that was never implemented.
