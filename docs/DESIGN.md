# PyFireCA Design Document

> Status: living design document
>
> Scope: architecture and scientific-software boundaries for the `v0.1.x` development line.

## 1. Purpose

PyFireCA is a wildfire cellular-automata research framework. Its primary purpose is to make the CA itself easy to study and modify without coupling CA changes to GIS I/O, fire-behavior equations, experiment scripts, or visualization code.

The project is **not** a generic urban/geospatial CA framework. Urban CA projects are engineering references only: they inform data contracts, GIS workflows, experiment organization, and software structure.

## 2. Design principles

1. **CA mechanisms are explicit.** State, neighborhood, transition rule, and time stepping must be visible in the API.
2. **Scientific equations are separated from propagation mechanics.** Fire behavior computes quantities such as ROS; CA rules decide how those quantities alter cells.
3. **Reference implementation first.** NumPy is the baseline implementation. Optimization follows profiling and must preserve reference behavior.
4. **GIS is an adapter layer.** The simulation kernel should not depend on file paths or perform implicit reprojection/resampling.
5. **Reproducibility is part of the model contract.** Randomness must be explicit and seeded through `numpy.random.Generator`.
6. **No premature platform architecture.** Avoid plugins, multiple backends, distributed execution, service layers, or GUI abstractions until a real need exists.
7. **Documentation evolves with code.** Design, status, validation, and handoff documents are mandatory development artifacts.

## 3. Core conceptual model

The minimal CA formulation used by PyFireCA is:

```text
Grid + State + Neighborhood + TransitionRule + Simulation
```

Wildfire behavior is added as a domain-specific collaborator:

```text
Environmental data
      ↓
FireBehaviorModel
      ↓
TransitionRule
      ↓
State update
```

The simulation orchestrator must not contain model-specific branches such as `if behavior == "rothermel"` or `if neighborhood == "moore"`.

## 4. Initial package structure

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

This layout is intentionally compact. Files become packages only when their implementation size or extension pressure justifies the split.

## 5. Component responsibilities

### 5.1 `state.py`

Owns CA state definitions and state-level invariants.

Initial wildfire states:

```text
UNBURNABLE
UNBURNED
BURNING
BURNED
```

Rules:

- numeric state codes must not be scattered as magic integers;
- state arrays should use compact integer dtypes;
- transitions that are impossible by model definition should be testable as invariants;
- future multi-stage combustion states may be added without changing `Simulation`.

### 5.2 `grid.py`

Owns the spatial lattice specification and state-array shape contract.

Initial implementation: `RasterGrid` only.

Expected metadata:

- height / width;
- cell size or affine transform when georeferenced;
- CRS when georeferenced;
- boundary semantics.

`Grid` does not read files and does not compute fire behavior.

### 5.3 `neighborhood.py`

Owns cell interaction geometry.

Initial types:

- Moore;
- Von Neumann;
- radius-based neighborhood.

Research extensions may include directional, weighted, adaptive, anisotropic, or multi-scale neighborhoods. These must be addable without changing `Simulation`.

A neighborhood should expose reusable offsets or equivalent index structures rather than instantiate Python `Cell` objects for every location.

### 5.4 `rules.py`

Owns CA transition mechanics. This is the main algorithm-research extension point.

Planned rule families:

- deterministic;
- probabilistic;
- distance-accumulation / Cell2Fire-like;
- future adaptive variants.

A transition rule may consume fire-behavior output, local environmental layers, neighborhood information, current state, time, and RNG. It should return state changes or transition information without performing GIS I/O.

### 5.5 `behavior/`

Owns wildfire behavior calculations but **not** spatial CA propagation.

A common behavior interface should eventually return a structured result containing quantities such as:

- spread rate;
- spread direction;
- fireline intensity when supported;
- optional model-specific diagnostics.

Initial scientific targets:

1. Rothermel-style surface fire behavior;
2. FBP-style behavior for Cell2Fire-related experiments.

Implementations should be independently testable against reference calculations.

### 5.6 `data.py`

Owns in-memory environmental layers and time-varying data access.

The design borrows the useful idea behind space-time cubes without copying a Level Set architecture.

Expected shapes:

```text
static layer:   (Y, X)
dynamic layer:  (T, Y, X)
state:          (Y, X)
```

The kernel should work with arrays, not file paths.

### 5.7 `gis.py`

Owns geospatial adapters and validation helpers.

Initial responsibilities:

- read/write raster data;
- preserve CRS and affine transform;
- validate alignment;
- fail explicitly on incompatible grids;
- no silent reprojection or resampling in the core workflow.

The first release may keep Rasterio as an optional dependency so the CA core remains lightweight.

### 5.8 `simulation.py`

Owns orchestration only:

```text
initialize → step → run → stop
```

It manages:

- current step/time;
- explicit RNG;
- application of a transition rule;
- stop conditions;
- optional callbacks later if justified.

It must stay scientifically boring. Model-specific formulas do not belong here.

### 5.9 `metrics.py`

Owns model outputs and evaluation measures rather than simulation mechanics.

Planned outputs include:

- burned area;
- active burning cells;
- arrival time;
- perimeter-derived metrics;
- spatial overlap metrics for validation.

## 6. Data representation strategy

PyFireCA should prefer **structure-of-arrays** representations:

```text
state       [Y, X]
fuel        [Y, X]
slope       [Y, X]
aspect      [Y, X]
wind_speed  [T, Y, X]
wind_dir    [T, Y, X]
moisture    [T, Y, X]
```

Avoid millions of Python `Cell` objects containing duplicated attributes. A cell is primarily an array location `(row, col)`.

This choice supports readable NumPy code now and possible Numba acceleration later.

## 7. GIS data contract

Before simulation, raster inputs must be checked for compatible:

- CRS;
- shape;
- resolution;
- affine transform;
- extent;
- NoData policy;
- units where scientifically important.

Incompatibility should raise an explicit project exception rather than being silently corrected.

Reprojection/alignment utilities may exist, but they must be called intentionally by preprocessing code.

## 8. Randomness and reproducibility

Do not use global `np.random.seed()` as model state.

Preferred pattern:

```python
rng = np.random.default_rng(seed)
```

The RNG is passed into the simulation/rule boundary. A fixed configuration and fixed seed should reproduce a deterministic regression artifact within documented numerical tolerance.

Monte Carlo execution will later derive independent streams explicitly rather than reusing hidden global state.

## 9. Configuration boundary

Configuration is an orchestration concern, not the internal model representation.

A YAML configuration may select:

```yaml
simulation:
  steps: 100
  seed: 42

ca:
  neighborhood:
    type: moore
    radius: 1
  rule:
    type: distance

behavior:
  model: rothermel
```

Internally, validated configuration should construct normal Python objects. Core numerical functions should not repeatedly query raw YAML dictionaries.

Initial implementation should prefer standard-library dataclasses and a small YAML dependency only when configuration work begins. Do not add Pydantic until validation requirements justify it.

## 10. Performance policy

Performance evolution:

```text
NumPy reference
    ↓ profile
Numba on measured hotspots
    ↓ only if needed
additional acceleration
```

Requirements:

- keep a readable reference path;
- benchmark separately from correctness tests;
- optimization must not change scientific semantics silently;
- backend equivalence tests are required before an optimized path becomes default.

PyTorch/JAX/differentiable CA are explicitly outside the current scope.

## 11. Testing architecture

Four mandatory levels:

```text
unit        — isolated contracts and invariants
integration — multiple components in one short simulation
regression  — stable reference outputs with fixed seed/config
validation  — comparison with scientific/reference calculations
```

Performance benchmarks live under `benchmarks/`, not `tests/`.

## 12. Reference projects and what is borrowed

The project should learn selectively rather than copy architectures wholesale:

- **Cell2Fire** — cell-based wildfire propagation, distance/ROS concepts, landscape simulation and Monte Carlo;
- **SimFire** — Python simulation API organization and mitigation concepts;
- **GridFire** — raster modeling, Monte Carlo organization, richer wildfire system concerns;
- **Pyretechnics** — modular fire-behavior equations and static/dynamic environmental data organization; Level Set propagation is not adopted;
- **ELMFIRE / ForeFire** — comparison baselines for non-CA propagation, not implementation targets;
- **UrbanVCA / PLUS / intPLUS** — GIS preprocessing, raster contracts, experiment/data workflow ideas only;
- **Mesa-Geo** — modern Python GIS engineering, documentation, CI, repository hygiene.

## 13. Explicit non-goals for `v0.1.x`

- generic urban CA framework;
- differentiable CA;
- PyTorch/JAX backend;
- GPU acceleration;
- Level Set propagation;
- front tracking;
- CFD/fire-atmosphere coupling;
- plugin ecosystem / entry points;
- REST API / Web UI / database;
- distributed execution.

## 14. Extension rule

A proposed feature is architecturally healthy when it can be added by extending one clearly owned component with minimal modification elsewhere.

Examples:

- new neighborhood → `neighborhood.py` + tests;
- new CA rule → `rules.py` + tests;
- new fire behavior model → `behavior/` + validation;
- new raster file format → GIS/data adapter code;
- new metric → `metrics.py`.

If a new CA rule requires edits throughout GIS, simulation, configuration, and grid code, the abstraction boundaries should be reviewed before implementation.

## 15. Design decisions log

### D001 — Wildfire-specific product scope

PyFireCA is a wildfire CA framework. Urban CA projects are references, not supported domains.

### D002 — Compact module layout

Start with a small number of modules. Do not create one directory/class per hypothetical future extension.

### D003 — NumPy as the scientific reference

The first correct implementation is NumPy. Numba is introduced only after profiling.

### D004 — Fire behavior separate from CA propagation

ROS/intensity calculations and cell-transition mechanics remain independently replaceable.

### D005 — GIS metadata is explicit

Geospatial alignment is validated before simulation; the kernel never silently repairs incompatible inputs.

### D006 — Development documentation is mandatory

Every meaningful architecture or scientific change must update `DESIGN.md`, `STATUS.md`, and `HANDOFF.md` when affected.
