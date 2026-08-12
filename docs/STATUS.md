# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **D — Rothermel validation gate; GIS/data foundation complete enough to pause**

## Current position

PyFireCA now has four independently tested foundations:

```text
1. Wildfire CA reference core
2. Fire-behavior/data contracts
3. Rothermel R1 + provenance-graded validation infrastructure
4. Minimal geospatial landscape input/output path
```

The GIS/data path is now:

```text
GeoTIFF
  ↓
optional Rasterio adapter
  ↓
RasterMetadata + explicit alignment
  ↓
SpatialLayer / EnvironmentalData
  ↓
explicit static-layer NoData domain policy
  ↓
LandscapeInput
  ↓
RasterGrid + Simulation
  ↓
canonical wildfire-state GeoTIFF
```

Dynamic inputs have an explicit safe baseline:

```text
optional preprocessing/interpolation
        ↓
EnvironmentalData.require_complete_snapshot(...)
        ↓
required layer is complete → continue
missing/non-finite values   → fail explicitly
```

The scientific bottleneck remains Rothermel R2:

```text
RothermelInputs
      ↓
R1: units + heterogeneous-fuel base quantities    ✓
      ↓
R2: Albini-adjusted no-wind/no-slope ROS
      ↓
external zero-wind + zero-slope fixture           ← current scientific gate
```

The project will not manufacture an external truth value merely to begin R2.

## Completed

### CA core

- `FireState`: `UNBURNABLE / UNBURNED / BURNING / BURNED`;
- state-array validation;
- `RasterGrid`;
- Moore and Von Neumann neighborhoods;
- synchronous `TransitionRule` and `Simulation`;
- explicit NumPy RNG;
- deterministic `NeighborIgnitionRule` architectural baseline;
- no-cascade synchronous-update regression test;
- `build_initial_state(domain_mask, ignition_mask)` with rejection of ignition outside the domain.

### Common behavior/data boundary

- `FireBehaviorModel[InputT]`;
- immutable `FireBehaviorResult`;
- common SI-derived output quantities;
- `SpatialLayer` for `(Y, X)` / `(T, Y, X)` arrays;
- `EnvironmentalData` with shared spatial/time-size validation;
- policy-free `snapshot()`;
- `MissingEnvironmentalDataError`;
- `require_complete_snapshot()` for explicit fail-fast validation of selected required inputs.

`require_complete_snapshot()` rejects both declared NoData and additional non-finite values. It does **not** interpolate, fill, mask, skip time indices, or alter the persistent CA domain.

### GIS / landscape foundation

Implemented:

```text
RasterMetadata
RasterAlignmentError
validate_raster_alignment
validate_named_raster_alignment
read_raster
write_raster
write_state_raster
nodata_mask
build_domain_mask
LandscapeInput
```

Geometric alignment requires the same shape, canonical CRS, and complete affine transform within explicit tolerance. Simulation never silently reprojects/resamples.

NoData policy is now explicit:

- NoData does not automatically mean `UNBURNABLE`;
- only caller-selected static layers define the persistent domain;
- declared sentinel and NaN NoData are supported;
- arbitrary NaN is not guessed as NoData when no marker is declared;
- dynamic weather/moisture cannot define permanent `UNBURNABLE` cells.

`LandscapeInput` enforces:

```text
environment.spatial_shape == metadata.shape == initial_state.shape
```

and owns the shared GIS metadata while `RasterGrid` owns evolving state.

### Canonical state GeoTIFF

`write_state_raster()` writes:

```text
dtype          uint8
state codes    0..3
GeoTIFF NoData None
```

`UNBURNABLE=0` is a real model state, not file-level NoData.

### Rothermel R1

Implemented and tested:

```text
SI ↔ ft/lb/Btu/min conversions
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
```

Six-class order is fixed:

```text
DEAD_1H
DEAD_10H
DEAD_100H
DEAD_HERBACEOUS
LIVE_HERBACEOUS
LIVE_WOODY
```

### R2 reference line and validation

R2 is explicitly **Albini-adjusted Rothermel**. Locked Albini 1976 changes include combustible loading, reaction-velocity exponent, live moisture of extinction, and dead/live reaction-intensity treatment. Andrews 2018 is the modern consistency reference.

Validation evidence grades:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal synthetic/analytical fixture
```

Pinned fixtures:

```text
tests/validation/data/albini1976_worked_examples.csv
tests/validation/data/behave7_surface_reference.csv
```

The remaining R2 gap is a precise external **zero-wind + zero-slope** numeric case matching the selected operational formulation.

## CI state

Latest verified workflow:

```text
run    31562488352
commit b5bdedebe8226d85719d6947a6043db866a579d4
```

All jobs passed:

```text
quality: Ruff lint + Ruff format + pytest/coverage   ✓
gis: optional Rasterio integration tests             ✓
Python 3.11                                          ✓
Python 3.12                                          ✓
Python 3.13                                          ✓
```

This green baseline includes the dynamic required-snapshot fail-fast tests.

## Key decisions now implemented

1. CA propagation and fire behavior remain separate.
2. Behavior outputs are standardized; model-native inputs remain model-specific.
3. NumPy remains the readable scientific reference path.
4. GIS file I/O remains outside CA numerical kernels.
5. Misaligned rasters fail explicitly.
6. Static NoData affects the persistent domain only through explicit layer selection.
7. Dynamic missing weather never silently changes permanent CA state.
8. Required dynamic inputs use an explicit fail-fast completeness gate; interpolation remains preprocessing policy.
9. `LandscapeInput` owns shared GIS metadata; `RasterGrid` owns evolving state.
10. State output uses canonical model states rather than file-level NoData.
11. Rothermel remains the first behavior reference implementation; FBP follows later.
12. R2 follows the named Albini-adjusted Rothermel line.
13. External validation values carry evidence grades and pinned provenance.

## Not implemented yet

### Immediate scientific work

- external R2 zero-wind/zero-slope reference;
- combustible/net fuel loading;
- mineral and moisture damping;
- live moisture of extinction;
- reaction velocity/intensity;
- propagating flux ratio;
- effective heating number / heat of preignition;
- heat source/sink;
- validated base ROS;
- wind/slope effects;
- complete Rothermel `FireBehaviorResult`.

### GIS/data work — deliberately deferred

- physical timestamps and temporal interpolation;
- high-level multi-file landscape loader;
- explicit reprojection/resampling preprocessing helper;
- arrival-time output convention;
- NetCDF/xarray adapter only for a concrete weather integration.

The current GIS foundation is sufficient to pause; these items should not displace the R2 scientific validation gate.

### Later CA research

- first behavior-informed CA rule;
- probabilistic/directional/adaptive neighborhoods;
- asynchronous/event-driven scheduling;
- active/sparse updates;
- FBP;
- Cell2Fire-like distance accumulation and arrival time;
- crown fire / spotting / suppression;
- Monte Carlo;
- profiling-led Numba optimization.

## Immediate next target

Return to the scientific line:

```text
pinned external zero-wind + zero-slope R2 reference
        ↓
small Albini-adjusted pure formula functions
        ↓
validated no-wind/no-slope ROS
```

If no suitable Grade A worked value exists, generate a reproducible **Grade B** case from a pinned official Behave 7 build, record the exact build/input/output provenance, and keep it explicitly labeled Grade B.

Do not begin Cell2Fire-like physical propagation until at least one physical ROS path is independently validated.
