# PyFireCA Development Session Log — R7/R8

> Date: 2026-08-12
>
> Scope: directional spread validation, physical arrival coupling, static spatial heterogeneity, and raster/GIS assembly.

## 1. Session objective

Advance PyFireCA from a validated maximum-spread Rothermel implementation to a physically timed, direction-aware, spatially heterogeneous raster propagation baseline while preserving the project's separation of concerns:

```text
fire behavior
→ directional fire shape
→ edge ROS
→ physical travel time
→ earliest arrival
→ FireState snapshot
```

No GPU, neural CA, WRF scheduler, crown fire, or general platform abstraction was added.

## 2. R7 off-axis directional spread

Pinned Behave core source showed that surface-fire directional spread follows the Catchpole-style ellipse used by Behave.

Implemented:

```text
_surface_ellipse.py
```

including:

```text
surface L/W from effective wind
eccentricity
backing ROS
flanking ROS
FromIgnitionPoint arbitrary-angle ROS
```

Pinned expression:

```text
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

A dedicated Behave workflow was added for an FM1 off-axis case.

Pinned Grade B result:

```text
FM1
100 ft/min DirectMidflame wind
zero slope
90° from head
FromIgnitionPoint

5.2277130003983068 chains/h
0.02921246024622574 m/s
```

Official Behave suite result:

```text
172 tests performed
172 passed
0 failed
```

The workflow now gates on the exact raw value and zero failed tests.

## 3. Wind-limit ellipse correction

Before using effective wind to determine fire shape, the Rothermel wind-limit path was rechecked.

Important operational behavior:

```text
if wind limit is enabled and exceeded:
    effective_wind_speed = wind_speed_limit
```

The ellipse therefore uses the limited effective wind, not the pre-limit effective wind.

This correction affects shape/eccentricity under high-wind limiting even when the already-capped forward ROS was correct.

## 4. North-up raster direction semantics

Added explicit square north-up raster offset bearings:

```text
(-1, 0) north 0°
(0, 1)  east  90°
(1, 0)  south 180°
(0, -1) west  270°
```

The helper name and documentation explicitly exclude rotated/sheared grids.

## 5. Homogeneous Rothermel directional provider

Added:

```text
HomogeneousRothermelDirectionalSpreadRate
```

Pipeline:

```text
RothermelInputs
→ RothermelModel.compute()
→ maximum ROS + direction
→ effective-wind surface ellipse
→ neighbor bearing
→ angular separation from head
→ FromIgnitionPoint edge ROS
```

FM1 100 ft/min regression values:

```text
east head       0.04936592733340002 m/s
north/south     0.02921246024622574 m/s
west backing    0.02074385430924511 m/s
NE/SE 45°       0.041067604539224284 m/s
```

Diagonal tests explicitly prevent replacement with `head_ROS*cos(theta)`.

## 6. First anisotropic arrival coupling

`StaticArrivalTimeSolver` was connected to the homogeneous directional provider.

Tests verify:

- east/head arrival is faster than west/backing arrival;
- north/south travel uses the pinned Grade B 90° ROS;
- zero-wind/no-slope behavior remains isotropic;
- wind-limited ellipse shape uses the limited effective wind.

The synchronous `Simulation` API remained unchanged.

## 7. Static spatial heterogeneity

Added:

```text
StaticSpatialRothermelDirectionalSpreadRate
```

Input contract:

```text
inputs_provider(row, col) -> RothermelInputs
```

One behavior/ellipse pair is cached per source cell.

Baseline edge rule:

> **The source cell determines the outgoing edge ROS.**

No target-cell averaging is performed.

A regression path changes wind direction between adjacent source cells so one edge is heading and the next outgoing edge is backing. This validates true per-source-cell behavior evaluation.

## 8. Static raster Rothermel adapter

Added:

```text
RothermelRasterLayerNames
StaticRasterRothermelInputsProvider
```

Exact default layer contract:

```text
fuel_model                   code / None
dead_1h_moisture             fraction
dead_10h_moisture            fraction
dead_100h_moisture           fraction
live_herbaceous_moisture     fraction
live_woody_moisture          fraction
midflame_wind_speed          m/s
wind_from_direction          deg
slope                        deg
aspect                       deg
```

The adapter deliberately performs no hidden conversions.

Validation added for:

- static-only layers;
- domain/shape consistency;
- declared units;
- integer fuel codes;
- audited catalogue membership;
- NoData/nonfinite values inside domain;
- legal NoData outside domain.

## 9. Landscape factory

Added:

```text
build_static_raster_rothermel_arrival_solver
```

Assembly:

```text
LandscapeInput
→ StaticRasterRothermelInputsProvider
→ StaticSpatialRothermelDirectionalSpreadRate
→ StaticArrivalTimeSolver
```

The factory remains intentionally thin and does not:

- infer ignition;
- solve automatically;
- mutate state;
- interpolate weather;
- write output.

Current physical-grid restrictions:

```text
north-up
square pixels
positive x / negative y affine step
explicit cell_size_m
cell_size_m matches affine pixel size
```

Rotated/sheared/rectangular/mismatched grids fail closed.

## 10. End-to-end example

Added:

```text
examples/static_raster_rothermel.py
```

It demonstrates:

```text
5×7 environment arrays
→ SpatialLayer / EnvironmentalData
→ RasterMetadata / LandscapeInput
→ static Rothermel arrival factory
→ ignition_times_s
→ earliest arrival
→ FireState snapshot at 20 min
```

Added `tests/test_examples.py` to execute the example under CI rather than treating examples as untested documentation.

## 11. Documentation updates

Added:

```text
docs/STATIC_RASTER_WORKFLOW.md
```

Updated:

```text
docs/STATUS.md      → R8
docs/HANDOFF.md     → R8
```

The static workflow document records layer names, units, NoData semantics, edge assumptions, grid geometry, minimal API, GeoTIFF preparation sequence, and explicit non-goals.

## 12. CI observations

Throughout R7/R8, functional test jobs repeatedly passed while the overall workflow was temporarily red because of Ruff formatting/import-order checks.

Important rule retained:

> Do not change scientific equations when Python/GIS tests are green and only Ruff is red.

Recent R8 functional matrices have passed on:

```text
Python 3.11
Python 3.12
Python 3.13
GIS
```

The example smoke test also executed successfully in those functional jobs. The final action of this session is to confirm the latest post-import-fix run is completely green and use it as the R8 canonical baseline.

## 13. Next research target

The next useful work is CA science rather than generic infrastructure.

Keep validated behavior fixed and compare discretization assumptions:

```text
source-cell outgoing edge ROS          current baseline
source/target interface coupling       next variant

4-neighbor vs 8-neighbor
extended neighborhoods
cell-size sensitivity
lattice directional bias
arrival-time error
perimeter/shape error
```

Do not silently modify `StaticSpatialRothermelDirectionalSpreadRate` to average source and target cells. New edge semantics must be explicit named providers so they can be compared scientifically.

Dynamic weather should be designed later as a separate scheduler because the static Dijkstra solver assumes edge travel time is invariant during traversal.
