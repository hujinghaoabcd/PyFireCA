# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: continue development without reconstructing scientific or architectural context from chat history.

## 1. Project identity and protected scope

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework** whose primary research target is the CA itself.

Protected CA extension points:

```text
State
Neighborhood
Transition Rule
Time stepping / scheduler
```

Fire behavior and GIS support the CA but do not define the propagation engine.

Do not casually reverse these decisions:

1. wildfire-specific product scope;
2. NumPy is the readable scientific reference path;
3. Numba only after profiling;
4. PyTorch/JAX/GPU/differentiable CA deferred;
5. Level Set/front tracking are comparison methods only;
6. fire behavior and CA propagation remain separate;
7. GIS file I/O stays outside numerical kernels;
8. compact package tree until real complexity justifies splitting;
9. behavior outputs standardized, model-native inputs strongly typed/model-specific;
10. Rothermel first, FBP later for Cell2Fire-oriented comparison;
11. Rothermel public contract uses explicit SI units and midflame wind;
12. R1 base calculations remain separate from R2 reaction/heat-transfer equations;
13. R2 follows a named **Albini-adjusted Rothermel** line;
14. external numerical references carry evidence grades and pinned provenance;
15. GIS alignment and NoData/domain semantics are explicit and never silently repaired/inferred.

## 2. Current source tree

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

Important tests now include:

```text
tests/test_state.py
tests/test_data.py
tests/test_gis.py
tests/test_rasterio_io.py
tests/test_rothermel_inputs.py
tests/test_rothermel_r1.py
tests/validation/
```

Do not create empty `config.py`, `metrics.py`, `fbp.py`, backend packages, or plugin systems merely to match an architecture diagram.

## 3. CA core truth

Canonical state codes:

```text
UNBURNABLE = 0
UNBURNED   = 1
BURNING    = 2
BURNED     = 3
```

Reference transition semantics are **synchronous**:

```text
read complete State(t)
        ↓
compute complete State(t+1)
        ↓
replace state once
```

A regression test guarantees newly ignited cells cannot propagate again in the same step.

`NeighborIgnitionRule` is architecture-only and contains no physical wildfire behavior.

`build_initial_state(domain_mask, ignition_mask)` now owns initial state construction:

```text
domain False  → UNBURNABLE
domain True   → UNBURNED
ignition True → BURNING
```

Ignition outside the domain raises.

## 4. Common behavior/data contract

CA-facing fire-behavior output:

```text
spread_rate_m_s            required
spread_direction_deg       optional, [0, 360), clockwise from north
fireline_intensity_w_m     optional
flame_length_m              optional
diagnostics                 optional
```

`SpatialLayer` supports:

```text
static   (Y, X)
dynamic  (T, Y, X)
```

`EnvironmentalData` requires one spatial shape and one dynamic time length.

No hidden unit conversion, datetime interpolation, masking, or imputation is allowed at this generic boundary.

## 5. GIS raster contract — implemented

`src/pyfireca/gis.py` currently provides:

```text
RasterMetadata
RasterAlignmentError
validate_raster_alignment
validate_named_raster_alignment
read_raster
write_raster
write_state_raster
```

Geometric alignment means:

```text
same shape
same canonical CRS
same full affine transform within explicit tolerance
```

The alignment layer never reprojects, resamples, crops, shifts, or changes CRS.

Rasterio is optional:

```bash
pip install -e ".[gis]"
```

The dedicated `gis` CI job installs `.[dev,gis]` and runs generated-GeoTIFF integration tests.

## 6. NoData / domain policy — now fixed

General rule:

> **NoData is metadata until the workflow explicitly decides how it defines the simulation domain.**

`nodata_mask(layer)` checks only the layer's declared marker:

- numeric sentinels supported;
- declared NaN supported;
- arbitrary NaN is not guessed as NoData when `nodata=None`.

`build_domain_mask(environment, layer_names)`:

- requires explicit layer names;
- only static layers may define the persistent domain;
- combines declared NoData locations across those selected layers;
- rejects dynamic layers.

Reason for rejecting dynamic layers: transient missing wind/moisture must not permanently convert a geographic cell to `UNBURNABLE`.

Dynamic missing-weather handling remains a separate future policy.

## 7. `LandscapeInput` — current geospatial assembly boundary

Implemented in `data.py`:

```text
LandscapeInput
├── environment: EnvironmentalData
├── metadata: RasterMetadata
└── initial_state: integer (Y, X)
```

Required invariant:

```text
environment.spatial_shape
== metadata.shape
== initial_state.shape
```

Convenience assembly:

```python
landscape = LandscapeInput.from_domain_layers(
    environment,
    metadata,
    domain_layer_names=["fuel", "elevation"],
    ignition_mask=ignition,
)
```

`make_grid()` returns an independent `RasterGrid` copy.

Important ownership decision:

```text
LandscapeInput → shared geospatial metadata + immutable-by-convention initial input
RasterGrid     → evolving CA state
Simulation     → orchestration
```

Do not duplicate CRS/transform separately into every layer or infer one scalar `cell_size` from an arbitrary affine transform.

## 8. State GeoTIFF output convention — fixed

`write_state_raster()` writes:

```text
dtype          uint8
state codes    0..3
GeoTIFF NoData None
```

This is deliberate. `UNBURNABLE=0` is a real model state; it is not file-level NoData.

Do not propagate input sentinels such as `-9999` into state outputs.

Arrival-time output conventions remain undecided because arrival time itself is not implemented yet.

## 9. Rothermel input / R1 truth

Fixed six-class order:

```text
DEAD_1H
DEAD_10H
DEAD_100H
DEAD_HERBACEOUS
LIVE_HERBACEOUS
LIVE_WOODY
```

Core input object receives:

```text
fuel
moisture
midflame_wind_speed_m_s
wind_from_direction_deg
slope_deg
aspect_deg
```

10-m / 20-ft wind adjustment stays outside the core Rothermel input contract.

R1 implemented:

```text
SI ↔ ft/lb/Btu/min conversions
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
```

Do not redesign this R1 layer merely to shorten later formulas.

## 10. R2 reference variant and validation gate

Target formulation:

> **Albini-adjusted Rothermel surface fire**

Locked Albini 1976 changes:

1. combustible loading correction;
2. revised reaction-velocity exponent `A = 133 * sigma^-0.7913`;
3. revised live moisture-of-extinction calculation with dead-Mx lower bound;
4. dead and live reaction intensities added using the later operational treatment.

Andrews 2018 is the modern consolidated consistency reference.

Validation grades:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal synthetic/analytical fixture
```

Pinned external fixtures:

```text
tests/validation/data/albini1976_worked_examples.csv
tests/validation/data/behave7_surface_reference.csv
```

Current scientific gap:

> no precise external **zero-wind + zero-slope** numeric fixture has yet been locked for the selected Albini-adjusted R2 chain.

Do not fabricate a Grade A value from PyFireCA's own implementation.

Acceptable fallback: generate a zero-wind/zero-slope case from a pinned official Behave 7 build and label it Grade B with exact build/input/output provenance.

## 11. Latest verified CI state

Workflow run:

```text
31562196229
commit 01ec0576e223666d37ceb4bac764b1136244e08a
```

All jobs passed:

```text
quality
  Ruff lint              ✓
  Ruff format            ✓
  pytest + coverage      ✓

gis                      ✓
Python 3.11              ✓
Python 3.12              ✓
Python 3.13              ✓
```

The state-raster writer and its integration tests are therefore part of the verified green baseline.

## 12. Exact next work

Two lines can proceed independently.

### Scientific line

```text
find/generate pinned external zero-wind + zero-slope reference
        ↓
implement small Albini-adjusted pure functions
        ↓
assemble validated no-wind/no-slope ROS
        ↓
wind/slope
        ↓
RothermelModel.compute() → FireBehaviorResult
```

Expected formula-level functions after the fixture gate:

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

### GIS/data line

Next unresolved semantic problem is **dynamic weather missing data**, not static domain NoData.

Possible policies must be explicit and testable:

```text
fail on missing weather
use previously validated interpolation
explicit masked behavior result
another documented strategy
```

Do not choose one globally until concrete weather integration is available.

After that, consider:

```text
arrival-time output convention
high-level multi-file landscape loader
explicit preprocessing/reprojection helper
physical timestamps/interpolation
NetCDF/xarray only if actually required
```

## 13. Do not pull these forward prematurely

Do not start yet:

```text
Cell2Fire-like distance accumulation
FBP implementation
probabilistic/learned CA
crown fire
spotting
suppression
Monte Carlo framework
Numba optimization
Torch/JAX/GPU
```

The first behavior-informed CA rule should come only after at least one physical ROS path is independently validated.

## 14. Files to read first next session

```text
1. docs/STATUS.md
2. docs/HANDOFF.md
3. docs/SESSION_LOG.md
4. docs/GIS_DATA_CONTRACT.md
5. docs/ROTHERMEL_REFERENCE.md
6. docs/VALIDATION.md
7. src/pyfireca/data.py
8. src/pyfireca/gis.py
9. src/pyfireca/behavior/rothermel.py
```

The handoff describes repository truth, not planned work that was never implemented.
