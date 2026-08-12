# PyFireCA Design Document

> Status: living design document
>
> Updated: 2026-08-13
>
> Scope: architecture and scientific-software boundaries for the first static simulator line.

## 1. Purpose

PyFireCA is a wildfire cellular-automata and raster-spread research framework designed so the **CA/propagation formulation itself** can be studied without coupling method changes to GIS I/O, fire-behavior equations, configuration, or experiment scripts.

The project is not a generic urban/geospatial CA framework. Other CA/GIS projects may inform engineering patterns, but wildfire simulation remains the supported domain.

The first user-facing baseline is intentionally narrow:

```text
static weather
north-up square metric rasters
Albini-adjusted Rothermel
Behave/Catchpole directional surface spread
static physical earliest-arrival propagation
```

New PyFireCA-specific CA innovations are currently deferred until this baseline is frozen.

## 2. Core principles

1. **CA/propagation mechanisms are explicit.** State, neighborhood, transition/update semantics, arrival propagation, and future schedulers are visible components.
2. **Fire behavior is separate from propagation.** Behavior computes ROS and related quantities; propagation converts those quantities into spatial/time evolution.
3. **Reference implementation first.** Readable NumPy before profiling-led acceleration.
4. **GIS is an adapter/data boundary.** Numerical kernels do not depend on file paths, GDAL objects, or silent reprojection/resampling.
5. **Missing-data semantics are explicit.** File NoData, persistent simulation domain, and transient missing environmental inputs are different concepts.
6. **Physical units and directions are explicit.** Midflame wind, moisture fractions, slope degrees, meteorological wind-from bearings, and geographic spread bearings are not interchangeable.
7. **Reproducibility is part of the workflow.** Input hashes, resolved configuration, scientific provenance, and runtime environment are recorded for file-based runs.
8. **No premature platform architecture.** No plugin/backend/distributed/service framework without a demonstrated requirement.
9. **Research variants must be named.** Alternative neighborhoods or interface-coupling rules may not silently change the baseline.
10. **Documentation tracks repository truth.** Design, validation, status, handoff, changelog, and release checklist evolve with code.

## 3. Current architecture

### 3.1 User/file workflow

```text
YAML configuration
        ↓
config.py
        ↓
GeoTIFFs → gis.py
        ↓
EnvironmentalData + LandscapeInput
        ↓
workflow.py
        ↓
StaticWildfireSimulationRequest
        ↓
validated fire behavior + physical propagation
        ↓
StaticWildfireSimulationResult
        ↓
outputs.py
        ↓
GeoTIFF / GeoJSON / metadata / metrics / log
```

### 3.2 Scientific path

```text
per-cell environmental inputs
        ↓
RothermelInputs
        ↓
RothermelModel
        ↓
head/max spread + effective wind/direction
        ↓
Behave/Catchpole surface ellipse
        ↓
direction-specific outgoing ROS
        ↓
physical edge distance / ROS
        ↓
StaticArrivalTimeSolver
        ↓
earliest arrival field
        ↓
state snapshots / terminal footprint
```

Configuration/CLI/workflow layers assemble this same path. They do not implement a second fire model.

## 4. Current package responsibilities

```text
src/pyfireca/
├── __init__.py
├── state.py
├── grid.py
├── neighborhood.py
├── rules.py
├── simulation.py
├── propagation.py
├── arrival.py
├── data.py
├── gis.py
├── ignition.py
├── simulator.py
├── outputs.py
├── config.py
├── workflow.py
├── cli.py
└── behavior/
    ├── base.py
    ├── fuel_catalog.py
    ├── rothermel.py
    ├── rothermel_model.py
    ├── rothermel_layers.py
    ├── rothermel_landscape.py
    ├── rothermel_spatial.py
    ├── rothermel_directional.py
    ├── _surface_ellipse.py
    ├── _rothermel_base.py
    ├── _rothermel_dynamic.py
    ├── _rothermel_effects.py
    ├── _rothermel_vectors.py
    ├── _rothermel_equations.py
    ├── _directions.py
    └── _units.py
```

Do not create empty future modules merely to match an architecture diagram.

## 5. Component responsibilities

### 5.1 `state.py`

Owns canonical wildfire states:

```text
UNBURNABLE = 0
UNBURNED   = 1
BURNING    = 2
BURNED     = 3
```

`UNBURNABLE` is a real model state, not file NoData.

### 5.2 `grid.py`

`RasterGrid` owns evolving synchronous-CA state and basic raster-grid state invariants. It does not read GIS files or compute fire behavior.

### 5.3 `neighborhood.py`

Owns discrete interaction geometry. Moore and Von Neumann neighborhoods are available.

Important distinction:

- the generic/synchronous architecture may use broader neighborhood concepts;
- the current **physical arrival baseline** only accepts immediate-neighbor edges so a long jump cannot silently skip an intermediate barrier.

Extended/adaptive/directional neighborhood methods remain post-baseline research work.

### 5.4 `rules.py` / `simulation.py`

Own the synchronous CA architecture reference.

Current synchronous semantics:

```text
State(t)
→ rule reads complete old state
→ compute State(t+1)
→ replace once
```

One synchronous step has **no hidden physical duration**. This path is not silently substituted for the physical arrival solver.

### 5.5 `behavior/`

Owns fire-behavior calculations, not GIS or arrival scheduling.

Current reference line:

> **Albini-adjusted Rothermel surface fire behavior.**

Validated behavior includes:

```text
base spread
wind factor
slope factor
wind/slope vector composition
optional operational wind limit
dynamic herbaceous curing
surface ellipse
FromIgnitionPoint off-axis radial spread
```

Stable common output emphasizes:

```text
spread_rate_m_s
spread_direction_deg
```

Fireline intensity/flame length remain outside the validated baseline public simulator output until separately verified.

### 5.6 `fuel_catalog.py`

Owns audited standard fuel records and explicit conversion to the PyFireCA SI fuel contract.

Current audited baseline:

```text
Anderson FM1–FM13
Scott–Burgan GR1 (101)
```

Records retain pinned USFS Fire Lab Behave provenance. Unknown/unaudited codes fail explicitly.

### 5.7 `data.py`

Owns array-first environmental and landscape assembly:

```text
SpatialLayer
EnvironmentalData
LandscapeInput
MissingEnvironmentalDataError
nodata_mask
build_domain_mask
```

`SpatialLayer` supports static `(Y, X)` and dynamic `(T, Y, X)` arrays, but the current user-facing simulator intentionally accepts static raster inputs only.

### 5.8 `gis.py`

Owns lightweight raster metadata/alignment plus optional Rasterio I/O.

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

Geometric alignment requires:

```text
same shape
same canonical CRS
same complete affine transform
```

The baseline physical landscape factory additionally requires:

```text
north-up grid
square pixels
positive x / negative y pixel directions
explicit cell_size_m
cell_size_m consistent with affine pixel magnitude
```

The simulator never silently reprojects, resamples, shifts, rotates, or crops inputs.

### 5.9 `propagation.py` / `arrival.py`

Own physical edge geometry/time and static earliest-arrival propagation.

Contract:

```text
edge_travel_time = physical_edge_distance / direction_specific_ROS
```

`StaticArrivalTimeSolver` is Dijkstra-style and assumes static, non-negative edge travel times.

This assumption is why dynamic weather cannot be faked by mutating cached inputs during a solve.

### 5.10 `ignition.py`

Owns user ignition events and conversion to an arrival-time seed field.

Supported:

```text
single ignition
multiple simultaneous ignition
delayed ignition
duplicate events → earliest time wins
```

### 5.11 `simulator.py`

Owns the first complete in-memory user-facing static simulator assembly.

It does not reimplement Rothermel or arrival logic.

### 5.12 `config.py`

Owns strict versioned YAML configuration.

Version 1 exposes only baseline options. Research variants are intentionally absent.

### 5.13 `workflow.py`

Owns file-based orchestration:

```text
load rasters
validate
assemble request
run
write reproducibility artifacts
```

It records input SHA-256 and fuel-catalogue provenance.

### 5.14 `outputs.py`

Owns spatial result serialization:

```text
arrival_time.tif
state.tif
burned_mask.tif
perimeter.geojson
```

Run-level metadata/metrics remain in the run root rather than being duplicated under spatial outputs.

### 5.15 `cli.py`

Owns command parsing/error presentation only:

```bash
pyfireca validate config.yml
pyfireca run config.yml
```

CLI uses `argparse` and delegates to config/workflow APIs.

## 6. Data representation

Prefer structure-of-arrays:

```text
state       [Y, X]
fuel        [Y, X]
slope       [Y, X]
aspect      [Y, X]
wind_speed  [Y, X]        current static baseline
wind_dir    [Y, X]
moisture    [Y, X]
```

The generic data layer may represent `(T,Y,X)` fields for future work, but dynamic scheduling is not implemented by the baseline simulator.

Avoid millions of Python `Cell` objects.

## 7. GIS and NoData semantics

Three concepts remain separate.

### 7.1 Geometric alignment

Shape + CRS + full affine transform identify the same raster cells. Equal resolution alone is insufficient.

### 7.2 Persistent domain

The baseline file workflow uses the `fuel_model` layer's declared NoData mask to define domain exclusion.

```text
fuel-model NoData
→ outside simulation domain
→ UNBURNABLE terminal state
```

### 7.3 Required behavior data

Other required behavior layers may contain NoData outside the domain.

NoData or non-finite required behavior values **inside** the domain fail validation.

There is no hidden interpolation or imputation.

## 8. Output semantics

### Arrival

```text
arrival_time.tif
float64
seconds
-1 file NoData for cells with no finite arrival
```

### Terminal state

```text
state.tif
uint8
0 UNBURNABLE
1 in-domain UNBURNED/unreachable
3 BURNED/reachable
file NoData = None
```

Physical-time snapshots including `BURNING` are generated programmatically through `result.state_at(...)`.

### Burned footprint

```text
burned_mask.tif
uint8 0/1
```

### Perimeter

```text
perimeter.geojson
```

The footprint is polygonized in source CRS and transformed to EPSG:4326 before GeoJSON serialization.

## 9. Rothermel scientific boundary

The selected operational reference is **Albini-adjusted Rothermel**.

R1–R5 and directional surface spread are now implemented and protected by external/pinned regression tests.

Evidence grades:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal synthetic/analytical fixture
```

Pinned operational Behave references remain part of CI/validation provenance.

Do not weaken tolerances or mix equation variants to force agreement.

## 10. Heterogeneous edge semantics

Current baseline:

> **The source cell determines outgoing edge ROS.**

This is a named modeling assumption, not a universal truth.

Alternative hypotheses such as source/target averaging, half-cell travel, interface resistance, or adaptive coupling must be implemented and evaluated as explicit research variants after baseline freeze.

They must not invisibly alter the default CLI behavior.

## 11. Dynamic weather boundary

`StaticArrivalTimeSolver` assumes edge travel time is invariant during traversal.

Time-varying wind/moisture violates that assumption.

Therefore future dynamic weather requires an explicitly designed scheduler/event model. Do not make the static provider mutable during an active Dijkstra solve and call that dynamic weather support.

WRF/NetCDF/xarray coupling belongs after that scheduler contract is designed.

## 12. Randomness and reproducibility

Current baseline propagation is deterministic for fixed inputs/ignitions.

Where randomness is used in synchronous/research paths:

```python
rng = np.random.default_rng(seed)
```

No global RNG state should become hidden model state.

File-based static runs currently record:

```text
resolved configuration
input SHA-256
raster geometry
ignition events
fuel-catalogue source revision
PyFireCA version
Python version
platform
Git commit when supplied by environment
runtime metrics
```

Future Monte Carlo work must define independent stream/seed-generation strategy explicitly.

## 13. Performance policy

```text
readable NumPy reference
→ correctness + validation
→ profiling
→ Numba only for measured hotspots
→ other acceleration only if justified
```

The reference path must remain available for equivalence testing.

## 14. Testing architecture

```text
unit        contracts/equations
integration multiple components
regression  pinned stable outputs
validation  external scientific comparisons
GIS         real raster read/write + full file workflow
package     build + clean-install + CLI/extra smoke
```

Current CI covers Python 3.11/3.12/3.13, GIS integration, Ruff quality gates, and clean built-package installation.

## 15. Reference-project usage

- **Cell2Fire** — cell propagation/distance ideas and landscape simulation comparisons.
- **SimFire** — Python organization and independent behavior comparison.
- **GridFire** — raster workflow/Monte Carlo/richer wildfire-process reference.
- **Pyretechnics** — modular behavior/data and independent numerical comparison.
- **ELMFIRE / ForeFire** — non-CA comparison baselines.
- Urban/GIS CA projects — engineering and GIS lessons only.

Reference software does not define PyFireCA by copy/paste; scientific interpretation and validation provenance remain explicit.

## 16. Explicit non-goals for the first static baseline

```text
generic urban CA
full Scott–Burgan 40 catalogue
dynamic weather / WRF
affine-aware rotated/non-square grids
FBP
crown fire
spotting
suppression
Monte Carlo
fireline intensity/flame length public output
Numba optimization
Torch/JAX/GPU/differentiable CA
plugin ecosystem
REST/Web/database platform
distributed execution
new PyFireCA-specific CA innovation
```

## 17. Design decisions log

### D001 — wildfire-specific scope
PyFireCA is a wildfire CA/raster-spread framework; urban CA projects are engineering references only.

### D002 — compact module growth
Create modules only when an implemented responsibility requires them.

### D003 — NumPy scientific reference
Implement/validate readable NumPy first; optimize after profiling.

### D004 — fire behavior separate from propagation
Behavior and propagation remain independently testable/replaceable.

### D005 — explicit GIS metadata/alignment
Simulation never silently repairs incompatible geospatial inputs.

### D006 — development documentation is mandatory
Design/status/handoff/validation/release docs track meaningful architecture/science changes.

### D007 — standardize common outputs, not model-native inputs
Behavior families may retain typed native inputs while crossing the CA boundary through common physical quantities.

### D008 — array-first environmental data
Use arrays and defer heavy temporal/storage abstractions until required.

### D009 — GIS transformation is preprocessing, not hidden simulation behavior
Reprojection/resampling/cropping must be explicit.

### D010 — external scientific fixtures require provenance grades
Reference values record source/version/revision/units/formulation scope.

### D011 — NoData and domain are separate concepts
Only explicit static domain-defining semantics produce permanent `UNBURNABLE` cells.

### D012 — required inputs fail fast
Missing/non-finite required behavior inputs are errors, not silently filled values.

### D013 — model state is not file NoData
State rasters use canonical state codes.

### D014 — physical time is explicit
Synchronous CA step count is not physical time; physical propagation uses edge travel time and earliest arrival.

### D015 — direction-specific surface spread
Head ROS is never assigned to every neighbor; off-axis ROS uses the validated ignition-point ellipse.

### D016 — current heterogeneous edge baseline is source controlled
Interface coupling alternatives are explicit future hypotheses.

### D017 — static arrival is not dynamic weather
Dynamic forcing requires a separately designed scheduler.

### D018 — baseline CLI excludes research switches
New research variants must not appear as undocumented default options.

### D019 — reproducible file runs are first-class
Resolved config, input hashes, provenance, environment, metrics, and stable spatial output semantics are part of the user workflow.

## 18. Immediate architecture priority

No new architecture is currently needed.

Immediate work is release-readiness:

```text
package metadata audit
license decision
stale-doc search
all-green release-candidate CI
release checklist
baseline tag/freeze
```

Only after that should the project return to the research directions in `docs/FUTURE_RESEARCH.md`.
