# Static Raster Rothermel Workflow

> Status: implemented reference workflow
>
> Updated: 2026-08-13
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
RothermelModel + Behave/Catchpole surface ellipse
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

The complete file-based user workflow built on top of this scientific path is documented in `docs/RUNNING_SIMULATOR.md`.

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

Custom in-memory names can be supplied through `RothermelRasterLayerNames` without changing the scientific contract. The version-1 YAML workflow intentionally fixes the public file keys above.

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

These transformations belong in explicit preprocessing so source-data provenance and assumptions remain visible.

`RothermelInputs` receives:

```text
moisture             dry-mass fraction
midflame wind        m/s
slope                 degrees
wind direction       degrees clockwise from north, meteorological from-bearing
aspect               degrees clockwise from north, downslope bearing
```

## 4. Fuel-model codes

The static raster adapter accepts only integer-like fuel codes present in PyFireCA's audited standard-fuel catalogue.

Current audited baseline:

```text
1–13  Anderson FM1–FM13
101   Scott–Burgan GR1
```

Anderson records are pinned to the USFS Fire Lab Behave core revision:

```text
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

An unknown model fails explicitly. The package does not silently fabricate or infer parameters for unaudited fuel records.

The remaining Scott–Burgan models are post-baseline catalogue work and do not block the first static simulator release.

## 5. NoData and persistent domain

NoData and CA domain state remain separate concepts.

The scientific adapter receives an explicit `domain_mask`.

```text
domain_mask=True
    every required Rothermel layer must contain a finite, non-NoData value

domain_mask=False
    source raster values may legitimately remain NoData
```

The version-1 file workflow derives the persistent domain from the `fuel_model` raster's declared NoData mask.

Dynamic/transient missing weather is not represented by this static adapter and must never be converted silently into permanent `UNBURNABLE` cells.

## 6. Static spatial edge semantics

`StaticSpatialRothermelDirectionalSpreadRate` uses one explicit baseline assumption:

> **The source cell determines the outgoing edge rate of spread.**

For an edge from source cell `i` to neighbor `j`:

```text
R_ij = directional_Rothermel_ROS(source=i, direction=i→j)
```

No source-target averaging is performed.

Alternative edge coupling rules such as averaging, target-controlled spread, interface resistance, half-cell coupling, or learned modifiers are scientifically distinct hypotheses. They are documented as future research variants and are not hidden in the baseline simulator.

## 7. Directional spread

For each source cell:

```text
fuel + moisture + wind + slope + aspect
        ↓
RothermelModel.compute()
        ↓
maximum ROS + maximum-spread bearing
        ↓
Behave/Catchpole surface ellipse
        ↓
neighbor bearing relative to head direction
        ↓
FromIgnitionPoint directional ROS
```

Pinned off-axis Grade B reference:

```text
FM1
100 ft/min DirectMidflame wind
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

The caller supplies `cell_size_m` explicitly because lightweight `RasterMetadata` stores a CRS string but intentionally does not guess/parse linear units.

The current factory rejects:

```text
rotated rasters
sheared rasters
rectangular pixels
affine/cell-size mismatch
```

This fail-closed behavior is preferable to silently computing physically incorrect travel distances.

The physical arrival baseline additionally restricts propagation to immediate-neighbor edges so a larger neighborhood cannot silently jump an intermediate barrier.

## 9. Minimal in-memory assembly

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

See `examples/static_raster_rothermel.py` for the file-free example.

For the ordinary file/CLI workflow use:

```bash
pyfireca validate examples/static_run.yml
pyfireca run examples/static_run.yml
```

after replacing the example paths with real aligned rasters.

## 10. GeoTIFF preparation

A real GeoTIFF workflow remains explicit:

```text
read each raster
→ validate CRS/shape/full affine alignment
→ intentional preprocessing/unit conversion outside the simulator
→ construct strict spatial layers
→ assemble LandscapeInput
→ run physical static arrival
```

PyFireCA never silently reprojects, resamples, fills, shifts, or changes units inside the simulation pipeline.

## 11. What this workflow is not

It is not:

- a time-dependent weather solver;
- WRF/NetCDF integration;
- a rotated-affine propagation solver;
- the full Scott–Burgan 40 catalogue;
- crown fire, spotting, or suppression;
- a Monte Carlo engine;
- a GPU backend;
- a claim that source-cell-only edge coupling is uniquely correct.

Anderson 13 **is** now audited and is part of the baseline.

## 12. Current development boundary

The static scientific pipeline is sufficient for future controlled CA-discretization research, but that research is intentionally frozen until release-readiness work is complete.

Potential later comparisons remain:

```text
source-cell edge ROS              current baseline
source/target interface coupling  future comparison
4 vs 8 vs extended neighborhoods  future comparison
cell-size sensitivity             future experiment
directional grid bias             future experiment
arrival/perimeter error           future metrics
```

Current next step is instead:

```text
release checklist
→ all-green built-package workflow
→ baseline freeze/tag
→ then reopen CA research
```

Dynamic weather requires a separate scheduler because Dijkstra-style static arrival assumes edge travel times do not change while fire traverses an edge.
