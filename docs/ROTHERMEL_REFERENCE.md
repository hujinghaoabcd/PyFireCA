# Rothermel Reference Implementation

> Status: **R1–R4 implemented for static surface fuels**
>
> Updated: 2026-08-12

## 1. Role in PyFireCA

Rothermel is the first fire-behavior family implemented as a readable scientific reference. This is a development-order decision, not a claim that Rothermel is preferable to FBP for every wildfire CA problem.

Current boundary:

```text
RothermelFuelModel + RothermelFuelMoisture + wind/slope/aspect
                         ↓
                   RothermelInputs
                         ↓
                  RothermelModel
                         ↓
                 FireBehaviorResult
                         ↓
                  CA transition rule
```

Fire-behavior equations remain separate from CA propagation.

## 2. Scientific references and validation software

Primary scientific references:

1. Rothermel (1972), USDA Forest Service Research Paper INT-115.
2. Albini (1976), USDA Forest Service GTR INT-30.
3. Andrews (2018), USDA Forest Service RMRS-GTR-371, DOI `10.2737/RMRS-GTR-371`.
4. Scott & Burgan (2005), USDA Forest Service RMRS-GTR-153, DOI `10.2737/RMRS-GTR-153`.

Pinned official operational regression source:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave core
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

PyFireCA independently implements the equations and uses the pinned software only as an external numerical reference.

Evidence grades:

```text
Grade A  primary/authoritative worked value
Grade B  pinned official operational software regression
Grade C  independent software comparison
Grade D  internal analytical/synthetic fixture
```

## 3. Public fuel and unit contracts

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
| wind | m/s |
| slope | degrees |
| direction | degrees clockwise from north |

Published ft/lb/Btu/min correlations are evaluated only after explicit conversion through `behavior/_units.py`.

`RothermelInputs` receives **midflame wind** directly. 10-m/20-ft wind adjustment is an external preprocessing concern.

Direction semantics:

```text
aspect                 geographic downslope bearing
wind_from_direction    meteorological from-bearing
wind push              wind_from + 180°
upslope                 aspect + 180°
```

These conversions live in `_directions.py`; raster row orientation never changes geographic angle semantics.

## 4. R1 — heterogeneous fuel-bed quantities — complete

Implemented in `behavior/rothermel.py`:

```text
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
```

Surface-area weighting uses relative area proportional to:

```text
SAV × oven-dry load / particle density
```

Synthetic hand-computable tests verify within-dead/live and dead/live-category weighting independently.

## 5. R2 formulation — Albini-adjusted Rothermel

The implementation explicitly follows the operational **Albini-adjusted Rothermel** line.

Locked Albini adjustments include:

### A1 — combustible loading

```text
w_n = w_0 × (1 - S_T)
```

### A2 — reaction-velocity exponent

```text
A = 133 × sigma^-0.7913
```

with `sigma` in inverse feet for this empirical relation.

### A3 — live moisture of extinction

```text
fine_dead = Σ load_dead × exp(-138 / SAV_dead)
fine_live = Σ load_live × exp(-500 / SAV_live)
```

followed by the Albini live-Mx relation and dead-Mx lower bound.

### A4 — dead/live reaction intensity

Dead and live contributions are calculated separately and added at the final reaction-intensity stage.

## 6. R2 implementation — complete for static fuels

`behavior/_rothermel_equations.py` contains independently testable functions for:

```text
combustible/net load
SAV size-bin weighted combustible load
mineral damping
moisture damping
live moisture of extinction
Albini reaction-velocity exponent
maximum reaction velocity
actual reaction velocity
reaction intensity
propagating flux
heat of preignition
effective heating number
preignition heat term
heat sink
no-wind/no-slope spread rate
```

Operational SAV load bins use the native inverse-foot boundaries:

```text
>= 1200
>= 192
>= 96
>= 48
>= 16   1/ft
```

`behavior/_rothermel_base.py` assembles the R1 and R2 stages.

It exposes:

```text
BaseSpreadResult
compute_base_spread_result(...)
compute_base_spread_rate_m_s(...)
```

The richer result carries downstream quantities such as reaction intensity, characteristic SAV, packing ratios, propagating flux, and heat sink without recomputing R2.

## 7. Grade B base-ROS validation — complete

### FM1 — dead-only

Pinned inputs include:

```text
fuel-bed depth        1.0 ft
dead Mx               0.12
1-h load              0.034 lb/ft²
1-h SAV               3500 1/ft
heat content          8000 Btu/lb
particle density      32 lb/ft³
total mineral         0.0555
effective mineral     0.01
dead moisture         5/5/5 %
midflame wind         0
slope                 0
```

Pinned official Behave result:

```text
4.4262698923571939 chains/hour
0.024733996158492002 m/s
```

### FM2 — static dead + live

FM2 is used to validate live-fuel heterogeneity without dynamic curing/load transfer.

Pinned official Behave result:

```text
2.3810521029916596 chains/hour
0.013305319151517395 m/s
```

The pinned FM2 live moisture of extinction is:

```text
11.63009861291455 dry-mass fraction
```

This validates static dead/live weighting, size-bin loading, live Mx, moisture damping, dead/live reaction addition, heat sink, and final base ROS together.

## 8. R3a — slope — Grade B validated

Pinned case:

```text
FM1
dead moisture 5/5/5%
30% slope
zero wind
```

Official result:

```text
20.817222076028628 chains/hour
```

Public PyFireCA input converts 30% slope to:

```text
atan(0.3) = 16.69924423399362 degrees
```

The scalar relation is:

```text
phi_s = 5.275 * beta^-0.3 * tan(slope)^2
```

## 9. R3b — wind — Grade B validated

Pinned case:

```text
FM1
zero slope
100 ft/min direct-midflame wind
```

Official result:

```text
8.834274755440232 chains/hour
```

The operational wind correlation is evaluated in its native units:

```text
C = 7.47 * exp(-0.133 * sigma^0.55)
B = 0.02526 * sigma^0.54
E = 0.715 * exp(-0.000359 * sigma)

phi_w = C * U^B * (beta / beta_op)^(-E)
```

with `sigma` in 1/ft and `U` in ft/min.

## 10. R3c — effective wind and optional wind limit

PyFireCA implements:

```text
compute_effective_wind_speed_m_s
compute_wind_speed_limit_m_s
apply_wind_speed_limit
```

The operational limit is optional and **disabled by default**.

FM1 reference quantities:

```text
reaction intensity     159495.8270605292 W/m²
wind-speed limit       758.3986638051593 ft/min
                       3.85266521213021 m/s
limited high-wind ROS  1.6614603649165824 m/s
```

The pinned official workflow validates the ROS produced at the calculated boundary wind speed:

```text
297.3264790473483 chains/hour
```

Python tests independently validate the enable/disable, threshold, inversion, and capping behavior. The official workflow intentionally avoids a custom C++ probe.

## 11. R3d — non-collinear wind+slope vector — Grade B magnitude validated

For non-collinear effects, scalar addition is not valid.

```text
slope_rate = R0 * phi_s
wind_rate  = R0 * phi_w

x = slope_rate + wind_rate*cos(delta)
y = wind_rate*sin(delta)
additional = hypot(x, y)
Rmax = R0 + additional
```

Pinned perpendicular case:

```text
FM1
30% slope
100 ft/min direct-midflame wind
wind push 90° from upslope
```

Expected and official Behave maximum ROS:

```text
21.399596624626479 chains/hour
```

The dedicated `.github/workflows/behave7-r3-vector.yml` regression passes.

The corresponding PyFireCA analytical direction is:

```text
15.052373502770299° clockwise from upslope
```

Direction is verified analytically and aligned to the Behave vector source path. The external CSV regression validates maximum-spread **magnitude**, so direction is not mislabelled as Grade B external output.

## 12. R4 — public model assembly — complete

`behavior/rothermel_model.py` implements:

```text
RothermelModel.compute(RothermelInputs)
        ↓
FireBehaviorResult
```

Assembly order:

```text
validated BaseSpreadResult
        ↓
phi_s + phi_w
        ↓
non-collinear vector composition
        ↓
effective wind
        ↓
optional wind limit
        ↓
relative-to-upslope direction
        ↓
geographic bearing
        ↓
FireBehaviorResult
```

Current cross-model outputs:

```text
spread_rate_m_s
spread_direction_deg
```

When both wind and slope directional effects are zero, `spread_direction_deg=None`; PyFireCA does not invent a head direction for an isotropic base-ROS case.

The following are intentionally still unset:

```text
fireline_intensity_w_m = None
flame_length_m = None
```

They require separate output-equation validation.

Rothermel-specific diagnostics include:

```text
base_spread_rate_m_s
reaction_intensity_w_m2
characteristic_sav_m_inv
packing_ratio
relative_packing_ratio
wind_factor
slope_factor
effective_factor
effective_wind_speed_m_s
wind_speed_limit_m_s
wind_limit_enabled
wind_limit_exceeded
```

End-to-end tests cover base, slope-only, wind-only, perpendicular wind+slope, high-wind limiting, dynamic-fuel rejection, and API type validation.

## 13. Reproducible official workflows

```text
.github/workflows/behave7-r2-probe.yml
.github/workflows/behave7-r3-vector.yml
```

The first verifies:

```text
FM1 base
FM2 static live-fuel base
FM1 slope-only
FM1 wind-only
FM1 wind-limit boundary
```

The second verifies the perpendicular wind+slope maximum ROS.

The only modification made to the upstream official `testSurface` source is additional output precision where needed; scientific equations are not patched.

## 14. Current scope boundary

**Implemented and validated enough for CA coupling:**

```text
static heterogeneous surface-fuel base ROS
wind effect
slope effect
non-collinear maximum-spread magnitude
explicit geographic maximum-spread direction
optional operational wind limit
public RothermelModel output
```

**Not yet implemented/validated:**

```text
dynamic herbaceous curing/load transfer
standard fuel catalogue provenance as a public catalogue API
fireline intensity output
flame length output
off-axis elliptical directional spread
crown fire
spotting
```

## 15. Next scientific stage

The next step is not more R2 algebra. It is:

```text
verified standard fuel catalogue
        ↓
dynamic herbaceous curing/load transfer
        ↓
behavior-informed CA rule
        ↓
continuous ROS/direction → neighbor travel/arrival time
        ↓
spread-shape and arrival-time validation
```

The CA layer should consume `FireBehaviorResult`; `Simulation` must not branch on the string/name of the behavior model.

## 16. Validation discipline

Do not weaken tolerances, mix equation variants, or overwrite external fixtures merely to make tests pass.

When evidence differs, label it explicitly rather than upgrading an internal analytical check to Grade B/A without an independent external output.
