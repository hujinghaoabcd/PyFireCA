# Rothermel Reference Implementation

> Status: **R1–R8 implemented for the current surface-fire reference path**
>
> Updated: 2026-08-12

## 1. Role in PyFireCA

Rothermel is the first fire-behavior family implemented as a readable scientific reference. This is a development-order decision, not a claim that Rothermel is preferable to FBP for every wildfire CA problem.

Current boundary:

```text
fuel + moisture + midflame wind + slope + aspect
                         ↓
                   RothermelInputs
                         ↓
                  RothermelModel
                         ↓
         maximum ROS + maximum direction
                         ↓
             Behave-aligned surface ellipse
                         ↓
             direction-specific edge ROS
                         ↓
          physical travel / earliest arrival
```

Fire-behavior equations, directional geometry, raster input adaptation, and CA/event propagation remain separate layers.

## 2. Scientific references and pinned validation software

Primary scientific references:

1. Rothermel (1972), USDA Forest Service Research Paper INT-115.
2. Albini (1976), USDA Forest Service GTR INT-30.
3. Catchpole et al. (1982), elliptical directional-spread relation used by the pinned Behave path.
4. Scott & Burgan (2005), USDA Forest Service RMRS-GTR-153, DOI `10.2737/RMRS-GTR-153`.
5. Andrews (2018), USDA Forest Service RMRS-GTR-371, DOI `10.2737/RMRS-GTR-371`.

Pinned official operational regression source:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

PyFireCA independently implements the equations and uses pinned Behave only as an external numerical reference.

Evidence grades:

```text
Grade A  primary/authoritative worked value
Grade B  pinned official operational software regression
Grade C  independent software comparison
Grade D  internal analytical/synthetic fixture
```

## 3. Public fuel and unit contract

Fixed six-class order:

```text
0 DEAD_1H
1 DEAD_10H
2 DEAD_100H
3 DEAD_HERBACEOUS
4 LIVE_HERBACEOUS
5 LIVE_WOODY
```

Public SI units:

| Quantity | Unit |
| --- | --- |
| fuel-bed depth | m |
| fuel load | kg/m² |
| SAV | 1/m |
| heat content | J/kg |
| particle density | kg/m³ |
| moisture | dry-mass fraction |
| midflame wind | m/s |
| slope | degrees |
| direction | degrees clockwise from geographic north |

Published ft/lb/Btu/min correlations are evaluated only after explicit conversion through `_units.py`.

`RothermelInputs` receives **midflame wind directly**. 10-m/20-ft wind adjustment remains preprocessing.

Direction semantics:

```text
aspect                 geographic downslope bearing
wind_from_direction    meteorological from-bearing
wind push              wind_from + 180°
upslope                 aspect + 180°
```

## 4. R1 — heterogeneous fuel-bed quantities

Implemented and tested:

```text
surface-area weights
characteristic SAV
packing ratio
bulk density
optimum packing ratio
```

Surface-area weighting uses relative area proportional to:

```text
SAV × oven-dry load / particle density
```

Synthetic hand-computable tests verify within-life-state and dead/live category weighting independently.

## 5. R2 — Albini-adjusted base ROS — Grade B

PyFireCA explicitly follows the **Albini-adjusted Rothermel** operational line.

Key adjustments locked into the reference include:

```text
combustible loading
Albini reaction-velocity exponent
live moisture of extinction
separate dead/live reaction-intensity contributions
```

The common R1/R2 chain includes:

```text
combustible/net load
SAV size-bin weighted load
mineral damping
moisture damping
live moisture of extinction
reaction velocity / intensity
propagating flux
heat of preignition
effective heating number
heat sink
no-wind/no-slope ROS
```

Pinned Grade B references:

```text
FM1 dead-only
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2 static dead + live
2.3810521029916596 chains/h
0.013305319151517395 m/s
```

FM2 validates static heterogeneous dead/live weighting and live moisture-of-extinction behavior without dynamic curing.

## 6. R3 — wind, slope, and maximum-spread vector

Pinned Grade B references:

```text
FM1, 30% slope, zero wind
20.817222076028628 chains/h

FM1, zero slope, 100 ft/min DirectMidflame wind
8.834274755440232 chains/h

FM1, 30% slope + perpendicular 100 ft/min wind push
21.399596624626479 chains/h maximum ROS
```

Implemented:

```text
slope factor
wind factor
effective-wind inversion
optional operational wind-speed limit
non-collinear wind/slope vector composition
maximum-spread geographic direction
```

Non-collinear effects use:

```text
slope_rate = R0 * phi_s
wind_rate  = R0 * phi_w
x = slope_rate + wind_rate*cos(delta)
y = wind_rate*sin(delta)
Rmax = R0 + hypot(x, y)
```

The perpendicular maximum-spread **magnitude** is independently Grade B. Direction is source-aligned and analytically tested but not falsely promoted to a separate Grade B direction observation.

### Wind-limit detail

The operational limit is optional and disabled by default.

When enabled and exceeded:

```text
effective_wind_speed_m_s = wind_speed_limit_m_s
```

This matters beyond forward ROS because the surface ellipse uses effective wind to determine L/W.

## 7. R4 — public behavior model

Public assembly:

```text
RothermelModel.compute(RothermelInputs)
        ↓
FireBehaviorResult
```

Stable cross-model outputs:

```text
spread_rate_m_s
spread_direction_deg
```

Zero wind + zero slope returns `spread_direction_deg=None` rather than inventing a head direction for an isotropic case.

The following remain intentionally unset:

```text
fireline_intensity_w_m = None
flame_length_m = None
```

They require separate output-equation validation.

Rothermel-specific intermediates stay in `diagnostics` rather than polluting the shared behavior API.

## 8. R5 — dynamic herbaceous curing/load transfer — Grade B

Pinned operational transfer rule:

```text
M_live_herb < 0.30       transfer = 1.0
0.30 <= M <= 1.20       transfer = 1.333 - 1.11*M
M > 1.20                 transfer = 0.0
```

Operational semantics retained:

- transferred dead herb inherits live-herb SAV;
- dead-herb physical properties use dead-fuel properties;
- transferred dead herb uses dead 1-h moisture;
- herbaceous load is conserved;
- redistribution occurs before the shared R1/R2 chain.

Pinned GR1 case:

```text
fuel model            101 / GR1
dead moisture         5/5/5 %
live herb moisture    60 %
live woody moisture   90 %
wind                   0
slope                  0

0.71419316836403091 chains/h
0.003990911424818205 m/s
```

`RothermelModel.compute()` reproduces this result end to end.

## 9. Audited standard-fuel catalogue

Public module:

```text
pyfireca.behavior.fuel_catalog
```

Current deliberately limited audited subset:

```text
1    FM1
2    FM2
101  GR1
```

Native pinned source values are stored first and converted explicitly to the SI `RothermelFuelModel` contract.

Unknown model numbers fail explicitly as not audited yet. PyFireCA does not pretend the full Anderson 13 / Scott–Burgan 40 catalogue has already been reviewed.

## 10. R7 — Behave-aligned surface ellipse and off-axis ROS — Grade B

Surface length-to-width relation:

```text
L/W = 0.936 exp(0.1147 U) + 0.461 exp(-0.0692 U) - 0.397
```

where effective wind `U` is in mph and surface `L/W` is capped at 8.

Then:

```text
e = sqrt((L/W)^2 - 1) / (L/W)
R_back = R_head * (1 - e) / (1 + e)
R_flank = (R_head + R_back) / (2 * L/W)
```

Pinned Behave `FromIgnitionPoint` radial relation:

```text
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

`beta=0°` is heading; `beta=180°` is backing.

Dedicated pinned case:

```text
FM1
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

The dedicated workflow verifies the raw value and official suite state:

```text
172 performed
172 passed
0 failed
```

The 90° radial result is therefore Grade B.

Known FM1 100 ft/min directional values used in tests:

```text
east head       0.04936592733340002 m/s
north/south     0.02921246024622574 m/s
west backing    0.02074385430924511 m/s
NE/SE 45°       0.041067604539224284 m/s
```

PyFireCA does not use `head_ROS*cos(theta)` as an off-axis shortcut.

## 11. R7/R8 — bridge from behavior to raster edges

### Homogeneous provider

```text
HomogeneousRothermelDirectionalSpreadRate
```

It caches one behavior + ellipse and maps each north-up neighbor offset to a geographic bearing and then to `FromIgnitionPoint` directional ROS.

### Static heterogeneous provider

```text
StaticSpatialRothermelDirectionalSpreadRate
```

Contract:

```text
inputs_provider(row, col) -> RothermelInputs
```

One behavior + ellipse is cached per source cell.

Current baseline edge semantic:

> **The source cell determines outgoing edge ROS.**

No source-target averaging is hidden in this provider.

Tests explicitly change wind direction between adjacent source cells so successive outgoing edges use different head/backing behavior.

## 12. R8 — raster input and landscape assembly

Raster input API:

```text
RothermelRasterLayerNames
StaticRasterRothermelInputsProvider
```

Default strict units:

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

No hidden conversion is performed for moisture percentages, percent slope, wind height, or angular conventions.

Required values are checked only inside the explicit simulation domain. Domain-exterior NoData is legal; domain-interior missing/non-finite behavior input fails fast.

Landscape convenience factory:

```text
build_static_raster_rothermel_arrival_solver(...)
```

Assembly:

```text
LandscapeInput
→ typed per-cell Rothermel inputs
→ static heterogeneous directional provider
→ StaticArrivalTimeSolver
```

Current geometry is deliberately limited to north-up square rasters with explicit metric `cell_size_m` matching affine pixel size. Rotated, sheared, rectangular, or mismatched grids fail closed.

Detailed workflow:

```text
docs/STATIC_RASTER_WORKFLOW.md
examples/static_raster_rothermel.py
```

## 13. Physical arrival boundary

Physical travel time remains:

```text
travel_time_s = physical_distance_m / direction_specific_ROS_m_s
```

`StaticArrivalTimeSolver` assumes edge travel times are static and non-negative. It must not be reused unchanged for time-varying weather by mutating cached provider state.

The original synchronous `Simulation` remains a separate reference CA path; no hidden physical `dt` has been assigned to one synchronous step.

## 14. Reproducible official workflows

```text
.github/workflows/behave7-r2-probe.yml
.github/workflows/behave7-r3-vector.yml
.github/workflows/behave7-r5-dynamic-probe.yml
.github/workflows/behave7-r7-directional.yml
```

These cover base ROS, wind/slope, dynamic GR1 curing, and off-axis radial spread respectively.

## 15. Current scope boundary

**Implemented and validated enough for controlled CA research:**

```text
static/dynamic-herbaceous surface-fuel Rothermel behavior
wind + slope maximum-spread behavior
off-axis surface ellipse
static directional neighbor ROS
physical edge travel time
static earliest arrival
static spatially heterogeneous raster inputs
north-up square-raster landscape assembly
```

**Not yet implemented/validated:**

```text
full standard-fuel catalogue
source-target/interface edge coupling alternatives
affine-aware rotated/non-square geometry
time-dependent weather scheduler
fireline intensity output
flame length output
FBP
crown fire
spotting
suppression
```

## 16. Next scientific stage

The next useful work is not more Rothermel algebra. Keep the behavior reference fixed and study CA discretization:

```text
source-cell edge ROS baseline                       ✓
        ↓
explicit source/target interface variants
        ↓
4 / 8 / extended neighborhoods
        ↓
cell-size sensitivity
        ↓
lattice directional bias
        ↓
arrival-time + perimeter/shape error
```

Only after a controlled static benchmark exists should PyFireCA design a time-dependent weather scheduler. Dynamic weather violates the static shortest-path assumption because an edge's ROS may change while fire is traversing it.

## 17. Validation discipline

Do not weaken tolerances, mix equation variants, overwrite pinned fixtures, or silently alter edge semantics merely to make a test pass.

When evidence differs, label it explicitly rather than upgrading an analytical/internal check to Grade B/A without independent external output.
