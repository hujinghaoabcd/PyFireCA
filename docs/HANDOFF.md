# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: allow the next development session or contributor to continue immediately without reconstructing design context from chat history.

## 1. Project identity

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. Urban CA projects are engineering/GIS references only; they are not supported simulation domains.

Primary research interest: **modify and study the CA itself**.

Protected CA extension points:

```text
State
Neighborhood
Transition Rule
Time stepping / scheduler
```

Fire behavior and GIS support the CA but do not define the simulation engine.

## 2. Scope decisions that should not be casually reversed

1. PyFireCA is wildfire-specific.
2. UrbanVCA / PLUS / intPLUS / Mesa-Geo inform engineering only.
3. PyTorchFire-style differentiable CA, Torch/JAX, and GPU backends are deferred.
4. Level Set and front tracking remain comparison methods, not core propagation engines.
5. NumPy remains the readable scientific reference implementation.
6. Numba is introduced only after profiling.
7. Fire behavior and CA propagation remain separate.
8. GIS file I/O remains outside numerical kernels.
9. The package tree stays compact until real complexity justifies splitting it.
10. Design/status/handoff/validation documents are maintained continuously.
11. Behavior outputs are standardized; model-native Rothermel/FBP inputs remain strongly typed and model-specific.
12. Physical weather time interpolation is deferred until a concrete data integration exists.
13. Rothermel is the first behavior reference implementation; FBP remains required later for Cell2Fire-oriented comparisons.

The last item is a sequencing decision, not a claim that Rothermel is universally preferable to FBP.

## 3. Reference-project lessons

### Cell2Fire

Use for cell-based wildfire propagation, ROS-driven cell-to-cell spread, distance/ellipse concepts, and Monte Carlo landscape experiments. Do not copy its architecture wholesale.

### SimFire

Use for Python simulation organization and as an independent Rothermel comparison path. Avoid coupling rendering/game concerns to numerical kernels.

### GridFire

Use for raster wildfire organization, Monte Carlo/scenario ideas, richer wildfire processes, and later performance comparisons.

### Pyretechnics

Use for modular fire-behavior organization, six-class fuel representation ideas, surface/crown/spot separation, and an independent Rothermel comparison path. Do **not** adopt its Level Set engine. Do not copy its EPL-licensed source into PyFireCA; implement published equations independently.

### ELMFIRE / ForeFire

Non-CA comparison baselines only.

### UrbanVCA / PLUS / intPLUS / Mesa-Geo

Engineering references for GIS preprocessing, raster contracts, CI, documentation, and modern project organization only.

## 4. Current implemented source tree

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
    └── rothermel.py
```

Tests:

```text
tests/
├── test_behavior_base.py
├── test_data.py
├── test_grid.py
├── test_neighborhood.py
├── test_rothermel_inputs.py
├── test_rules.py
├── test_simulation.py
└── test_state.py
```

Do not create empty `gis.py`, `config.py`, `metrics.py`, `fbp.py`, or additional packages merely to match an architecture diagram. Add them when their milestone starts.

## 5. CA core truth

### Fire state

```text
UNBURNABLE = 0
UNBURNED   = 1
BURNING    = 2
BURNED     = 3
```

State arrays are validated as two-dimensional integer arrays.

### Raster grid

`RasterGrid` owns the state array, shape, optional positive `cell_size`, safe state replacement, and independent copy. CRS/transform metadata are not implemented yet.

### Neighborhoods

Implemented:

```text
Neighborhood protocol
MooreNeighborhood
VonNeumannNeighborhood
valid_neighbor_indices
```

Current edge policy is clipping.

### Transition semantics

`TransitionRule.next_state(grid, *, rng)` reads the current full state and returns a complete next-state array. `Simulation` applies it only after rule evaluation finishes.

This makes the reference engine explicitly **synchronous**. Newly ignited cells cannot propagate again in the same step.

### Reference rule

`NeighborIgnitionRule` is an architectural baseline only. It contains no physical fire behavior.

## 6. Common fire-behavior contract

`src/pyfireca/behavior/base.py` implements:

```text
FireBehaviorModel[InputT]
FireBehaviorResult
```

Common result fields:

```text
spread_rate_m_s            required
spread_direction_deg       optional
fireline_intensity_w_m     optional
flame_length_m              optional
diagnostics                 optional model-specific scalar mapping
```

Direction convention:

```text
0°   north
90°  east
180° south
270° west
```

Angles increase clockwise and must satisfy `[0, 360)`.

The stable interchange boundary is the **result**. Do not replace the generic model input type with a giant all-model input dataclass.

## 7. Environmental data contract

`src/pyfireca/data.py` implements:

```text
SpatialLayer
EnvironmentalData
```

`SpatialLayer` supports:

```text
static   (Y, X)
dynamic  (T, Y, X)
```

with optional `units` and `nodata` metadata.

`EnvironmentalData` requires one shared spatial shape and one shared dynamic time length. `snapshot(t)` returns aligned 2-D arrays.

Current limitations are intentional:

- integer time index only;
- no datetime interpolation;
- no CRS/affine metadata in `SpatialLayer`;
- NoData is metadata only;
- no hidden masking/imputation;
- no xarray/Zarr abstraction.

Detailed rules: `docs/BEHAVIOR_DATA_CONTRACT.md`.

## 8. Rothermel input contract

`src/pyfireca/behavior/rothermel.py` now exists but contains **inputs/validation only**, not the equation implementation.

### Fuel class order

The public six-class order is fixed:

```text
0 DEAD_1H
1 DEAD_10H
2 DEAD_100H
3 DEAD_HERBACEOUS
4 LIVE_HERBACEOUS
5 LIVE_WOODY
```

Do not reorder these indices. Tests intentionally lock them.

### `RothermelFuelModel`

Public SI fields:

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

Validation rules:

- positive integer code;
- finite/non-negative quantities;
- mineral fractions in `[0, 1]`;
- burnable model requires positive depth, extinction moisture, and total load;
- a loaded fuel class requires positive SAV ratio, heat content, and particle density;
- a nonburnable model may use zeros.

The dataclass is not yet tied to an Anderson or Scott--Burgan catalogue.

### `RothermelFuelMoisture`

External moisture inputs:

```text
dead_1h_fraction
dead_10h_fraction
dead_100h_fraction
live_herbaceous_fraction
live_woody_fraction
```

`as_six_class_values()` currently assigns dead-herbaceous moisture from dead 1-h moisture. Live moisture may exceed 1.0 on a dry-mass basis.

Dynamic herbaceous load transfer is not implemented yet.

### `RothermelInputs`

```text
fuel
moisture
midflame_wind_speed_m_s
wind_from_direction_deg
slope_deg
aspect_deg
```

Important conventions:

- wind speed is **midflame** wind;
- `wind_from_direction_deg` is meteorological from-direction;
- slope is `[0, 90)` degrees;
- aspect is clockwise from geographic north;
- 10-m/20-ft wind adjustment does not belong inside the core Rothermel input contract.

Detailed plan: `docs/ROTHERMEL_REFERENCE.md`.

## 9. Scientific source/provenance rule

The Rothermel code must be an independent implementation of published equations.

Primary reference path documented for implementation:

1. Rothermel 1972, USDA Forest Service Research Paper INT-115;
2. Albini 1976, USDA Forest Service GTR INT-30 where applicable;
3. Andrews 2018, USDA Forest Service RMRS-GTR-371;
4. Scott & Burgan 2005, USDA Forest Service RMRS-GTR-153 for later fuel catalogues.

SimFire and Pyretechnics are independent numerical comparison paths. They are **not** code sources to copy.

When two implementations disagree, return to the scientific reference and add a regression/reference test for the resolved interpretation.

## 10. CI / engineering state

GitHub Actions currently runs:

```text
Ruff lint
Ruff format --check
pytest + coverage
Python 3.11 pytest
Python 3.12 pytest
Python 3.13 pytest
```

The latest run after formatting the Rothermel input contract completed fully green.

Engineering files already present:

```text
.github/workflows/ci.yml
.pre-commit-config.yaml
.gitignore
pyproject.toml
CITATION.cff
CHANGELOG.md
CONTRIBUTING.md
README.md
README.zh-CN.md
```

RepoForge migration remains intentionally deferred. When applied, use `scientific-python / standard` with managed README sections; do not overwrite the hand-written scientific README body without reviewed migration.

## 11. Performance contract

Do not start C++, Cython, CUDA, Torch, or JAX.

```text
readable NumPy reference
      ↓
scientific/reference tests
      ↓
profiling
      ↓
Numba for measured hotspots only
```

Keep the NumPy path after optimization for numerical equivalence tests.

## 12. Exact next implementation target

Do **not** redesign the input contract and do **not** jump to Cell2Fire-like propagation yet.

Continue Rothermel in stages:

```text
R1 explicit unit conversions + base fuel quantities
 ↓
R2 no-wind / no-slope surface ROS
 ↓
R3 wind + slope effects
 ↓
R4 FireBehaviorResult output
 ↓
R5 verified standard fuel catalogues
 ↓
R6 behavior-informed CA rule
```

### Next code work

1. define explicit native/legacy-unit conversion helpers required by the published equation path;
2. test conversions independently;
3. implement small pure functions for base Rothermel fuel quantities;
4. create numeric reference fixtures from authoritative material before accepting complete ROS calculations;
5. keep each equation stage directly testable;
6. do not mix directional CA neighborhood logic into the behavior equations.

## 13. Open questions

Resolved:

- common behavior result fields/units;
- direction convention;
- static/dynamic in-memory layer shape;
- model-specific input policy;
- first behavior family: Rothermel;
- initial six-class Rothermel fuel representation;
- midflame wind as the core behavior input.

Still open:

1. exact internal legacy-unit calculation strategy for the reference equation implementation;
2. authoritative numerical fixtures for each Rothermel stage;
3. dynamic fuel curing implementation details;
4. physical weather timestamps/interpolation;
5. sparse vs full-array CA transitions after profiling;
6. asynchronous/event-driven scheduler architecture;
7. extra propagation state for Cell2Fire-like distance accumulation;
8. GeoTIFF/NoData conventions for state and arrival-time outputs;
9. Monte Carlo RNG stream strategy.

Any resolved item that affects architecture/scientific interpretation must be documented before or with code.

## 14. Handoff checklist

At the end of every development session this file must answer:

- what changed;
- what tests/CI pass;
- what is incomplete;
- what scientific assumptions were introduced;
- what design decisions were made;
- what exact module/function comes next;
- what must not be changed accidentally.

The handoff describes repository truth, not planned work that was never implemented.
