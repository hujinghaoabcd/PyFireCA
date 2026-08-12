# GIS Raster Data Contract

> Status: active design contract
>
> Updated: 2026-08-12

## 1. Purpose

PyFireCA uses GIS data without allowing GIS file formats to define the numerical CA engine.

The current boundary is:

```text
GeoTIFF
  ↓
Rasterio adapter (optional dependency)
  ↓
ndarray + RasterMetadata
  ↓
explicit raster alignment
  ↓
SpatialLayer / EnvironmentalData
  ↓
explicit domain-mask semantics
  ↓
LandscapeInput
  ↓
RasterGrid + CA simulation
```

The engine must never discover during a simulation that two inputs use different grids or that NoData semantics were guessed implicitly.

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

The CA/core data modules therefore do not need Rasterio/GDAL objects.

## 3. Alignment definition

Two raster layers are geometrically aligned only when these agree:

```text
shape
CRS
six affine coefficients within an explicit tolerance
```

`validate_raster_alignment()` and `validate_named_raster_alignment()` fail closed. They never reproject, resample, crop, shift, or change CRS.

Equal shape and nominal resolution alone are insufficient because two rasters can be offset by part of a cell while reporting the same pixel size.

Default transform comparison uses:

```text
absolute_tolerance = 1e-9
relative_tolerance = 0
```

This tolerance is only for floating-point serialization noise.

## 4. CRS and resolution

Rasterio canonicalizes source CRS before `RasterMetadata` is constructed. The lightweight core compares that canonical string exactly rather than implementing its own CRS parser.

`RasterMetadata.resolution` returns pixel-axis vector magnitudes:

```text
x_resolution = sqrt(a² + d²)
y_resolution = sqrt(b² + e²)
```

This also works for rotated transforms, but complete alignment still uses all six affine coefficients.

## 5. Rasterio adapter

Rasterio remains an optional dependency:

```bash
pip install -e ".[gis]"
```

Implemented adapter functions:

```text
read_raster(path, band=1)
    → ndarray + RasterMetadata

write_raster(path, values, metadata)
    → one-band GeoTIFF
```

The adapter preserves source values, dtype, CRS, transform, and NoData metadata. It does not mask, fill, reproject, resample, or change units.

An independent GitHub Actions `gis` job installs the optional dependency and executes generated-GeoTIFF integration tests.

## 6. NoData is metadata before it is simulation semantics

The generic rule is:

> **NoData does not automatically mean `FireState.UNBURNABLE`.**

`SpatialLayer.nodata` stores an explicit marker. `nodata_mask()` checks only that declared marker:

- sentinel values such as `-9999` are supported;
- a declared `NaN` marker is supported;
- arbitrary NaN values are **not** silently treated as NoData when `nodata=None`.

This prevents generic data containers from making domain/science decisions on behalf of a model.

## 7. Persistent simulation domain

`build_domain_mask(environment, layer_names)` defines the initial persistent domain deliberately.

Rules:

1. the caller explicitly names which layers define the domain;
2. those layers must be static `(Y, X)` layers;
3. a cell is valid only when none of the selected layers contains its declared NoData value;
4. dynamic `(T, Y, X)` weather/moisture layers are rejected as domain-defining layers.

The dynamic-layer restriction is important. Missing wind at one time index must not silently convert a geographic cell into a permanently unburnable location.

Dynamic missing-data handling remains a separate future weather-data policy (failure, interpolation, masking, or another explicit strategy).

## 8. Domain mask → CA state

`state.build_initial_state()` owns the state-level conversion:

```text
domain_mask == False  → UNBURNABLE
domain_mask == True   → UNBURNED
ignition_mask == True → BURNING
```

The function requires boolean two-dimensional masks and rejects ignition outside the valid domain.

It does **not** inspect GIS NoData itself. This keeps the responsibilities separated:

```text
GIS/data policy → domain mask
state policy    → initial CA state
```

## 9. `LandscapeInput`

`src/pyfireca/data.py` now defines the first user-facing landscape assembly object:

```text
LandscapeInput
├── environment: EnvironmentalData
├── metadata: RasterMetadata
└── initial_state: integer (Y, X) array
```

Construction validates:

```text
environment.spatial_shape
== metadata.shape
== initial_state.shape
```

Convenience constructor:

```python
landscape = LandscapeInput.from_domain_layers(
    environment,
    metadata,
    domain_layer_names=["fuel", "elevation"],
    ignition_mask=ignition,
)
```

The result has one authoritative geospatial metadata object instead of duplicating CRS/transform on every environmental layer.

## 10. Relationship to `RasterGrid`

`LandscapeInput.make_grid()` creates an independent `RasterGrid` from the stored initial state.

It deliberately leaves `RasterGrid.cell_size=None`. A scalar cell size cannot represent every valid affine grid (for example rectangular or rotated pixels), so PyFireCA does not infer one from GIS metadata prematurely.

The geospatial metadata remain owned by `LandscapeInput`; evolving CA state remains owned by `RasterGrid`/`Simulation`.

## 11. Current validation coverage

Core GIS/data tests now cover:

- positive raster dimensions;
- CRS and finite affine validation;
- rotated/north-up resolution;
- shape/CRS/transform mismatch rejection;
- explicit transform tolerance;
- optional NoData equality during geometric checks;
- Rasterio read/write round trip;
- CRS, affine, NoData and dtype preservation;
- explicit sentinel and NaN NoData masks;
- no implicit NaN inference without a marker;
- multi-layer persistent domain construction;
- rejection of dynamic domain-defining layers;
- domain/ignition → canonical fire-state mapping;
- rejection of ignition outside domain;
- `LandscapeInput` shape consistency;
- independent `RasterGrid` creation.

The latest implementation commit is green in the quality, GIS, and Python 3.11/3.12/3.13 CI jobs.

## 12. Remaining GIS/data work

Not implemented yet:

```text
multi-file landscape loader
explicit preprocessing/reprojection helper
GeoTIFF convention for state / arrival-time outputs
dynamic weather missing-data policy
physical timestamps and temporal interpolation
NetCDF/xarray adapter if a concrete weather integration requires it
```

No new abstraction should be added merely to anticipate these items.

## 13. Design rule

**GIS preprocessing may intentionally transform data; CA simulation may not silently transform its grid or invent missing-data semantics.**

This remains the central reproducibility boundary for PyFireCA spatial inputs.
