# GIS Raster Data Contract

> Status: active design contract
>
> Updated: 2026-08-12

## 1. Purpose

PyFireCA uses GIS data without allowing GIS file formats to define the numerical CA engine.

Current boundary:

```text
GeoTIFF
  ↓
Rasterio adapter (optional)
  ↓
ndarray + RasterMetadata
  ↓
explicit raster alignment
  ↓
SpatialLayer / EnvironmentalData
  ↓
static NoData → explicit domain mask
  ↓
LandscapeInput
  ↓
RasterGrid + Simulation
  ↓
canonical state GeoTIFF
```

The engine must not discover mid-simulation that inputs use different grids or that missing-data semantics were guessed implicitly.

## 2. `RasterMetadata`

`src/pyfireca/gis.py` defines a lightweight Rasterio-independent object:

```text
shape       (height, width)
crs         canonical non-empty string
transform   (a, b, c, d, e, f)
nodata      optional marker
```

Affine mapping:

```text
x = a * col + b * row + c
y = d * col + e * row + f
```

The CA/data core therefore does not depend on Rasterio/GDAL objects.

## 3. Alignment definition

Two raster layers are geometrically aligned only when these agree:

```text
shape
CRS
all six affine coefficients within an explicit tolerance
```

`validate_raster_alignment()` and `validate_named_raster_alignment()` fail closed. They never reproject, resample, crop, shift, or change CRS.

Default transform comparison:

```text
absolute_tolerance = 1e-9
relative_tolerance = 0
```

This tolerance is for floating-point representation noise only.

## 4. CRS and resolution

Rasterio canonicalizes source CRS before `RasterMetadata` is constructed. The core compares that canonical string exactly rather than implementing a partial CRS parser.

`RasterMetadata.resolution` returns pixel-axis magnitudes:

```text
x_resolution = sqrt(a² + d²)
y_resolution = sqrt(b² + e²)
```

Complete alignment still checks the full affine transform.

## 5. Rasterio adapter

Rasterio remains optional:

```bash
pip install -e ".[gis]"
```

Implemented:

```text
read_raster(path, band=1)
write_raster(path, values, metadata)
write_state_raster(path, state, metadata)
```

`read_raster()` / `write_raster()` preserve stored values, dtype, CRS, transform, and NoData metadata without masking, filling, reprojection, resampling, or unit conversion.

A dedicated GitHub Actions `gis` job installs `.[dev,gis]` and runs generated-GeoTIFF integration tests.

## 6. NoData is metadata before simulation semantics

General rule:

> **NoData does not automatically mean `FireState.UNBURNABLE`.**

`SpatialLayer.nodata` stores an explicit marker. `nodata_mask()` checks only that declared marker:

- sentinels such as `-9999` are supported;
- a declared `NaN` marker is supported;
- arbitrary NaN is not silently classified as NoData when `nodata=None`.

This prevents generic data containers from making domain decisions on behalf of a wildfire model.

## 7. Persistent simulation domain

`build_domain_mask(environment, layer_names)` defines the persistent domain deliberately.

Rules:

1. the caller explicitly names which layers define the domain;
2. those layers must be static `(Y, X)` layers;
3. a cell is valid only when none of the selected layers contains its declared NoData marker;
4. dynamic `(T, Y, X)` layers are rejected as domain-defining layers.

The dynamic-layer restriction prevents one missing weather value from permanently converting a geographic cell into an unburnable cell.

## 8. Dynamic weather completeness policy

PyFireCA now provides an explicit **fail-fast baseline** without imposing interpolation globally:

```python
snapshot = environment.require_complete_snapshot(
    ["wind_speed", "wind_direction", "fuel_moisture"],
    time_index=t,
)
```

This method:

- checks only the explicitly requested required layers;
- rejects declared NoData cells;
- rejects additional non-finite values such as unmarked NaN/Inf;
- reports layer name, time index, and unusable-cell counts;
- does not fill, interpolate, mask, or change the persistent domain.

The ordinary `snapshot()` method remains policy-free.

This establishes a safe default boundary for future WRF/NetCDF integration:

```text
weather preprocessing / interpolation (if explicitly chosen)
        ↓
require_complete_snapshot()
        ↓
fire behavior calculation
```

Interpolation rules are still deferred until a concrete time-coordinate/weather-source integration exists.

## 9. Domain mask → CA state

`state.build_initial_state()` owns state conversion:

```text
domain_mask == False  → UNBURNABLE
domain_mask == True   → UNBURNED
ignition_mask == True → BURNING
```

It requires boolean 2-D masks and rejects ignition outside the valid domain.

Responsibilities therefore remain separate:

```text
GIS/data policy → domain mask
state policy    → initial CA state
```

## 10. `LandscapeInput`

`src/pyfireca/data.py` defines:

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

Convenience assembly:

```python
landscape = LandscapeInput.from_domain_layers(
    environment,
    metadata,
    domain_layer_names=["fuel", "elevation"],
    ignition_mask=ignition,
)
```

One authoritative geospatial metadata object is shared instead of duplicating CRS/transform on every layer.

## 11. Relationship to `RasterGrid`

`LandscapeInput.make_grid()` creates an independent `RasterGrid` from the stored initial state.

`RasterGrid.cell_size` is intentionally left unset because a single scalar cannot safely represent every valid affine grid, including rectangular or rotated pixels.

Geospatial metadata remain with `LandscapeInput`; evolving state remains with `RasterGrid` / `Simulation`.

## 12. State GeoTIFF convention

`write_state_raster()` defines the first model-output format:

```text
dtype          uint8
state codes    0..3
GeoTIFF NoData None
```

`FireState.UNBURNABLE == 0` remains a real model state. It is never reinterpreted as file-level NoData, and source sentinels such as `-9999` are not propagated into state output.

Arrival-time output remains separate and will receive its own convention when arrival time is implemented.

## 13. Current validation coverage

Tests now cover:

- raster shape/CRS/affine validation;
- north-up and rotated resolution;
- alignment mismatch and tolerance behavior;
- Rasterio read/write round trip;
- CRS/affine/NoData/dtype preservation;
- sentinel and NaN NoData masks;
- no implicit NaN→NoData inference;
- static multi-layer domain construction;
- rejection of dynamic domain-defining layers;
- domain/ignition → CA-state conversion;
- ignition-outside-domain rejection;
- `LandscapeInput` shape invariants and independent grid creation;
- fail-fast required dynamic snapshots;
- declared dynamic NoData rejection;
- unmarked non-finite dynamic-value rejection;
- canonical state GeoTIFF dtype/state/NoData behavior.

## 14. Remaining GIS/data work

Not implemented yet:

```text
physical timestamps and temporal interpolation
high-level multi-file landscape loader
explicit preprocessing/reprojection helper
arrival-time output convention
NetCDF/xarray adapter if a concrete weather integration requires it
```

No new abstraction should be added merely to anticipate these items.

## 15. Design rule

**GIS preprocessing may intentionally transform data; CA simulation may not silently transform its grid, invent domain semantics, or repair missing weather.**
