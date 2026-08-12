# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: continue from repository truth without reconstructing scientific decisions from chat history.

## 1. Identity and protected scope

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. Fire behavior, directional fire-shape geometry, and CA/event propagation are separate layers.

Protected extension points:

```text
State
Neighborhood
Transition rule
Time stepping / event scheduler
Behavior model
Directional spread model
Spatial input provider
```

Do not casually reverse these decisions:

1. wildfire-specific scope;
2. NumPy is the readable scientific reference path;
3. optimization only after profiling;
4. fire behavior and propagation remain separate;
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
18. surface L/W uses effective wind, and limited effective wind when wind limiting is active;
19. the current raster bearing helper is explicitly north-up;
20. external reference values carry evidence grades and pinned provenance.

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
    └── rothermel_directional.py
```

Do not create empty future modules only to match an architecture diagram.

## 3. Two propagation baselines now coexist

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

Rotated/sheared/non-square geospatial grids require a future affine-aware adapter.

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

`RothermelModel.compute()` is public and reproduces these validated stages.

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

Public API:

```text
StandardFuelModelRecord
available_standard_fuel_model_numbers
get_standard_fuel_model_record
get_standard_fuel_model
```

Unknown fuel numbers fail explicitly as not audited yet.

## 7. R7 surface ellipse — now validated

Pinned Behave surface length-to-width relation:

```text
L/W = 0.936 exp(0.1147 U) + 0.461 exp(-0.0692 U) - 0.397
```

with effective wind `U` in mph and surface cap `L/W <= 8`.

Then:

```text
e = sqrt((L/W)^2 - 1) / (L/W)
R_back = R_head * (1 - e) / (1 + e)
R_flank = (R_head + R_back) / (2 * L/W)
```

Pinned Behave `FromIgnitionPoint` radial spread:

```text
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

`beta` is angular separation from the maximum-spread direction.

Implementation:

```text
src/pyfireca/behavior/_surface_ellipse.py
```

### Grade B FM1 off-axis reference

Workflow:

```text
.github/workflows/behave7-r7-directional.yml
```

Pinned case:

```text
FM1
5/5/5% dead moisture
100 ft/min DirectMidflame wind
zero slope
90° from head
FromIgnitionPoint
```

Official full-precision result:

```text
5.2277130003983068 chains/h
0.02921246024622574 m/s
```

The strengthened workflow checks the exact raw marker plus:

```text
Total tests performed: 172
Total tests passed:    172
Total tests failed:    0
```

This 90° radial ROS is Grade B.

## 8. Rothermel directional edge provider

Public:

```text
HomogeneousRothermelDirectionalSpreadRate
```

It:

1. evaluates one static `RothermelInputs` once;
2. builds the surface ellipse from maximum ROS and effective wind;
3. maps north-up raster offsets to geographic bearings;
4. computes angular offset from the head direction;
5. returns Behave-style `FromIgnitionPoint` radial ROS for the outgoing edge.

FM1 100 ft/min reference behavior:

```text
east head       0.04936592733340002 m/s
north/south     0.02921246024622574 m/s
west backing    0.02074385430924511 m/s
NE/SE 45°       0.041067604539224284 m/s
```

The diagonal path is **not** `head_ROS*cos(theta)`.

## 9. First end-to-end anisotropic physical path

Tests now exercise:

```text
RothermelModel
→ effective-wind surface ellipse
→ north-up edge bearing
→ directional edge ROS
→ distance / ROS
→ StaticArrivalTimeSolver
```

On an east-west line, the head-fire cell arrives before the backing-fire cell. On a north-south line, travel time uses the pinned Grade B 90° off-axis ROS.

This is the first validated anisotropic physical-time spread chain in PyFireCA.

## 10. Wind-limit detail that must not regress

When the optional wind limit is exceeded, `RothermelModel` now reports:

```text
effective_wind_speed_m_s = wind_speed_limit_m_s
```

not the pre-limit effective wind. This matters because the ellipse L/W must use the limited effective wind.

## 11. Validation provenance

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

## 12. CI truth

R7 functional tests have passed on:

```text
Python 3.11
Python 3.12
Python 3.13
GIS
```

The dedicated pinned R7 Behave workflow is green. If only quality is red, inspect Ruff before touching scientific code.

## 13. Exact next work

The off-axis science gate is resolved. Next implement a **static spatially heterogeneous directional provider**.

Recommended interface:

```text
inputs_provider(row, col) -> RothermelInputs
        ↓
per-source-cell Rothermel behavior + ellipse
        ↓
outgoing directional edge ROS
        ↓
StaticArrivalTimeSolver
```

First-baseline edge semantic is intentionally:

> **Outgoing edge ROS is determined by the source cell.**

Do not invent source/target averaging until there is a scientific rationale and a separately tested alternative.

After this:

```text
heterogeneous static provider
→ heterogeneous arrival validation
→ affine-aware distance/bearing
→ time-dependent weather/event scheduler
```

## 14. Deferred work

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

## 15. Files to read first next session

```text
1. docs/STATUS.md
2. docs/HANDOFF.md
3. docs/ROTHERMEL_REFERENCE.md
4. src/pyfireca/behavior/rothermel_model.py
5. src/pyfireca/behavior/_surface_ellipse.py
6. src/pyfireca/behavior/rothermel_directional.py
7. src/pyfireca/propagation.py
8. src/pyfireca/arrival.py
9. tests/test_rothermel_directional.py
10. tests/test_arrival.py
```
