# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **R7 — validated directional Rothermel-to-arrival coupling**

## Current position

PyFireCA now has eight working foundations:

```text
1. Wildfire CA reference core
2. Fire-behavior/data contracts
3. GIS landscape input/output baseline
4. Validated Albini-adjusted Rothermel R1–R4 path
5. Dynamic Scott–Burgan herbaceous curing/load transfer
6. Audited standard-fuel catalogue subset
7. Static physical travel-time / arrival-time propagation
8. Behave-aligned surface ellipse → directional neighbor ROS → arrival coupling
```

Current scientific path:

```text
fuel + moisture + wind + slope
              ↓
     RothermelModel.compute()
              ↓
 maximum ROS + maximum direction
              ↓
  Behave/Catchpole surface ellipse
              ↓
FromIgnitionPoint directional ROS
              ↓
north-up neighbor edge bearing
              ↓
     physical distance / ROS
              ↓
       earliest arrival time
              ↓
  physical-time FireState snapshot
```

This path is now implemented end to end for a static homogeneous Rothermel environment. The next major engineering/science gap is **spatially heterogeneous static behavior inputs**, followed later by affine-aware geometry and truly time-dependent weather.

## Completed foundations

### CA core

- `FireState`: `UNBURNABLE / UNBURNED / BURNING / BURNED`;
- `RasterGrid`;
- Moore and Von Neumann neighborhoods;
- synchronous `TransitionRule` and `Simulation` reference path;
- explicit NumPy RNG;
- deterministic `NeighborIgnitionRule` architecture baseline;
- `build_initial_state(domain_mask, ignition_mask)`;
- synchronous no-cascade regression tests.

The original synchronous `Simulation` remains unchanged. One CA step still has no hidden physical duration.

### Behavior/data/GIS boundary

Implemented:

```text
FireBehaviorModel
FireBehaviorResult
SpatialLayer
EnvironmentalData
require_complete_snapshot
RasterMetadata
validate_raster_alignment
read_raster / write_raster
write_state_raster
nodata_mask
build_domain_mask
LandscapeInput
```

Static NoData becomes persistent domain semantics only when explicitly selected. Dynamic missing weather never silently creates permanent `UNBURNABLE` cells.

## Rothermel validation status

### R1 — heterogeneous fuel-bed quantities — complete

Validated:

```text
SI ↔ ft/lb/Btu/min conversions
surface-area weights
characteristic SAV
packing ratio
bulk density
optimum packing ratio
```

Fixed class order:

```text
DEAD_1H
DEAD_10H
DEAD_100H
DEAD_HERBACEOUS
LIVE_HERBACEOUS
LIVE_WOODY
```

### R2 — Albini-adjusted base ROS — Grade B

Pinned Behave 7 references:

```text
FM1 dead-only
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2 static dead + live
2.3810521029916596 chains/h
0.013305319151517395 m/s
```

### R3 — wind, slope, maximum-spread vector

Pinned references:

```text
FM1, 30% slope, zero wind
20.817222076028628 chains/h

FM1, zero slope, 100 ft/min direct-midflame wind
8.834274755440232 chains/h

FM1, 30% slope + perpendicular 100 ft/min wind push
21.399596624626479 chains/h maximum ROS
```

Implemented:

- slope factor;
- wind factor;
- effective-wind inversion;
- optional wind-speed limit;
- non-collinear wind/slope vector composition;
- explicit wind-from/downwind and aspect/upslope direction conversions.

When wind limiting is enabled and exceeded, `effective_wind_speed_m_s` now reports the **limited** effective wind, matching the Behave operational path. This is required before computing the fire ellipse.

### R4 — public model assembly — complete

```text
RothermelModel.compute(RothermelInputs)
        ↓
FireBehaviorResult
```

Stable outputs:

```text
spread_rate_m_s
spread_direction_deg
```

Zero wind + zero slope returns `spread_direction_deg=None`.

`fireline_intensity_w_m` and `flame_length_m` remain `None` until separately validated.

## R5 — dynamic herbaceous curing — Grade B

Pinned transfer rule:

```text
M_live_herb < 0.30       transfer = 1.0
0.30 <= M <= 1.20       transfer = 1.333 - 1.11*M
M > 1.20                 transfer = 0.0
```

Pinned GR1 result:

```text
model        101 / GR1
dead M       5/5/5 %
live herb M  60 %
live woody M 90 %
wind/slope   0 / 0

0.71419316836403091 chains/h
0.003990911424818205 m/s
```

`RothermelModel.compute()` reproduces this result end to end.

## Audited standard-fuel catalogue

Current public audited subset:

```text
1    FM1
2    FM2
101  GR1
```

API:

```text
StandardFuelModelRecord
available_standard_fuel_model_numbers()
get_standard_fuel_model_record(number)
get_standard_fuel_model(number)
```

Records retain pinned native source values and convert explicitly to the SI `RothermelFuelModel` contract. Unknown models fail explicitly as not yet audited.

## R6 — physical travel time and earliest arrival — complete baseline

`pyfireca.propagation` provides:

```text
square_grid_neighbor_distance_m
north_up_square_grid_offset_bearing_deg
spread_travel_time_s
square_grid_neighbor_travel_time_s
```

Contract:

```text
travel_time = physical_distance / direction_specific_ROS
```

`north_up_square_grid_offset_bearing_deg()` is explicitly north-up only:

```text
row -1 → north
col +1 → east
row +1 → south
col -1 → west
```

Rotated/sheared rasters require a later affine-aware adapter.

`StaticArrivalTimeSolver` performs Dijkstra-style earliest-arrival propagation for static non-negative edge travel times.

`arrival_times_to_state(..., time_s, burn_duration_s)` maps arrival fields to canonical `FireState` snapshots.

## R7 — Behave-aligned directional surface spread — Grade B

### Surface-fire ellipse

Pinned Behave surface L/W relation:

```text
L/W = 0.936 exp(0.1147 U) + 0.461 exp(-0.0692 U) - 0.397
```

where `U` is effective wind in mph. Surface L/W is capped at 8.

Then:

```text
e = sqrt((L/W)^2 - 1) / (L/W)
R_back = R_head * (1 - e) / (1 + e)
R_flank = (R_head + R_back) / (2 * L/W)
```

The pinned Behave `FromIgnitionPoint` path reduces the Catchpole-style ellipse to:

```text
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

where `beta=0°` is heading and `beta=180°` is backing.

Implemented in:

```text
src/pyfireca/behavior/_surface_ellipse.py
```

### Grade B off-axis reference

Dedicated pinned workflow:

```text
.github/workflows/behave7-r7-directional.yml
```

Case:

```text
FM1
dead moisture 5/5/5%
100 ft/min DirectMidflame wind
zero slope
90° from head
SurfaceFireSpreadDirectionMode::FromIgnitionPoint
```

Official full-precision Behave result:

```text
5.2277130003983068 chains/h
0.02921246024622574 m/s
```

The strengthened workflow requires:

```text
raw value match
Total tests performed: 172
Total tests passed:    172
Total tests failed:    0
```

Therefore the 90° off-axis radial ROS is Grade B.

### Homogeneous directional provider

Public behavior API now includes:

```text
HomogeneousRothermelDirectionalSpreadRate
```

It evaluates one static homogeneous `RothermelInputs`, caches its maximum behavior and ellipse, converts each north-up raster neighbor offset to a geographic bearing, and returns the Behave-style `FromIgnitionPoint` radial ROS for that edge.

Verified FM1 100 ft/min behavior:

```text
east  / head      0.04936592733340002 m/s
north / south     0.02921246024622574 m/s  ← Grade B 90°
west  / backing   0.02074385430924511 m/s
NE/SE / 45°       0.041067604539224284 m/s
```

The diagonal tests explicitly verify ellipse directional ROS rather than `head_ROS*cos(theta)`.

### First full anisotropic arrival coupling

End-to-end tests now exercise:

```text
FM1 Rothermel
→ maximum spread behavior
→ effective-wind ellipse
→ neighbor bearing
→ directional edge ROS
→ edge travel time
→ StaticArrivalTimeSolver
```

On an east-west line, the east head-fire neighbor arrives before the west backing-fire neighbor. On a north-south line, arrival time uses the pinned Grade B 90° off-axis ROS.

This is the first physically timed anisotropic propagation path in PyFireCA.

## Validation provenance

Evidence grades:

```text
Grade A  primary/authoritative worked value
Grade B  pinned official operational software regression
Grade C  independent implementation comparison
Grade D  internal analytical/synthetic fixture
```

Pinned revisions:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

External workflows:

```text
.github/workflows/behave7-r2-probe.yml
.github/workflows/behave7-r3-vector.yml
.github/workflows/behave7-r5-dynamic-probe.yml
.github/workflows/behave7-r7-directional.yml
```

## CI state

Functional suites covering R1–R7, dynamic GR1, fuel catalogue, GIS, ellipse directional spread, travel time, arrival time, and state snapshots pass across:

```text
Python 3.11  ✓
Python 3.12  ✓
Python 3.13  ✓
GIS          ✓
```

The R7 pinned directional workflow is green. Use the latest post-format all-green main run as the canonical CI baseline.

## Key decisions now fixed

1. Fire behavior and propagation remain separate.
2. One synchronous CA step has no hidden physical duration.
3. Physical edge travel time requires direction-specific ROS.
4. Maximum/head ROS is never silently assigned to all neighbors.
5. Surface off-axis ROS uses the pinned Behave/Catchpole `FromIgnitionPoint` ellipse path.
6. `FromPerimeter` directional rates are not used for ignition-point arrival propagation.
7. Ellipse L/W uses effective wind; if wind limiting is active, it uses the limited effective wind.
8. North-up raster offset bearings are explicit; rotated/sheared grids need an affine-aware adapter.
9. The current Rothermel directional provider uses **source-cell behavior** for each outgoing edge.
10. The current provider is static/homogeneous; time-dependent weather is not approximated as static without an explicit decision.
11. Dynamic curing remains a preprocessing redistribution before the shared R1/R2 chain.
12. Fireline intensity/flame length remain outside validated public outputs.

## Immediate next target

The off-axis science gate is now resolved. Next:

```text
validated homogeneous anisotropic path                 ✓
        ↓
static spatially heterogeneous Rothermel inputs        NEXT
        ↓
per-source-cell behavior + ellipse edge provider
        ↓
heterogeneous earliest-arrival validation
        ↓
affine-aware distance/bearing for non-square/rotated GIS grids
        ↓
time-dependent weather/event scheduling
```

For the first heterogeneous baseline, keep the edge semantic explicit: **outgoing edge ROS is determined by the source cell**. Do not invent source/target averaging until it has a scientific rationale and a separately tested alternative.

## Deferred work

- full Anderson 13 and Scott–Burgan 40 catalogue audit;
- affine-aware rotated/non-square raster geometry;
- time-varying weather/event scheduler;
- physical timestamp interpolation / NetCDF/xarray integration;
- fireline intensity and flame length validation;
- FBP;
- crown fire;
- spotting;
- suppression;
- Monte Carlo;
- profiling-led Numba;
- Torch/JAX/GPU/differentiable CA.
