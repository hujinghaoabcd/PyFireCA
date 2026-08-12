# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: continue development without reconstructing scientific or architectural context from chat history.

## 1. Identity and protected scope

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. The primary research target is the CA itself.

Protected extension points:

```text
State
Neighborhood
Transition Rule
Time stepping / scheduler
```

Do not casually reverse these decisions:

1. wildfire-specific scope;
2. NumPy is the scientific reference path;
3. Numba only after profiling;
4. Torch/JAX/GPU/differentiable CA deferred;
5. Level Set/front tracking are comparison methods only;
6. fire behavior and CA propagation remain separate;
7. GIS I/O stays outside numerical kernels;
8. behavior outputs standardized, model-native inputs remain typed/model-specific;
9. Rothermel first, FBP later for Cell2Fire-oriented work;
10. Rothermel public inputs use explicit SI units and midflame wind;
11. R1 remains separate from R2 reaction/heat-transfer equations;
12. R2 is explicitly **Albini-adjusted Rothermel**;
13. external numerical references carry evidence grades and provenance;
14. GIS alignment, domain semantics, and dynamic missing-data handling are explicit rather than inferred.

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

Do not create empty `config.py`, `metrics.py`, `fbp.py`, backend packages, or plugin systems merely to match a future architecture diagram.

## 3. CA core truth

Canonical states:

```text
UNBURNABLE = 0
UNBURNED   = 1
BURNING    = 2
BURNED     = 3
```

Reference transitions are **synchronous**. `TransitionRule.next_state()` reads the complete old state, returns a complete next state, and `Simulation` replaces the grid only after evaluation finishes.

`NeighborIgnitionRule` is architecture-only; it is not physical wildfire behavior.

`build_initial_state(domain_mask, ignition_mask)` maps:

```text
domain False  → UNBURNABLE
domain True   → UNBURNED
ignition True → BURNING
```

and rejects ignition outside the domain.

## 4. Common behavior/data contract

CA-facing behavior output:

```text
spread_rate_m_s            required
spread_direction_deg       optional, [0, 360), clockwise from north
fireline_intensity_w_m     optional
flame_length_m              optional
diagnostics                 optional
```

`SpatialLayer` supports `(Y, X)` and `(T, Y, X)`. `EnvironmentalData` requires one spatial shape and one dynamic time length.

Two snapshot APIs now intentionally have different semantics:

```text
snapshot(...)
    policy-free array access

require_complete_snapshot(required_layers, time_index=...)
    explicit fail-fast gate
```

`require_complete_snapshot()` rejects declared NoData and any additional non-finite values in selected required layers. It does not interpolate, fill, mask, skip time indices, or modify permanent CA state.

Raised exception:

```text
MissingEnvironmentalDataError
```

This is the safe baseline for future dynamic weather integration.

## 5. GIS raster contract — stable baseline

Implemented in `gis.py`:

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
same full affine transform within explicit tolerance
```

No implicit reprojection/resampling/cropping/origin shifts are permitted inside simulation.

Rasterio is optional through:

```bash
pip install -e ".[gis]"
```

and has a dedicated `gis` GitHub Actions job.

## 6. NoData and persistent-domain semantics — fixed

General rule:

> **NoData is metadata until explicitly converted into domain semantics.**

`nodata_mask(layer)` checks only the declared marker:

- numeric sentinels supported;
- declared NaN supported;
- arbitrary NaN is not guessed as NoData when `nodata=None`.

`build_domain_mask(environment, layer_names)`:

- requires explicit layer selection;
- accepts static layers only;
- combines declared NoData locations from those selected layers;
- rejects dynamic layers.

Reason: transient missing wind/moisture must not permanently change a cell to `UNBURNABLE`.

Dynamic missing data instead use the fail-fast required-snapshot gate described above.

## 7. `LandscapeInput` — current geospatial assembly boundary

```text
LandscapeInput
├── environment: EnvironmentalData
├── metadata: RasterMetadata
└── initial_state: integer (Y, X)
```

Invariant:

```text
environment.spatial_shape
== metadata.shape
== initial_state.shape
```

`LandscapeInput.from_domain_layers()` assembles state from explicit static domain layers and optional ignition mask. `make_grid()` returns an independent `RasterGrid` copy.

Ownership remains:

```text
LandscapeInput → shared spatial metadata + initial input
RasterGrid     → evolving CA state
Simulation     → orchestration
```

Do not duplicate CRS/transform on every layer or infer an unsafe scalar cell size from arbitrary affine geometry.

## 8. State GeoTIFF convention — fixed

`write_state_raster()` writes:

```text
dtype          uint8
state codes    0..3
GeoTIFF NoData None
```

`UNBURNABLE=0` is a real model state and is not file-level NoData. Do not propagate input sentinels such as `-9999` into state outputs.

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

Core input fields:

```text
fuel
moisture
midflame_wind_speed_m_s
wind_from_direction_deg
slope_deg
aspect_deg
```

10-m/20-ft wind adjustment remains external.

R1 implemented and tested:

```text
SI ↔ ft/lb/Btu/min conversions
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
```

Do not redesign R1 just to make R2 shorter.

## 10. R2 reference variant and validation gate

Target:

> **Albini-adjusted Rothermel surface fire**

Locked Albini 1976 changes:

1. combustible loading correction;
2. revised reaction-velocity exponent `A = 133 * sigma^-0.7913`;
3. revised live moisture-of-extinction calculation with dead-Mx lower bound;
4. revised dead/live reaction-intensity treatment.

Andrews 2018 is the modern consolidated consistency reference.

Validation grades:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal synthetic/analytical fixture
```

Pinned:

```text
tests/validation/data/albini1976_worked_examples.csv
tests/validation/data/behave7_surface_reference.csv
```

Current scientific gap:

> no precise external **zero-wind + zero-slope** value has yet been locked for the selected Albini-adjusted R2 chain.

Do not fabricate a Grade A fixture from PyFireCA calculations.

Acceptable fallback: run a pinned official Behave 7 build for an exact zero-wind/zero-slope case and record it as Grade B with exact revision/input/output provenance.

## 11. Latest verified CI state

Latest verified run:

```text
workflow 31562488352
commit   b5bdedebe8226d85719d6947a6043db866a579d4
```

Everything passed:

```text
quality: Ruff lint / Ruff format / pytest+coverage  ✓
gis: Rasterio integration                          ✓
Python 3.11                                        ✓
Python 3.12                                        ✓
Python 3.13                                        ✓
```

This baseline includes:

- NoData/domain tests;
- `LandscapeInput` tests;
- canonical state GeoTIFF tests;
- required dynamic snapshot fail-fast tests.

## 12. Exact next work

The GIS/data foundation is now sufficient to **pause**. Do not add xarray, NetCDF, temporal interpolation, high-level loaders, or preprocessing frameworks without a concrete integration.

Return to the R2 scientific gate:

```text
1. Obtain reproducible zero-wind + zero-slope external reference
2. Pin provenance and evidence grade
3. Implement formula-level Albini-adjusted pure functions
4. Assemble and validate base ROS
5. Only then add wind/slope
6. Then expose RothermelModel.compute() → FireBehaviorResult
```

Expected R2 functions after the fixture gate:

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

## 13. Deferred work

Do not pull forward yet:

```text
physical timestamp/interpolation framework
NetCDF/xarray adapter
Cell2Fire-like distance accumulation
FBP
probabilistic/learned CA
crown fire
spotting
suppression
Monte Carlo framework
Numba optimization
Torch/JAX/GPU
```

The first behavior-informed CA rule comes only after a physical ROS path is independently validated.

## 14. Files to read first next session

```text
1. docs/STATUS.md
2. docs/HANDOFF.md
3. docs/ROTHERMEL_REFERENCE.md
4. docs/VALIDATION.md
5. docs/GIS_DATA_CONTRACT.md
6. src/pyfireca/behavior/rothermel.py
7. src/pyfireca/data.py
8. src/pyfireca/gis.py
```

The handoff describes repository truth, not planned work that was never implemented.
