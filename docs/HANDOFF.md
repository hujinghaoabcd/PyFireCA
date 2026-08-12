# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: allow the next development session or contributor to continue immediately without reconstructing design context from chat history.

## 1. Project identity

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. It is not intended to become a generic urban CA platform. Urban CA projects are engineering references only: they inform GIS data organization, raster contracts, experiment structure, and software engineering.

Primary research interest: **modify and study the CA itself**.

Protected CA extension points:

```text
State
Neighborhood
Transition Rule
Time stepping / scheduler
```

Fire behavior and GIS are supporting layers, not the definition of the CA engine.

## 2. Scope decisions already made

Do not casually reverse these decisions without updating `docs/DESIGN.md` and explaining the scientific reason.

1. PyFireCA is wildfire-specific.
2. UrbanVCA / PLUS / intPLUS / Mesa-Geo do not become supported urban-model modules.
3. PyTorchFire-style differentiable CA is deferred.
4. Level Set and front tracking remain comparison methods, not core propagation engines.
5. NumPy is the readable scientific reference implementation.
6. Numba is introduced only after profiling.
7. Fire behavior and CA propagation remain separate.
8. GIS file I/O remains outside numerical kernels.
9. The package tree stays compact until real extension pressure justifies splitting files.
10. Development design/status/handoff/validation documents are maintained continuously.
11. Behavior-model outputs are standardized, but Rothermel/FBP native inputs are **not** forced into one oversized common input type.
12. Physical weather time interpolation is deferred until a real weather-source integration is implemented.

## 3. Reference-project lessons already accepted

### Cell2Fire

Main wildfire-CA reference for:

- cell-based landscape propagation;
- ROS-driven cell-to-cell spread;
- distance/ellipse concepts;
- Monte Carlo landscape experiments.

Do not copy its implementation architecture wholesale.

### SimFire

Use for:

- Python simulation-manager ideas;
- Rothermel-oriented wildfire workflow;
- mitigation/suppression concepts;
- environment/simulation separation.

Avoid coupling rendering/game concerns to the numerical kernel.

### GridFire

Use for:

- raster fire-model organization;
- Monte Carlo/scenario ideas;
- richer wildfire system concerns;
- later performance comparisons.

### Pyretechnics

Use mainly for:

- modular fire-behavior equations;
- surface/crown/spot separation;
- static + dynamic environmental data organization;
- reference-calculation ideas.

Do **not** adopt its Level Set propagation as PyFireCA's core.

### ELMFIRE / ForeFire

Keep as non-CA comparison baselines only.

### UrbanVCA / PLUS / intPLUS

Engineering references only:

- preprocessing pipeline separation;
- GIS raster compatibility requirements;
- driving/environmental layer organization;
- simulation vs assessment separation.

UrbanVCA's flat research-script layout should not be copied.

### Mesa-Geo

Use as a modern Python/GIS engineering reference for:

- package hygiene;
- CI / pre-commit / coverage;
- documentation and contribution standards;
- GIS-aware design.

Do not force agent-based abstractions into a raster CA where arrays are more appropriate.

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
    └── base.py
```

Current examples/tests:

```text
examples/
└── minimal.py

tests/
├── test_behavior_base.py
├── test_data.py
├── test_grid.py
├── test_neighborhood.py
├── test_rules.py
├── test_simulation.py
└── test_state.py
```

Files such as `gis.py`, `config.py`, `metrics.py`, `behavior/rothermel.py`, `behavior/fbp.py`, and fuel modules should be added only when their milestone starts. Do not create empty placeholders simply to match a diagram.

## 5. Current CA behavior

### `FireState`

```text
UNBURNABLE = 0
UNBURNED   = 1
BURNING    = 2
BURNED     = 3
```

`validate_state_array()` requires a two-dimensional integer array and rejects unsupported state codes.

### `RasterGrid`

Implemented:

- state validation;
- `shape` property;
- optional positive `cell_size`;
- safe state replacement with shape checking;
- independent copy.

No CRS/transform metadata yet.

### Neighborhoods

Implemented:

- `Neighborhood` structural protocol;
- `MooreNeighborhood(radius=...)`;
- `VonNeumannNeighborhood(radius=...)`;
- `valid_neighbor_indices(...)`.

Current boundary semantics are **clipping**: off-grid neighbors are omitted.

### `TransitionRule`

Implemented as a synchronous protocol:

```python
next_state(grid, *, rng) -> array
```

The rule reads the current grid and returns a complete next-state array. `Simulation` applies it only after computation finishes.

### `NeighborIgnitionRule`

Architectural baseline only:

```text
BURNING cell
    ↓
becomes BURNED next step
    +
currently UNBURNED neighbors become BURNING
```

It intentionally contains no Rothermel/FBP physics.

### `Simulation`

Implemented:

- `Simulation.from_seed(...)`;
- explicit `numpy.random.Generator`;
- `step()`;
- `run(steps)`;
- output shape/state validation;
- explicit synchronous replacement semantics.

## 6. Current fire-behavior contract

Implemented in `src/pyfireca/behavior/base.py`.

### `FireBehaviorResult`

Common CA-facing fields:

```text
spread_rate_m_s           required
spread_direction_deg      optional
fireline_intensity_w_m    optional
flame_length_m             optional
diagnostics                optional model-specific scalar mapping
```

Conventions:

- spread rate: metres per second;
- fireline intensity: watts per metre;
- flame length: metres;
- direction: degrees clockwise from geographic north;
- direction must satisfy `[0, 360)`;
- invalid/non-finite common values raise errors rather than being silently repaired.

### `FireBehaviorModel[InputT]`

The protocol is generic in the input type:

```python
compute(inputs: InputT) -> FireBehaviorResult
```

This is deliberate. A future `RothermelInputs` and `FBPInputs` may differ. The stable interchange boundary is the **result**, not a giant all-model input object.

Detailed contract: `docs/BEHAVIOR_DATA_CONTRACT.md`.

## 7. Current environmental data contract

Implemented in `src/pyfireca/data.py`.

### `SpatialLayer`

Supports:

```text
static   (Y, X)
dynamic  (T, Y, X)
```

Metadata:

```text
units
nodata
```

`at(time_index)` provides one `(Y, X)` view. Static layers ignore the requested index; dynamic layers require a valid integer index.

### `EnvironmentalData`

A named collection of `SpatialLayer` objects.

Current invariants:

- at least one layer;
- non-empty layer names;
- every layer has the same spatial shape;
- every dynamic layer has the same time length;
- `snapshot(t)` returns aligned `(Y, X)` arrays.

Important limitations:

- time is currently integer-index based;
- no datetime coordinate/interpolation;
- no CRS/transform metadata here;
- `nodata` is metadata only;
- no automatic masking/imputation;
- no xarray/Zarr abstraction yet.

## 8. Test / CI state

GitHub Actions includes:

- Ruff lint;
- Ruff format check;
- pytest + coverage in the quality job;
- pytest matrix for Python 3.11, 3.12, 3.13.

Milestone C added tests for:

- valid/invalid common behavior results;
- model-specific behavior input compatibility;
- static/dynamic layer indexing;
- invalid data dimensions/dtypes;
- spatial alignment;
- dynamic time-length alignment;
- missing layer errors;
- mixed static/dynamic snapshots.

CI initially caught only style/format issues in the new files. These were fixed. At the final check in this session:

- quality job: success;
- Python 3.12: success;
- Python 3.13: success;
- Python 3.11 test step: success, workflow cleanup still finishing.

If the next session starts with a red badge, inspect the newest run first; do not change scientific code based on an old failed formatting run.

## 9. Engineering / documentation files

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

docs/DESIGN.md
docs/DEVELOPMENT.md
docs/STATUS.md
docs/HANDOFF.md
docs/VALIDATION.md
docs/BEHAVIOR_DATA_CONTRACT.md
```

RepoForge philosophy to preserve:

- use `scientific-python / standard` when migrated;
- README is a landing page;
- scientific body prose remains hand-maintained;
- prefer RepoForge managed header sections rather than whole-file ownership;
- do not force migration until the diff is reviewed.

## 10. Performance contract

Do not begin with C++, Cython, CUDA, Torch, or JAX.

Development order:

```text
readable NumPy reference
      ↓
scientific/regression tests
      ↓
profiling
      ↓
Numba only for measured hotspots
```

Keep the NumPy reference after optimization so numerical equivalence can be tested.

## 11. Data-model direction

Continue structure-of-arrays:

```text
state       [Y, X]
fuel        [Y, X]
slope       [Y, X]
aspect      [Y, X]
wind_speed  [T, Y, X]
wind_dir    [T, Y, X]
moisture    [T, Y, X]
```

Do not create one heavyweight Python object per raster cell.

Future GIS compatibility checks still need:

```text
CRS
shape
resolution
transform
extent
NoData execution policy
units where scientifically important
```

## 12. Immediate next implementation target

The common result/data boundary is now implemented. The next session should **not** redesign it unless a validated scientific requirement proves it inadequate.

Next task:

```text
first real behavior family
      ↓
model-specific typed inputs
      ↓
initial fuel representation
      ↓
reference fixtures
      ↓
scientific equations
```

Recommended exact sequence:

1. choose whether the first validated behavior implementation is Rothermel or FBP;
2. inspect the authoritative equations/reference implementation used for validation;
3. define only that model's required input dataclass and fuel representation;
4. document source units and conversion rules;
5. create reference fixtures before implementing the full equation chain;
6. implement the readable NumPy reference;
7. connect it to `FireBehaviorResult`;
8. only then build a behavior-informed CA rule.

Because Cell2Fire is the principal CA reference, FBP will eventually be required. Rothermel remains useful because SimFire/Pyretechnics provide independent comparison paths. Choose the first implementation based on validation quality, not which file is shorter.

## 13. Open design questions

Resolved this session:

- common behavior output fields/units;
- common direction convention;
- static/dynamic in-memory layer representation;
- dynamic layers currently use a common integer time length;
- behavior inputs remain model-specific.

Still open:

1. first behavior family to implement/validate;
2. exact first fuel representation;
3. how dynamic weather physical timestamps map to simulation time;
4. full-array vs sparse transitions for later performance work;
5. asynchronous/event-driven scheduler architecture;
6. extra propagation state for Cell2Fire-like distance accumulation;
7. GeoTIFF metadata/NoData convention for arrival time/state outputs;
8. Monte Carlo RNG stream-generation policy.

When one is resolved, record it in `docs/DESIGN.md` rather than hiding it inside code.

## 14. Definition of a good next handoff

At the end of every development session, this file should answer:

- What changed?
- What tests/CI pass?
- What remains incomplete?
- What scientific assumptions were introduced?
- What design decisions were made?
- What exact module/function should be implemented next?
- What must not be changed accidentally?

The handoff must describe repository truth, not aspirational work that was never implemented.
