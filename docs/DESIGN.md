# PyFireCA Design Document

> Status: living design document
>
> Scope: architecture and scientific-software boundaries for the `v0.1.x` development line.

## 1. Purpose

PyFireCA is a wildfire cellular-automata research framework designed so the **CA itself** can be studied and modified without coupling CA changes to GIS I/O, fire-behavior equations, experiment scripts, or visualization code.

The project is not a generic urban/geospatial CA framework. Other CA/GIS projects may inform engineering patterns, but wildfire simulation remains the supported domain.

## 2. Core principles

1. **CA mechanisms are explicit:** State, Neighborhood, TransitionRule, and scheduler/time stepping are visible extension points.
2. **Fire behavior is separate from propagation:** behavior computes ROS/intensity/etc.; CA rules decide how those quantities change cells.
3. **Reference implementation first:** readable NumPy before profiling-led optimization.
4. **GIS is an adapter/data boundary:** numerical kernels do not depend on paths, GDAL objects, or silent reprojection/resampling.
5. **Missing-data semantics are explicit:** file NoData, persistent simulation domain, and transient missing weather are different concepts.
6. **Reproducibility is part of the API:** randomness uses explicit `numpy.random.Generator`; external scientific fixtures carry provenance.
7. **No premature platform architecture:** no plugin/backend/distributed/service framework without a demonstrated need.
8. **Documentation tracks repository truth:** design, validation, status, handoff, and changelog evolve with code.

## 3. Conceptual architecture

```text
GIS / external data
        ↓
RasterMetadata + aligned arrays
        ↓
EnvironmentalData + LandscapeInput
        ↓
FireBehaviorModel ───────────────┐
        ↓                        │
FireBehaviorResult               │
        ↓                        │
TransitionRule ← Neighborhood ← RasterGrid/State
        ↓
Simulation / scheduler
        ↓
state / future arrival-time outputs
```

The simulation orchestrator must never contain model-family branches such as `if behavior == "rothermel"` or `if neighborhood == "moore"`.

## 4. Current implemented package

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
└── behavior/
    ├── __init__.py
    ├── base.py
    ├── _units.py
    └── rothermel.py
```

Do not create empty `config.py`, `metrics.py`, `fbp.py`, backend packages, or plugin systems merely to make the tree look complete.

## 5. Component responsibilities

### 5.1 `state.py`

Owns canonical wildfire states and state-level invariants.

```text
UNBURNABLE = 0
UNBURNED   = 1
BURNING    = 2
BURNED     = 3
```

`build_initial_state(domain_mask, ignition_mask)` converts explicit domain/ignition semantics to canonical state. It does not inspect GIS files or infer NoData meaning.

### 5.2 `grid.py`

`RasterGrid` owns the evolving CA state array and grid-shape contract. It does not read files or compute fire behavior.

A scalar `cell_size` remains optional and is not inferred automatically from arbitrary affine metadata because rotated/rectangular pixels may not have one safe scalar representation.

### 5.3 `neighborhood.py`

Owns interaction geometry. Moore and Von Neumann neighborhoods are implemented. Future research may add directional, weighted, adaptive, anisotropic, radius-based, or multi-scale neighborhoods without modifying `Simulation`.

Avoid millions of Python `Cell` objects; cells are array locations.

### 5.4 `rules.py`

Owns CA transition mechanics and is the primary algorithm-research extension point.

Planned rule families include deterministic, probabilistic, and Cell2Fire-like distance accumulation. Rules may consume state, neighborhood, environmental data, fire-behavior outputs, time, and RNG, but never perform GIS file I/O.

### 5.5 `simulation.py`

Owns orchestration only:

```text
initialize → step → run → stop
```

The current reference engine is synchronous: the full old state is read before the complete new state is applied. Newly ignited cells therefore cannot propagate again in the same step.

### 5.6 `behavior/`

Owns wildfire behavior calculations, not CA propagation.

Stable CA-facing output:

```text
spread_rate_m_s            required
spread_direction_deg       optional, clockwise from north in [0, 360)
fireline_intensity_w_m     optional
flame_length_m              optional
diagnostics                 optional
```

Behavior-model inputs remain model-specific and strongly typed.

Initial scientific sequence:

```text
Albini-adjusted Rothermel reference
        ↓
validated FireBehaviorResult
        ↓
later FBP for Cell2Fire-oriented comparisons
```

### 5.7 `data.py`

Owns array-first environmental and landscape assembly.

```text
SpatialLayer
EnvironmentalData
LandscapeInput
MissingEnvironmentalDataError
nodata_mask
build_domain_mask
```

`SpatialLayer` supports static `(Y, X)` and dynamic `(T, Y, X)` data with optional explicit units/NoData metadata.

`EnvironmentalData.snapshot()` is intentionally policy-free.

`EnvironmentalData.require_complete_snapshot()` is the explicit fail-fast path for calculations requiring complete selected inputs. It rejects declared NoData and additional non-finite values but never interpolates, fills, masks, skips time steps, or changes the permanent domain.

`LandscapeInput` owns one shared `RasterMetadata`, aligned environmental arrays, and initial state; it can create an independent evolving `RasterGrid`.

### 5.8 `gis.py`

Owns the lightweight raster contract plus optional Rasterio I/O.

Implemented:

```text
RasterMetadata
RasterAlignmentError
validate_raster_alignment
validate_named_raster_alignment
read_raster
write_raster
write_state_raster
```

Rasterio is optional. Importing the CA core does not require it.

Geometric alignment requires:

```text
same shape
same canonical CRS
same complete affine transform within explicit tolerance
```

The GIS layer never silently reprojects, resamples, crops, shifts, or changes CRS.

## 6. Data representation

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

This supports readable NumPy now and possible Numba later.

## 7. GIS and NoData semantics

Three concepts must remain distinct.

### 7.1 Geometric alignment

Before simulation, raster data must describe the same cells. Shape + CRS + full affine transform are checked explicitly. Equal resolution alone is insufficient.

### 7.2 Persistent domain

NoData does **not** automatically mean `UNBURNABLE`.

The persistent domain is built only from caller-selected static layers:

```text
selected static layer declared NoData
        ↓
invalid domain cell
        ↓
UNBURNABLE during initial state construction
```

Dynamic layers cannot define permanent domain state.

### 7.3 Transient missing environmental inputs

When a calculation requires complete dynamic weather/moisture, it calls:

```text
require_complete_snapshot(required_layers, time_index)
```

Missing/non-finite required data cause an explicit error. If interpolation is later supported, interpolation belongs to a documented preprocessing/data-integration step before this completeness gate.

## 8. Output semantics

The canonical state GeoTIFF uses:

```text
dtype          uint8
state codes    0..3
file NoData    None
```

`UNBURNABLE=0` is a real model state and must not be confused with file NoData.

Arrival-time output will receive a separate convention only when arrival-time state is implemented.

## 9. Rothermel scientific boundary

The first reference line is **Albini-adjusted Rothermel**.

The public fuel representation uses six fixed classes and SI-facing inputs. Legacy ft/lb/Btu/min conversion is centralized in `_units.py`.

R1 currently contains only independently testable base quantities. R2 reaction/heat-transfer functions are blocked until a reproducible external zero-wind/zero-slope validation fixture is pinned.

External numerical evidence grades are:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal synthetic/analytical fixture
```

Do not weaken tolerances or mix equation variants to force agreement.

## 10. Randomness and reproducibility

Use:

```python
rng = np.random.default_rng(seed)
```

Do not use global RNG state as model state. Future Monte Carlo execution must define independent stream generation explicitly.

Reproducible runs should eventually record package version, Git commit, seed strategy, configuration, input identity/hash where practical, and backend/runtime information.

## 11. Performance policy

```text
readable NumPy reference
        ↓
correctness + validation
        ↓
profiling
        ↓
Numba only for measured hotspots
        ↓
other acceleration only if still justified
```

The NumPy path remains available for equivalence testing after optimization.

## 12. Testing architecture

```text
unit        isolated contracts and equations
integration multiple components in small scenarios
regression  stable outputs under fixed configuration/seed
validation  scientific/reference comparisons
```

Performance benchmarks live outside correctness tests.

Optional GIS dependencies have their own CI job in addition to Python 3.11/3.12/3.13 and quality jobs.

## 13. Reference-project usage

- **Cell2Fire** — cell-based propagation, ROS/distance concepts, landscape Monte Carlo.
- **SimFire** — Python organization and independent Rothermel comparison.
- **GridFire** — raster/Monte Carlo organization and richer wildfire concerns.
- **Pyretechnics** — modular behavior/data organization and independent numerical comparison; its Level Set engine is not adopted.
- **ELMFIRE / ForeFire** — non-CA comparison baselines.
- Urban/GIS CA projects — GIS preprocessing and software-engineering lessons only.

Reference code is not copied blindly; published equations and independently documented interpretations define scientific implementation.

## 14. Explicit non-goals for `v0.1.x`

- generic urban CA;
- differentiable CA;
- Torch/JAX backend;
- GPU acceleration;
- Level Set/front tracking as propagation engine;
- CFD/fire-atmosphere coupling;
- plugin ecosystem;
- REST/Web/database platform;
- distributed execution.

## 15. Design decisions log

### D001 — Wildfire-specific scope
PyFireCA is a wildfire CA framework; urban CA projects are engineering references only.

### D002 — Compact module layout
Create modules when a real milestone needs them, not for hypothetical completeness.

### D003 — NumPy scientific reference
Implement and validate readable NumPy first; optimize only after profiling.

### D004 — Fire behavior separate from CA propagation
Behavior equations and transition mechanics remain independently replaceable.

### D005 — Explicit GIS metadata/alignment
Simulation never silently repairs incompatible geospatial inputs.

### D006 — Development documentation is mandatory
Design/status/handoff/validation documentation tracks meaningful architecture/science changes.

### D007 — Standardize outputs, not model-native inputs
Behavior families share `FireBehaviorResult`; their inputs remain model-specific.

### D008 — Minimal array-first environmental data
Use `(Y,X)` / `(T,Y,X)` arrays and defer heavy time/xarray abstractions until concrete integration requires them.

### D009 — GIS alignment precedes file transformation
Shape, canonical CRS, and full affine transform are validated before simulation. Reprojection/resampling belongs to explicit preprocessing.

### D010 — External scientific fixtures require provenance grades
Reference values record source, revision/version, units, formulation scope, and evidence grade.

### D011 — NoData and persistent domain are separate
A NoData marker becomes permanent domain exclusion only when the caller explicitly selects that static layer as domain-defining. Dynamic NoData never silently creates `UNBURNABLE` state.

### D012 — Required dynamic inputs fail fast by default
`require_complete_snapshot()` validates explicitly required data and raises on declared NoData or non-finite values. Automatic repair/interpolation is not a hidden model behavior.

### D013 — State output is complete model state, not masked source data
State GeoTIFFs use canonical `uint8` state codes with no file-level NoData. `UNBURNABLE=0` remains a modeled state.

## 16. Immediate architecture priority

The GIS/data foundation is now sufficient. Do not expand it merely because extension points exist.

Immediate work returns to the Rothermel R2 validation gate:

```text
external zero-wind + zero-slope reference
        ↓
Albini-adjusted formula-level functions
        ↓
validated base ROS
```

Only after a physical ROS path is independently validated should behavior-informed CA propagation begin.
