# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **R8 — static spatial raster Rothermel coupling**

## Current position

PyFireCA now has nine working foundations:

```text
1. Wildfire CA reference core
2. Fire-behavior/data contracts
3. GIS landscape input/output baseline
4. Validated Albini-adjusted Rothermel R1–R4 path
5. Dynamic Scott–Burgan herbaceous curing/load transfer
6. Audited standard-fuel catalogue subset
7. Static physical travel-time / arrival-time propagation
8. Behave-aligned surface ellipse → directional neighbor ROS → arrival coupling
9. Static spatial raster layers → typed per-cell Rothermel → heterogeneous arrival
```

Current implemented path:

```text
aligned raster layers
        ↓
SpatialLayer / EnvironmentalData
        ↓
LandscapeInput
        ↓
StaticRasterRothermelInputsProvider
        ↓
per-source-cell RothermelInputs
        ↓
StaticSpatialRothermelDirectionalSpreadRate
        ↓
RothermelModel + Behave/Catchpole surface ellipse
        ↓
direction-specific outgoing neighbor ROS
        ↓
physical edge distance / ROS
        ↓
StaticArrivalTimeSolver
        ↓
earliest arrival time
        ↓
physical-time FireState snapshot
```

The static GIS-to-arrival path is now implemented end to end for north-up square metric rasters. The next scientific CA boundary is no longer basic Rothermel or GIS assembly; it is controlled comparison of **edge coupling, neighborhood/grid discretization, and lattice bias**, followed later by an explicitly designed time-dependent weather scheduler.

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

The original synchronous `Simulation` remains unchanged. One CA step has no hidden physical duration.

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

When wind limiting is enabled and exceeded, `effective_wind_speed_m_s` reports the **limited** effective wind, matching the Behave operational path and keeping ellipse shape consistent with the capped wind.

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
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

The last expression is the pinned Behave `FromIgnitionPoint` path used for radial arrival propagation.

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

The hardened workflow requires the raw value plus `172 passed / 0 failed`.

### Homogeneous directional provider

`HomogeneousRothermelDirectionalSpreadRate` evaluates one static Rothermel state, caches its behavior and ellipse, converts north-up raster offsets to bearings, and returns the Behave-style radial ROS.

Verified FM1 100 ft/min values:

```text
east  / head      0.04936592733340002 m/s
north / south     0.02921246024622574 m/s
west  / backing   0.02074385430924511 m/s
NE/SE / 45°       0.041067604539224284 m/s
```

Diagonal spread follows the ellipse; no `head_ROS*cos(theta)` shortcut is used.

## R8 — static spatial raster coupling — implemented baseline

### Per-source-cell heterogeneous behavior

`StaticSpatialRothermelDirectionalSpreadRate` accepts:

```text
inputs_provider(row, col) -> RothermelInputs
```

and caches one Rothermel behavior/ellipse state per evaluated source cell.

The baseline edge semantic is explicit:

> **The source cell determines the outgoing edge ROS.**

No source/target averaging is hidden inside the provider. Alternative interface rules are future CA variants and must be implemented separately.

Tests verify that when wind direction changes between adjacent source cells, the first edge can use head ROS while the next edge uses backing ROS. Earliest-arrival propagation therefore re-evaluates behavior by source cell rather than reusing one landscape-wide state.

### Static raster input adapter

Public API:

```text
RothermelRasterLayerNames
StaticRasterRothermelInputsProvider
```

Default layers and exact units:

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

The adapter never silently converts percent moisture, percent slope, 10-m wind, radians, or wind-height definitions.

Only `domain_mask=True` cells are required to have complete Rothermel data. NoData outside the domain is legal; NoData/non-finite values inside the domain fail fast.

Fuel codes must be integer-like and present in the audited catalogue.

### Landscape convenience factory

Public API:

```text
build_static_raster_rothermel_arrival_solver(...)
```

This thin factory assembles:

```text
LandscapeInput
→ StaticRasterRothermelInputsProvider
→ StaticSpatialRothermelDirectionalSpreadRate
→ StaticArrivalTimeSolver
```

It does not infer ignition, solve automatically, interpolate weather, or write outputs.

Current geometry is deliberately fail-closed:

```text
north-up only
square pixels only
positive x / negative y affine steps
explicit cell_size_m
cell_size_m must match affine pixel size
```

The caller explicitly asserts metric cell size because lightweight `RasterMetadata` does not parse CRS linear units.

Rotated, sheared, rectangular, or affine/cell-size-mismatched grids are rejected rather than approximated silently.

### Example workflow

```text
examples/static_raster_rothermel.py
```

The file-free example builds a 5×7 aligned environment, runs static Rothermel directional arrival, then converts the arrival field to a physical-time `FireState` snapshot. A smoke test executes the example so future API changes cannot silently break it.

Detailed contract:

```text
docs/STATIC_RASTER_WORKFLOW.md
```

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

Functional suites covering R1–R8, dynamic GR1, fuel catalogue, GIS, directional ellipse, physical travel/arrival, spatial raster adapters, landscape factory, and example workflow pass across the supported Python/GIS matrix in the latest functional runs. The canonical baseline remains the latest all-green post-format run; do not reinterpret a Ruff-only failure as a scientific regression.

## Key decisions now fixed

1. Fire behavior and propagation remain separate.
2. One synchronous CA step has no hidden physical duration.
3. Physical edge travel time requires direction-specific ROS.
4. Maximum/head ROS is never silently assigned to all neighbors.
5. Surface off-axis ROS uses the pinned Behave/Catchpole `FromIgnitionPoint` ellipse path.
6. `FromPerimeter` directional rates are not used for ignition-point arrival propagation.
7. Ellipse L/W uses effective wind; if wind limiting is active, it uses limited effective wind.
8. North-up square-grid bearing/distance semantics are explicit.
9. The current heterogeneous baseline uses **source-cell behavior for outgoing edges**.
10. Source/target averaging, interface resistance, or other edge coupling are separate model hypotheses.
11. Static raster units are explicit and never silently converted.
12. Domain-exterior NoData is allowed; domain-interior required behavior data fail fast.
13. The current static provider must not be mutated to fake dynamic weather.
14. Fireline intensity/flame length remain outside validated public outputs.

## Immediate next target

R8 completes the static GIS-to-arrival baseline. The next work should now emphasize CA research rather than adding generic infrastructure:

```text
validated fire behavior                            ✓
validated directional ellipse                      ✓
static raster heterogeneous arrival                ✓
        ↓
controlled CA edge-coupling variants
        ↓
neighborhood / cell-size / lattice-bias experiments
        ↓
spread-shape and arrival-time error metrics
        ↓
only then design time-dependent weather scheduling
```

Candidate controlled variants should remain explicit, for example:

```text
source-cell-controlled edge ROS        current baseline
source/target interface coupling       future variant
4-neighbor / 8-neighbor / extended     future experiment
cell-size sensitivity                  future experiment
directional grid bias                  future experiment
```

Do not implement source/target averaging as an invisible tweak to the current provider.

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
