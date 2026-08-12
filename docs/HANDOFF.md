# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: allow the next development session or contributor to continue immediately without reconstructing design context from chat history.

## 1. Project identity

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. It is not intended to become a generic urban CA platform. Urban CA projects were reviewed only to learn GIS data organization, raster contracts, experiment structure, and software engineering.

Primary research interest: **modify and study the CA itself**.

The architecture therefore protects these extension points:

```text
State
Neighborhood
Transition Rule
Time stepping / scheduler
```

Fire behavior and GIS are supporting layers, not the definition of the CA engine.

## 2. Reference-project lessons already accepted

### Cell2Fire

Use as the main wildfire-CA scientific reference for:

- cell-based landscape propagation;
- ROS-driven cell-to-cell spread;
- distance/ellipse ideas;
- Monte Carlo landscape experiments.

Do not copy its implementation architecture wholesale. PyFireCA should keep Python modules and interfaces more explicit and testable.

### SimFire

Use for:

- Python simulation-manager ideas;
- Rothermel-oriented wildfire workflow;
- mitigation/suppression concepts;
- separation between environment and simulation objects.

Avoid coupling rendering/game concerns to the numerical kernel.

### GridFire

Use for:

- raster fire-model organization;
- Monte Carlo and richer wildfire-system concerns;
- performance/scenario thinking.

Do not adopt Clojure-specific architecture simply for similarity.

### Pyretechnics

Use mainly for:

- modular fire-behavior equations;
- clean separation of surface/crown/spot behavior;
- static + dynamic environmental data abstraction;
- reference implementation ideas.

Do **not** adopt its Level Set propagation as PyFireCA's core. PyFireCA remains CA-first.

### ELMFIRE / ForeFire

Keep as non-CA comparison baselines. They are not implementation targets for the first development line.

### UrbanVCA / PLUS / intPLUS

Engineering references only:

- preprocessing pipeline separation;
- GIS raster compatibility requirements;
- driving/environmental layer organization;
- simulation vs assessment separation.

UrbanVCA's flat research-script layout should **not** be copied into PyFireCA.

### Mesa-Geo

Use as a software-engineering reference for:

- Python package hygiene;
- GIS-aware abstractions;
- CI / pre-commit / coverage;
- documentation and contribution standards.

Do not force agent-based abstractions into a raster CA where arrays are more appropriate.

## 3. Explicitly deferred reference

PyTorchFire is intentionally deferred.

Do not introduce in the current development line:

- differentiable CA;
- Torch backend;
- JAX backend;
- GPU abstraction;
- gradient calibration.

These may be reconsidered only after the classical CA framework is scientifically stable.

## 4. Current architecture

The intended initial source tree is compact:

```text
src/pyfireca/
├── __init__.py
├── state.py
├── grid.py
├── neighborhood.py
├── rules.py
├── simulation.py
├── data.py
├── gis.py
├── config.py
├── metrics.py
└── behavior/
    ├── __init__.py
    ├── base.py
    ├── rothermel.py
    ├── fbp.py
    └── fuel.py
```

Important: this is a target boundary, not a requirement to create empty files. Add files when the corresponding milestone starts.

## 5. Core design contract

### State

States are explicit enums/codes, not magic integers. Initial state set:

```text
UNBURNABLE
UNBURNED
BURNING
BURNED
```

### Grid

Initial implementation is a raster grid. Do not prematurely add hex/vector/grid subclasses until real use requires them.

### Neighborhood

Must be replaceable independently of simulation. Start with Moore and Von Neumann. Radius/directional/adaptive variants come later.

### Transition rule

This is the main research extension point. A rule changes state using current state, neighbors, environment, behavior output, time, and optionally RNG.

### Fire behavior

Rothermel/FBP calculate physical or empirical fire-behavior quantities. They do not directly own the CA simulation loop.

### Simulation

Orchestration only. `Simulation` should not contain branches that select fire-behavior models or GIS formats.

### Data/GIS

The kernel consumes arrays/domain objects. File paths are resolved outside it. Raster compatibility must be checked explicitly.

## 6. Performance contract

Do not begin with C++, Cython, CUDA, Torch, or JAX.

Development order:

```text
readable NumPy reference
      ↓
scientific tests + regression tests
      ↓
profiling
      ↓
Numba only for measured hotspots
```

Keep the reference implementation even after optimization so numerical equivalence can be tested.

## 7. Data contract direction

Prefer structure-of-arrays:

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

GIS compatibility checks should eventually cover:

```text
CRS
shape
resolution
transform
extent
NoData
units where important
```

## 8. Documentation/repository standard

The project follows the same documentation philosophy as RepoForge:

- README is the landing page, not the manual;
- scientific method details and validation live under `docs/`;
- README should stay representative and runnable;
- validation and limitations must be explicit;
- development-stage documents are kept current.

The project is expected to use the RepoForge `scientific-python / standard` profile once the first scaffold settles.

## 9. What has already been created

At the time of this handoff:

- `README.md`;
- `README.zh-CN.md`;
- `pyproject.toml`;
- `docs/DESIGN.md`;
- `docs/DEVELOPMENT.md`;
- `docs/STATUS.md`;
- this `docs/HANDOFF.md`.

The bootstrap pass continues after this file with validation, core code, tests, and CI.

## 10. Immediate next implementation order

Continue in this order unless a concrete bug requires otherwise:

```text
1. FireState
2. Neighborhood base behavior
3. MooreNeighborhood
4. VonNeumannNeighborhood
5. tests for exact offsets and invalid radius
6. RasterGrid shape/state validation
7. TransitionRule protocol/ABC
8. minimal synchronous Simulation
9. explicit RNG
10. one deterministic regression example
```

Do not start Rothermel/FBP before steps 1–8 are understandable and tested.

## 11. Questions that still require explicit design decisions

These are deliberately open and should be resolved with tests/documentation when their milestone begins:

1. Exact boundary semantics: clipped neighbors vs padded/periodic options.
2. Whether state updates are returned as full arrays, sparse indices, or transition objects.
3. Initial scheduler semantics beyond synchronous update.
4. Exact distance-accumulation state required for a Cell2Fire-like rule.
5. Unit system and common result schema for Rothermel/FBP.
6. How dynamic weather time indexing maps to simulation time.
7. GeoTIFF output convention for arrival time and NoData.

Do not hide these decisions in implementation details; record them in `DESIGN.md` when resolved.

## 12. Definition of a good next handoff

At the end of every development session, update this file so the next session can answer immediately:

- What changed?
- What tests pass?
- What is incomplete?
- What design decisions were made?
- What must not be changed accidentally?
- What exact file/function should be implemented next?
- Are there any known scientific or numerical uncertainties?

The handoff should describe repository truth, not plans that were never implemented.
