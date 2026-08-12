# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: continue from repository truth without reconstructing scientific decisions from chat history.

## 1. Identity and protected scope

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. Urban CA projects are engineering/GIS references only; urban simulation is not product scope.

Protected extension points:

```text
State
Neighborhood
Transition rule
Time stepping / event scheduler
Behavior model
Directional spread model
Spatial input provider
Edge-coupling rule
```

Do not casually reverse these decisions:

1. wildfire-specific scope;
2. NumPy is the readable scientific reference path;
3. optimize only after profiling;
4. fire behavior and CA/event propagation remain separate;
5. GIS I/O stays outside numerical kernels;
6. public behavior quantities use explicit SI units;
7. R2 is Albini-adjusted Rothermel;
8. midflame wind is explicit;
9. wind-from, wind-push, downslope aspect, and upslope are distinct semantics;
10. non-collinear wind/slope are vector-combined;
11. wind limit is optional and disabled by default;
12. dynamic herbaceous curing is load redistribution before the common R1/R2 path;
13. fuel records are public only after pinned-source audit;
14. one synchronous CA step has no hidden physical duration;
15. physical edge propagation requires direction-specific ROS;
16. do not assign maximum/head ROS to every neighbor;
17. arrival propagation uses the Behave `FromIgnitionPoint` radial spread path, not `FromPerimeter`;
18. surface L/W uses effective wind, including limited effective wind when wind limiting is active;
19. current physical raster geometry is explicitly north-up + square-cell;
20. the current heterogeneous edge baseline is **source-cell controlled**;
21. source/target averaging or interface resistance are separate research hypotheses, not hidden tweaks;
22. static raster units are strict and never silently converted;
23. static providers must not be mutated to fake dynamic weather;
24. external reference values carry evidence grades and pinned provenance.

## 2. Current source tree to read first

```text
src/pyfireca/
├── state.py
├── grid.py
├── neighborhood.py
├── rules.py
├── simulation.py
├── propagation.py
├── arrival.py
├── data.py
├── gis.py
└── behavior/
    ├── base.py
    ├── _units.py
    ├── _directions.py
    ├── fuel_catalog.py
    ├── rothermel.py
    ├── _rothermel_equations.py
    ├── _rothermel_dynamic.py
    ├── _rothermel_base.py
    ├── _rothermel_effects.py
    ├── _rothermel_vectors.py
    ├── _surface_ellipse.py
    ├── rothermel_model.py
    ├── rothermel_directional.py
    ├── rothermel_spatial.py
    ├── rothermel_layers.py
    └── rothermel_landscape.py
```

Also read:

```text
docs/STATIC_RASTER_WORKFLOW.md
examples/static_raster_rothermel.py
```

Do not create empty future modules only to match an architecture diagram.

## 3. Two propagation baselines coexist

### Synchronous CA reference

`Simulation` remains synchronous and step-count based. `NeighborIgnitionRule` is an architecture baseline, not physical wildfire science.

### Physical-time arrival reference

`StaticArrivalTimeSolver` is a Dijkstra-style earliest-arrival baseline for static non-negative directional edge travel times.

```text
directional ROS
→ physical edge distance
→ travel time
→ earliest arrival
→ arrival_times_to_state(..., burn_duration_s)
```

No `dt` was silently added to `Simulation`.

## 4. Physical raster geometry

`pyfireca.propagation` provides:

```text
square_grid_neighbor_distance_m
north_up_square_grid_offset_bearing_deg
spread_travel_time_s
square_grid_neighbor_travel_time_s
```

North-up convention:

```text
(-1, 0) north 0°
(0, 1)  east  90°
(1, 0)  south 180°
(0, -1) west  270°
```

The current landscape factory deliberately rejects rotated/sheared/non-square grids. Do not generalize geometry by approximation; implement an affine-aware path later if required.

## 5. Rothermel R1–R5 truth

Fixed six-class order:

```text
DEAD_1H
DEAD_10H
DEAD_100H
DEAD_HERBACEOUS
LIVE_HERBACEOUS
LIVE_WOODY
```

Public input:

```text
RothermelInputs(
    fuel,
    moisture,
    midflame_wind_speed_m_s,
    wind_from_direction_deg,
    slope_deg,
    aspect_deg,
)
```

### Grade B references

```text
FM1 base
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2 static dead+live base
2.3810521029916596 chains/h
0.013305319151517395 m/s

FM1 30% slope
20.817222076028628 chains/h

FM1 100 ft/min DirectMidflame wind
8.834274755440232 chains/h

FM1 30% slope + perpendicular 100 ft/min wind
21.399596624626479 chains/h maximum ROS

GR1, 60% live-herb moisture, zero wind/slope
0.71419316836403091 chains/h
0.003990911424818205 m/s
```

`RothermelModel.compute()` reproduces these validated stages.

Dynamic curing rule:

```text
M < 0.30       transfer = 1.0
0.30..1.20     transfer = 1.333 - 1.11*M
M > 1.20       transfer = 0.0
```

Transferred dead herb uses live-herb SAV, dead-fuel physical properties, and dead 1-h moisture.

## 6. Audited fuel catalogue

Currently public and audited only:

```text
1    FM1
2    FM2
101  GR1
```

Unknown fuel numbers fail explicitly as not audited yet. Do not claim the full Anderson 13 / Scott–Burgan 40 catalogue is complete.

## 7. R7 directional surface ellipse — Grade B

Pinned Behave surface ellipse:

```text
L/W = 0.936 exp(0.1147 U) + 0.461 exp(-0.0692 U) - 0.397
e = sqrt((L/W)^2 - 1) / (L/W)
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

`U` is effective wind in mph; surface `L/W <= 8`.

Pinned FM1 `FromIgnitionPoint`, 100 ft/min, zero slope, 90° from head:

```text
5.2277130003983068 chains/h
0.02921246024622574 m/s
```

The dedicated R7 workflow requires exact raw marker plus `172 passed / 0 failed`.

`HomogeneousRothermelDirectionalSpreadRate` bridges one validated Rothermel state to north-up raster edge ROS.

Known FM1 100 ft/min directional values:

```text
east head       0.04936592733340002 m/s
north/south     0.02921246024622574 m/s
west backing    0.02074385430924511 m/s
NE/SE 45°       0.041067604539224284 m/s
```

Never replace the ellipse with `head_ROS*cos(theta)`.

## 8. R8 static heterogeneous spatial provider

Public:

```text
StaticSpatialRothermelDirectionalSpreadRate
```

Contract:

```text
inputs_provider(row, col) -> RothermelInputs
```

The provider evaluates/caches one behavior + ellipse per source cell and then returns outgoing directional edge ROS.

Current baseline assumption:

> **The source cell determines the outgoing edge ROS.**

Tests include a line where source-cell wind changes direction: one edge uses head ROS and the next uses backing ROS. This proves the arrival solver re-evaluates behavior by source cell.

`clear_cache()` is for controlled experiments/tests only; it does not make the provider dynamically time-aware.

## 9. R8 static raster input contract

Public:

```text
RothermelRasterLayerNames
StaticRasterRothermelInputsProvider
```

Default layer contract:

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

Important:

- moisture rasters are already fractions, not percentages;
- slope is already degrees, not percent slope;
- wind is already midflame m/s, not 10-m/20-ft wind;
- wind direction is meteorological from-bearing;
- fuel code must be integer-like and audited;
- required layers must be static;
- NoData outside `domain_mask` is legal;
- NoData/nonfinite values inside `domain_mask` fail fast.

No unit conversion is hidden in this adapter.

## 10. Landscape factory

Public:

```text
build_static_raster_rothermel_arrival_solver(...)
```

Assembly:

```text
LandscapeInput
→ StaticRasterRothermelInputsProvider
→ StaticSpatialRothermelDirectionalSpreadRate
→ StaticArrivalTimeSolver
```

It is deliberately thin. It does not infer ignition, solve, interpolate, mutate state, or write output.

Geometry contract:

```text
north-up affine
square pixels
positive x step
negative y step
explicit cell_size_m
cell_size_m == affine x/y pixel magnitude
```

Why `cell_size_m` is explicit: lightweight `RasterMetadata` stores a CRS string but does not parse CRS linear units. The caller asserts that affine coordinates are metric; the factory checks geometric consistency only.

Rotated, sheared, rectangular, or mismatched grids are rejected.

## 11. Example that must remain executable

```text
examples/static_raster_rothermel.py
```

It demonstrates:

```text
5×7 raster environment
→ LandscapeInput
→ Rothermel landscape factory
→ ignition times
→ earliest arrival
→ FireState snapshot at physical time
```

`tests/test_examples.py` smoke-runs the example so API changes cannot silently break it.

Detailed data contract:

```text
docs/STATIC_RASTER_WORKFLOW.md
```

## 12. Validation provenance

Pinned software:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Evidence:

```text
Grade A  authoritative worked value
Grade B  pinned official operational software regression
Grade C  independent software comparison
Grade D  internal analytical/synthetic fixture
```

Workflows:

```text
.github/workflows/behave7-r2-probe.yml
.github/workflows/behave7-r3-vector.yml
.github/workflows/behave7-r5-dynamic-probe.yml
.github/workflows/behave7-r7-directional.yml
```

## 13. CI truth

The R8 functional path has passed across Python 3.11/3.12/3.13 and GIS jobs in the recent runs. Several recent red main runs were Ruff-format-only while every functional job was green. Always inspect the failed step before changing scientific code.

Canonical baseline = latest all-green post-format main run.

## 14. Exact next research work

The basic static GIS pipeline is no longer the science bottleneck. Do not immediately jump to WRF or GPU.

The most useful next CA work is controlled comparison of discretization assumptions while keeping the validated behavior model fixed:

```text
A. source-cell-controlled outgoing edge ROS       current baseline
B. explicit source/target interface coupling      future variant

4-neighbor vs 8-neighbor vs extended neighborhood
cell-size sensitivity
lattice directional bias
arrival-time error
perimeter/shape error
```

Any source/target averaging must be a named provider/variant, never an invisible modification of `StaticSpatialRothermelDirectionalSpreadRate`.

After a controlled static benchmark exists, design the time-dependent weather scheduler **in docs first**. Static Dijkstra assumes an edge's travel time is invariant while the fire traverses it; dynamic weather violates that assumption.

## 15. Deferred work

- full Anderson 13 / Scott–Burgan 40 catalogue audit;
- affine-aware rotated/non-square raster geometry;
- time-dependent weather scheduler;
- NetCDF/xarray/WRF integration;
- fireline intensity/flame length validation;
- FBP;
- crown fire;
- spotting;
- suppression;
- Monte Carlo;
- Numba optimization;
- Torch/JAX/GPU/differentiable CA.

## 16. Files to read first next session

```text
1. docs/STATUS.md
2. docs/HANDOFF.md
3. docs/STATIC_RASTER_WORKFLOW.md
4. docs/ROTHERMEL_REFERENCE.md
5. src/pyfireca/behavior/rothermel_model.py
6. src/pyfireca/behavior/_surface_ellipse.py
7. src/pyfireca/behavior/rothermel_directional.py
8. src/pyfireca/behavior/rothermel_spatial.py
9. src/pyfireca/behavior/rothermel_layers.py
10. src/pyfireca/behavior/rothermel_landscape.py
11. src/pyfireca/arrival.py
12. tests/test_rothermel_layers.py
13. tests/test_rothermel_landscape.py
14. examples/static_raster_rothermel.py
```
