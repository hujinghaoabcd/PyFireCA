# Static Raster Rothermel Workflow

> Status: implemented reference workflow
>
> Scope: static, north-up, square raster grids using audited Rothermel fuel models

## 1. Purpose

This workflow connects PyFireCA's GIS/data boundary to the validated Rothermel and physical-arrival propagation path without hiding scientific assumptions.

```text
aligned raster layers
        ↓
SpatialLayer / EnvironmentalData
        ↓
LandscapeInput
        ↓
StaticRasterRothermelInputsProvider
        ↓
StaticSpatialRothermelDirectionalSpreadRate
        ↓
RothermelModel + Behave-aligned surface ellipse
        ↓
direction-specific neighbor ROS
        ↓
StaticArrivalTimeSolver
        ↓
arrival time
        ↓
arrival_times_to_state(...)
```

The workflow is deliberately static. Dynamic weather must not be introduced by mutating cached arrays behind the static provider.

## 2. Required raster layers

Default layer names are defined by `RothermelRasterLayerNames`:

| Layer | Required units | Meaning |
| --- | --- | --- |
| `fuel_model` | `code` or `None` | audited standard fuel-model code |
| `dead_1h_moisture` | `fraction` | dead 1-h dry-mass moisture fraction |
| `dead_10h_moisture` | `fraction` | dead 10-h dry-mass moisture fraction |
| `dead_100h_moisture` | `fraction` | dead 100-h dry-mass moisture fraction |
| `live_herbaceous_moisture` | `fraction` | live herbaceous dry-mass moisture fraction |
| `live_woody_moisture` | `fraction` | live woody dry-mass moisture fraction |
| `midflame_wind_speed` | `m/s` | already-adjusted midflame wind speed |
| `wind_from_direction` | `deg` | meteorological wind-from bearing |
| `slope` | `deg` | slope angle, not percent slope |
| `aspect` | `deg` | geographic downslope bearing |

Custom names can be supplied through `RothermelRasterLayerNames` without changing the scientific contract.

## 3. Unit policy

The raster adapter is intentionally strict.

It does **not** silently perform:

```text
0–100 % moisture      → fraction
percent slope         → slope degrees
10-m/20-ft wind       → midflame wind
radians               → degrees
wind-from             → wind-push
```

These transformations belong in explicit preprocessing steps so that source-data provenance and assumptions remain visible.

`RothermelInputs` receives:

```text
moisture             dry-mass fraction
midflame wind        m/s
slope                 degrees
wind direction        degrees clockwise from north, meteorological from-bearing
aspect                degrees clockwise from north, downslope bearing
```

## 4. Fuel-model codes

The static raster adapter accepts only integer-like fuel codes that are present in PyFireCA's audited standard-fuel catalogue.

Current audited subset:

```text
1    FM1
2    FM2
101  GR1
```

An unknown model fails explicitly. The package does not silently fabricate or infer parameters for fuel records that have not been audited against pinned provenance.

## 5. NoData and persistent domain

NoData and CA domain state remain separate concepts.

The adapter receives an explicit `domain_mask`.

```text
domain_mask=True
    every required Rothermel layer must contain a finite, non-NoData value

domain_mask=False
    source raster values may legitimately remain NoData
```

This matters for real GIS data where areas outside a study region often contain NoData in every environmental raster.

Dynamic/transient missing weather is not represented by this static adapter and must never be converted silently into permanent `UNBURNABLE` cells.

## 6. Static spatial edge semantics

`StaticSpatialRothermelDirectionalSpreadRate` uses one explicit baseline assumption:

> **The source cell determines the outgoing edge rate of spread.**

For an edge from source cell `i` to neighbor `j`:

```text
R_ij = directional_Rothermel_ROS(source=i, direction=i→j)
```

No source-target averaging is performed.

Alternative edge coupling rules such as arithmetic/harmonic averaging, target-controlled spread, interface resistance, or learned edge modifiers are scientifically distinct CA assumptions and should be implemented as separate providers for controlled comparison.

## 7. Directional spread

For each source cell:

```text
fuel + moisture + wind + slope + aspect
        ↓
RothermelModel.compute()
        ↓
maximum ROS + maximum-spread bearing
        ↓
Behave-aligned surface ellipse
        ↓
neighbor bearing relative to head direction
        ↓
FromIgnitionPoint directional ROS
```

The pinned off-axis Grade B reference is:

```text
FM1
100 ft/min direct-midflame wind
zero slope
90° from heading

5.2277130003983068 chains/h
0.02921246024622574 m/s
```

The arrival solver therefore never applies a `head_ROS × cos(theta)` shortcut.

## 8. Current grid geometry contract

`StaticArrivalTimeSolver` currently uses square-cell center-to-center distances.

The landscape convenience factory therefore supports only:

```text
north-up affine
square pixels
positive x step
negative y step
explicit metric cell_size_m matching affine pixel size
```

The caller supplies `cell_size_m` explicitly because the lightweight `RasterMetadata` stores a CRS string but intentionally does not guess/parse its linear units.

The current factory rejects:

```text
rotated rasters
rectangular pixels
affine/cell-size mismatch
```

This fail-closed behavior is preferable to silently computing physically incorrect travel distances.

## 9. Minimal assembly

```python
solver = build_static_raster_rothermel_arrival_solver(
    landscape,
    cell_size_m=30.0,
    neighborhood=VonNeumannNeighborhood(),
)

arrival = solver.solve(domain_mask, ignition_times_s)

state = arrival_times_to_state(
    domain_mask,
    arrival,
    time_s=1200.0,
    burn_duration_s=600.0,
)
```

See `examples/static_raster_rothermel.py` for a complete file-free example.

## 10. GeoTIFF preparation

A real GeoTIFF workflow should remain explicit:

```text
read each raster
        ↓
validate CRS/shape/full affine alignment
        ↓
apply intentional preprocessing/unit conversion outside the CA kernel
        ↓
construct SpatialLayer(values, units=..., nodata=...)
        ↓
assemble EnvironmentalData / LandscapeInput
        ↓
run the static raster workflow
```

PyFireCA never silently reprojects, resamples, fills, shifts, or changes units inside the simulation pipeline.

## 11. What this workflow is not

It is not yet:

- a time-dependent weather solver;
- WRF/NetCDF integration;
- a rotated-affine propagation solver;
- a full Anderson 13 / Scott–Burgan 40 catalogue;
- crown fire, spotting, or suppression;
- a GPU backend;
- a claim that source-cell-only edge coupling is the uniquely correct CA discretization.

Those are later modules or research questions, not hidden behavior in this baseline.

## 12. Next scientific/engineering boundary

The static pipeline is now sufficient to study CA-specific spatial discretization questions while keeping behavior physics fixed.

Useful controlled variants include:

```text
source-cell edge ROS              current baseline
source/target interface coupling  future comparison
4 vs 8 vs extended neighborhoods
cell size sensitivity
directional grid bias
arrival/perimeter error
```

Dynamic weather requires a separate scheduler because Dijkstra-style static arrival assumes edge travel times do not change while the fire is traversing an edge.
