# GIS Raster Data Contract

> Status: active design contract
>
> Updated: 2026-08-12

## 1. Purpose

PyFireCA uses GIS data, but GIS file formats must not define the numerical CA engine.

The intended boundary is:

```text
GeoTIFF / future NetCDF / other GIS source
        ↓
GIS adapter
        ↓
array + RasterMetadata
        ↓
explicit alignment validation
        ↓
EnvironmentalData / RasterGrid / behavior inputs
        ↓
CA simulation
```

The engine should never discover during a simulation that two input rasters use different grids.

## 2. `RasterMetadata`

`src/pyfireca/gis.py` currently defines a lightweight Rasterio-independent metadata object:

```text
shape       (height, width)
crs         canonical non-empty string
transform   (a, b, c, d, e, f)
nodata      optional marker
```

The affine tuple follows:

```text
x = a * col + b * row + c
y = d * col + e * row + f
```

PyFireCA stores this contract independently of Rasterio/GDAL so importing the CA core does not require a GIS binary stack.

A future Rasterio adapter should convert `dataset.crs`, `dataset.transform`, `dataset.shape`, and `dataset.nodata` into this small representation before numerical code sees them.

## 3. Alignment definition

For the current raster CA line, two layers are geometrically aligned only when these agree:

```text
shape
CRS
six affine coefficients within an explicit tolerance
```

`validate_raster_alignment()` checks these conditions and raises `RasterAlignmentError` on mismatch.

It never:

- reprojects;
- resamples;
- clips/crops;
- shifts an origin;
- changes pixel size;
- changes CRS.

Those are preprocessing operations and must be requested explicitly.

## 4. Why transform is checked instead of resolution alone

Equal shape and equal nominal resolution do not prove that two rasters represent the same cells.

For example:

```text
fuel.tif origin       = (500000, 3600000)
wind.tif origin       = (500015, 3600000)
resolution both       = 30 m
shape both            = identical
```

The layers are half a cell out of phase and must not be combined silently.

The affine transform therefore belongs to the formal alignment contract.

## 5. Transform tolerance

Floating-point serialization can introduce tiny coefficient differences, so alignment uses an explicit absolute tolerance instead of exact tuple equality.

Initial default:

```text
absolute_tolerance = 1e-9
relative_tolerance = 0
```

This tolerance is for numerical representation noise only. It must never be enlarged to make genuinely shifted rasters “pass”.

A user/workflow may choose another tolerance explicitly, and the choice should be documented in reproducible preprocessing when it materially affects acceptance.

## 6. CRS policy

The core metadata object currently treats `crs` as a canonical string supplied by a GIS adapter and compares it exactly.

This is deliberate: the core package should not contain a partial CRS parser.

A Rasterio adapter can later canonicalize equivalent CRS definitions using Rasterio/PROJ before constructing `RasterMetadata`.

Do not compare raw user-entered CRS text in a way that claims semantically equivalent WKT strings are always different; normalization belongs to the adapter that understands CRS semantics.

## 7. Resolution

`RasterMetadata.resolution` returns the magnitudes of the affine pixel-axis vectors:

```text
x_resolution = sqrt(a² + d²)
y_resolution = sqrt(b² + e²)
```

This works for both north-up and rotated transforms.

Resolution is useful metadata, but alignment still checks the complete affine transform.

## 8. NoData policy

NoData is **not** part of geometric alignment by default.

Two aligned sources may use different marker values such as:

```text
-9999
-32768
NaN
```

while still describing exactly the same grid.

`validate_raster_alignment(..., check_nodata=True)` may enforce equality when a workflow specifically requires it.

More importantly, PyFireCA still needs a later scientific/data decision describing how input NoData becomes simulation semantics, for example:

```text
invalid observation?
unburnable cell?
masked cell excluded from analysis?
missing dynamic weather requiring failure/interpolation?
```

Do not silently convert every NoData value to `UNBURNABLE` until that policy is explicitly defined for each input type.

## 9. Named multi-layer validation

`validate_named_raster_alignment()` checks a mapping of named candidate layers against one reference grid and includes the layer name in errors.

Intended preprocessing pattern:

```text
reference = fuel metadata

validate:
    elevation
    slope
    aspect
    wind speed
    wind direction
    moisture
```

An error should identify the offending layer rather than only reporting two anonymous transforms.

## 10. Relationship to `SpatialLayer`

`SpatialLayer` remains the lightweight numerical representation:

```text
(Y, X)
(T, Y, X)
```

It intentionally does not duplicate CRS/affine metadata on every dynamic time slice.

The intended future loaded-raster object or adapter result may pair:

```text
RasterMetadata
+
SpatialLayer
```

without making each cell a Python GIS object.

The exact user-facing container is deferred until Rasterio I/O is implemented; do not create another abstraction merely to anticipate it.

## 11. Relationship to `RasterGrid`

`RasterGrid` currently owns CA state and optional `cell_size` but does not yet embed `RasterMetadata`.

Do not add metadata to `RasterGrid` until the real GIS adapter workflow demonstrates which ownership model is cleanest. Likely options are:

```text
A. simulation/domain object owns one shared RasterMetadata
B. RasterGrid gains optional geospatial metadata
```

Whichever is chosen must avoid duplicating contradictory metadata across every layer.

## 12. Rasterio adapter — deferred next step

`rasterio` is already an optional dependency group, not a core dependency.

A future adapter should minimally support:

```text
read one raster → ndarray + RasterMetadata
write one result array using explicit reference metadata
canonicalize CRS using Rasterio/PROJ
validate dtype/band assumptions
```

Tests should use small in-memory/generated rasters rather than committing large datasets.

The adapter must not silently align incompatible inputs. A separate explicit preprocessing helper may later reproject/resample when requested.

## 13. Validation requirements

Current unit tests cover:

- positive raster dimensions;
- non-empty CRS;
- finite affine coefficients;
- north-up and rotated resolution calculation;
- shape mismatch rejection;
- CRS mismatch rejection;
- transform mismatch rejection;
- explicit transform tolerance;
- optional NoData equality;
- named-layer error reporting.

Future Rasterio integration tests must also cover:

- CRS round trip;
- affine transform round trip;
- NoData preservation;
- dtype preservation;
- intentional failure on misalignment;
- written output reopening with expected geometry.

## 14. Design rule

**GIS preprocessing may transform data; CA simulation may not silently transform its input grid.**

This distinction is central to reproducible spatial simulation and should remain visible in the code and documentation.
