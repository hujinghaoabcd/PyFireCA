# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **D — Rothermel validation gate + GIS landscape input/output foundation**

## Current position

PyFireCA now has a tested wildfire CA reference core, common behavior/data contracts, typed Rothermel inputs and R1 calculations, an explicitly selected Albini-adjusted R2 formulation, provenance-graded scientific fixtures, and a working minimal geospatial input/output path.

```text
GeoTIFF
  ↓
Rasterio adapter
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

Scientific behavior remains deliberately gated before the complete Rothermel ROS chain:

```text
RothermelInputs
      ↓
R1: units + fuel weighting/base quantities      ✓
      ↓
R2: Albini-adjusted no-wind/no-slope ROS
      ↓
external zero-wind + zero-slope fixture         ← unresolved
```

The project will not manufacture an external truth value merely to start R2.

## Completed

### CA reference core

- `FireState` codes `UNBURNABLE / UNBURNED / BURNING / BURNED`;
- state-array validation;
- `RasterGrid`;
- `Neighborhood` protocol;
- Moore and Von Neumann neighborhoods;
- clipped boundaries;
- synchronous `TransitionRule` protocol;
- explicit `numpy.random.Generator`;
- `Simulation.step()` / `run()`;
- deterministic `NeighborIgnitionRule` architectural baseline;
- no-cascade synchronous-update regression test;
- `build_initial_state()` for explicit domain/ignition → CA-state conversion.

### Common behavior/data boundary

- generic `FireBehaviorModel[InputT]`;
- immutable `FireBehaviorResult`;
- common SI-derived spread/intensity/flame-length outputs;
- direction convention clockwise from geographic north;
- `SpatialLayer` supporting `(Y, X)` and `(T, Y, X)`;
- `EnvironmentalData` shared spatial/time-size validation;
- explicit units and NoData metadata;
- no hidden unit conversion, masking, interpolation, or imputation.

### GIS raster contract

Implemented in `src/pyfireca/gis.py`:

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
same six affine coefficients within explicit tolerance
```

Rasterio remains optional via `.[gis]` and has a dedicated CI job.

### NoData and persistent-domain semantics

The generic rule is now executable rather than informal:

> **NoData does not automatically mean `UNBURNABLE`.**

Implemented:

```text
nodata_mask(layer)
build_domain_mask(environment, layer_names)
build_initial_state(domain_mask, ignition_mask)
```

Policy:

- only explicitly selected static layers define the persistent domain;
- declared sentinel or NaN NoData markers are supported;
- arbitrary NaN values are not guessed as NoData when no marker is declared;
- dynamic weather/moisture layers cannot define a permanent domain;
- ignition outside the valid domain is rejected.

### `LandscapeInput`

Implemented in `src/pyfireca/data.py`:

```text
LandscapeInput
├── environment
├── metadata
└── initial_state
```

It enforces:

```text
environment.spatial_shape
== metadata.shape
== initial_state.shape
```

`LandscapeInput.from_domain_layers()` assembles an initial landscape using explicit static-layer NoData semantics. `make_grid()` returns an independent `RasterGrid` copy.

The shared geospatial metadata stay with `LandscapeInput`; evolving state stays with `RasterGrid` / `Simulation`.

### Canonical wildfire-state GeoTIFF output

`write_state_raster()` now defines the first model-output convention:

```text
dtype      uint8
state      canonical codes 0..3
GeoTIFF NoData  None
```

`FireState.UNBURNABLE == 0` remains a real model state and is not reinterpreted as file-level NoData. Source raster NoData markers such as `-9999` are not propagated into a state raster.

### Rothermel R1

Implemented and tested:

```text
SI ↔ published ft/lb/Btu/min conversions
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
```

The six-class public fuel representation is fixed as:

```text
DEAD_1H
DEAD_10H
DEAD_100H
DEAD_HERBACEOUS
LIVE_HERBACEOUS
LIVE_WOODY
```

### R2 reference variant

The reference line is explicitly **Albini-adjusted Rothermel**.

Locked Albini 1976 adjustments include:

1. combustible-loading correction;
2. revised reaction-velocity exponent;
3. revised live moisture of extinction;
4. revised dead/live reaction-intensity combination.

Andrews 2018 is the modern consolidated consistency reference.

### Validation evidence hierarchy

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal analytical/synthetic fixture
```

Pinned fixtures include:

```text
tests/validation/data/albini1976_worked_examples.csv
tests/validation/data/behave7_surface_reference.csv
```

External snapshots have provenance and integrity protection.

## CI state

Latest state-output / landscape code is fully green across:

```text
quality
  Ruff lint
  Ruff format
  pytest + coverage

gis
  .[dev,gis]
  GIS + Rasterio integration tests

Python 3.11
Python 3.12
Python 3.13
```

Latest verified workflow run: `31562196229` for commit `01ec0576e223666d37ceb4bac764b1136244e08a`.

## Key decisions now implemented

1. CA propagation and fire behavior remain separate.
2. Behavior outputs are standardized; model-native inputs remain model-specific.
3. Environmental data remain array-first and lightweight.
4. GIS I/O stays outside numerical CA kernels.
5. Geometric misalignment fails explicitly; simulation never silently reprojects/resamples.
6. NoData remains metadata until a workflow explicitly converts selected static layers into domain semantics.
7. Dynamic missing weather does not become permanent `UNBURNABLE` state.
8. `LandscapeInput` owns shared GIS metadata; `RasterGrid` owns evolving state.
9. State output uses canonical model states rather than file-level NoData.
10. NumPy remains the scientific reference path.
11. Rothermel remains the first behavior reference implementation; FBP follows later.
12. R2 follows the named Albini-adjusted Rothermel line.
13. External validation values carry explicit evidence grades and provenance.

## Not implemented yet

### Immediate scientific work

- dedicated external R2 zero-wind/zero-slope fixture;
- combustible/net fuel loading;
- mineral damping;
- moisture damping;
- live moisture of extinction;
- reaction velocity/intensity;
- propagating flux ratio;
- effective heating number / heat of preignition;
- heat source/sink;
- validated no-wind/no-slope ROS;
- wind/slope behavior;
- complete Rothermel `FireBehaviorResult`.

### GIS/data work

- high-level multi-file landscape loader;
- explicit reprojection/resampling preprocessing helper if needed;
- arrival-time output convention;
- dynamic weather missing-data policy;
- physical weather timestamps/interpolation;
- NetCDF/xarray adapter only when a concrete integration requires it.

### Later CA research

- first behavior-informed CA transition rule;
- probabilistic rules;
- directional/adaptive neighborhoods;
- asynchronous/event-driven scheduling;
- active/sparse updates;
- FBP;
- Cell2Fire-like distance accumulation;
- arrival time;
- crown fire / spotting / suppression;
- Monte Carlo experiments;
- profiling-led Numba optimization.

## Immediate next target

Two independent next paths remain valid:

```text
Scientific:
external zero-wind + zero-slope R2 reference
        ↓
Albini-adjusted pure formula functions
        ↓
validated base ROS
```

```text
GIS/data:
dynamic-weather missing-data semantics
        ↓
arrival-time/output convention
        ↓
high-level multi-file landscape loading only if the concrete workflow needs it
```

Do not start Cell2Fire-like propagation until at least one physical ROS path is independently validated.
