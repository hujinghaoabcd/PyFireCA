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
8. **Scientific reference values carry provenance.** External numerical fixtures must identify their source, variant, units, and evidence grade rather than appearing as unexplained constants.

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
    ├── _units.py
    ├── rothermel.py
    ├── fbp.py
    └── fuel.py
```

This layout is intentionally compact. Files become packages only when their implementation size or extension pressure justifies the split. The tree above describes ownership boundaries, not a requirement to create empty files before their milestone begins.

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

Owns the spatial lattice and CA state-array shape contract.

Initial implementation: `RasterGrid` only.

`RasterGrid` currently stores state and optional cell size. It does not yet own CRS/affine metadata. Geospatial ownership is deliberately postponed until the Rasterio adapter workflow demonstrates whether shared domain metadata or optional grid metadata is cleaner.

`Grid` does not read files and does not compute fire behavior.

### 5.3 `neighborhood.py`

Owns cell interaction geometry.

Initial types:

- Moore;
- Von Neumann.

Research extensions may include radius, directional, weighted, adaptive, anisotropic, or multi-scale neighborhoods. These must be addable without changing `Simulation`.

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

All behavior implementations return a common `FireBehaviorResult` containing standardized quantities used by CA rules. The current common boundary is:

- `spread_rate_m_s` — required, finite and non-negative;
- `spread_direction_deg` — optional, degrees clockwise from geographic north in `[0, 360)`;
- `fireline_intensity_w_m` — optional;
- `flame_length_m` — optional;
- `diagnostics` — optional model-specific scalar values.

The behavior model input type is intentionally generic. Rothermel- and FBP-style implementations may define different strongly typed input dataclasses rather than being forced into one oversized common input object. Their scientific differences stay visible; interchangeability occurs at the common result boundary.

Initial scientific targets:

1. Albini-adjusted Rothermel surface fire behavior as the first reference implementation;
2. FBP-style behavior for later Cell2Fire-related experiments.

Implementations must be independently testable against reference calculations. Detailed unit, direction, and adapter rules are maintained in [`BEHAVIOR_DATA_CONTRACT.md`](BEHAVIOR_DATA_CONTRACT.md), and Rothermel-specific provenance/validation decisions in [`ROTHERMEL_REFERENCE.md`](ROTHERMEL_REFERENCE.md).

### 5.6 `data.py`

Owns in-memory environmental layers and time-varying data access.

The implemented contract is deliberately small:

```text
SpatialLayer
EnvironmentalData
```

A `SpatialLayer` is either:

```text
static layer:   (Y, X)
dynamic layer:  (T, Y, X)
```

It may carry explicit `units` and `nodata` metadata. `EnvironmentalData` validates a shared spatial shape across all layers and, for the initial index-based contract, a shared time length across dynamic layers.

Static and dynamic layers can be accessed through one snapshot call without creating heavyweight Python `Cell` objects. Physical timestamps/interpolation, xarray/Zarr abstractions, and GIS metadata are intentionally deferred until concrete integrations require them.

The kernel works with arrays, not file paths.

### 5.7 `gis.py`

Owns the lightweight geospatial raster contract and later file-format adapters.

The currently implemented core is Rasterio-independent:

```text
RasterMetadata
RasterAlignmentError
validate_raster_alignment()
validate_named_raster_alignment()
```

`RasterMetadata` contains:

```text
shape       (height, width)
crs         canonical string supplied by an adapter
transform   six affine coefficients
nodata      optional marker
```

For the raster CA line, geometric alignment currently requires compatible:

- shape;
- canonical CRS;
- complete affine transform within an explicit numerical tolerance.

NoData equality is optional because NoData representation and NoData simulation semantics are separate concerns.

The core GIS contract never silently:

- reprojects;
- resamples;
- crops;
- shifts an origin;
- changes CRS.

Those operations belong to explicit preprocessing. Resolution alone is insufficient to establish alignment because two equal-resolution rasters may still have different origins or rotations.

Rasterio remains an optional dependency for the future adapter that converts real datasets to arrays plus `RasterMetadata`. Detailed rules are in [`GIS_DATA_CONTRACT.md`](GIS_DATA_CONTRACT.md).

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

The implemented geometric precondition is:

```text
same spatial shape
+
same canonical CRS
+
same affine transform within declared tolerance
```

The transform check implicitly protects origin, resolution, pixel-axis orientation, rotation/shear, and extent implied by shape + transform. Equal shape/resolution alone does not prove cell-to-cell correspondence.

`validate_raster_alignment()` fails closed with `RasterAlignmentError`; it never attempts to repair the data. `validate_named_raster_alignment()` validates many named inputs against one reference grid and includes the offending layer name in errors.

The default affine coefficient tolerance is an absolute `1e-9` with zero relative tolerance. It exists only for floating-point representation noise and must not be enlarged to accept a real grid shift.

NoData remains a separate semantic contract. The project has not yet decided that every missing fuel/weather cell is automatically `UNBURNABLE`.

A later Rasterio/PROJ adapter may canonicalize equivalent CRS definitions before creating `RasterMetadata`, but the numerical core will not implement a partial CRS parser.

See [`GIS_DATA_CONTRACT.md`](GIS_DATA_CONTRACT.md).

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

A YAML configuration may eventually select:

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
- optimized/reference equivalence tests are required before an optimized path becomes default.

PyTorch/JAX/differentiable CA are explicitly outside the current scope.

## 11. Testing and validation architecture

Four software/scientific levels remain mandatory:

```text
unit        — isolated contracts and invariants
integration — multiple components in one short simulation
regression  — stable reference outputs with fixed seed/config
validation  — comparison with scientific/reference calculations
```

Scientific external values additionally receive evidence grades documented in [`VALIDATION.md`](VALIDATION.md):

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal synthetic/analytical fixture
```

External snapshots are pinned with source revision/provenance and protected from accidental edits. Performance benchmarks live under `benchmarks/`, not correctness tests.

## 12. Reference projects and what is borrowed

The project should learn selectively rather than copy architectures wholesale:

- **Cell2Fire** — cell-based wildfire propagation, distance/ROS concepts, landscape simulation and Monte Carlo;
- **SimFire** — Python simulation API organization and independent behavior comparison;
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
- new raster file format → `gis.py` adapter + GIS tests;
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

### D007 — Standardize behavior outputs, not model-native inputs

Rothermel, FBP, and future behavior models return the same `FireBehaviorResult`, but each model may keep its own typed input dataclass. This avoids a weak oversized input schema while preserving a stable CA-facing boundary.

### D008 — Minimal array-first environmental data contract

The initial data layer uses `SpatialLayer` and `EnvironmentalData` with `(Y, X)` / `(T, Y, X)` arrays and explicit numerical alignment checks. Physical time coordinates and xarray/Zarr abstractions are deferred until a concrete requirement justifies them.

### D009 — GIS alignment precedes file-format adapters

The core GIS contract is a lightweight `RasterMetadata` object independent of Rasterio. Raster layers must agree in shape, canonical CRS, and full affine transform before they enter simulation. GIS preprocessing may transform data; CA simulation may not silently transform its input grid. Rasterio remains an optional adapter dependency.

### D010 — External scientific fixtures require provenance grades

Externally sourced numerical values are not anonymous regression constants. They record evidence grade, source/document or repository, revision/version where applicable, units, and scope. Grade A primary worked values are preferred for interpretation; Grade B official software regression and Grade C independent implementations are used according to documented scope.
