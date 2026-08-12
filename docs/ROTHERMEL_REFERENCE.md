# Rothermel Reference Implementation Plan

> Status: active implementation / validation plan
>
> Updated: 2026-08-12

## 1. Role in PyFireCA

Rothermel is the first fire-behavior family implemented as a readable scientific reference. This is a development-order decision, not a claim that Rothermel is preferable to FBP for every wildfire CA problem.

Target boundary:

```text
RothermelFuelModel + RothermelFuelMoisture + wind/slope/aspect
                         ↓
                   RothermelInputs
                         ↓
              Rothermel behavior model
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

Official operational regression source used for Grade B validation:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave core
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

PyFireCA does not copy reference-program source code. The pinned operational implementation is used to verify interpretation and numerical output of independently implemented published equations.

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

## 4. R1 — heterogeneous fuel-bed quantities — complete

Implemented in `behavior/rothermel.py`:

```text
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
```

Surface-area weighting is based on relative area proportional to:

```text
SAV × oven-dry load / particle density
```

The result contains within-dead/live class weights and dead/live category weights. Synthetic hand-computable tests independently verify the weighting logic.

## 5. R2 formulation — Albini-adjusted Rothermel

The implementation explicitly follows the operational **Albini-adjusted Rothermel** line rather than an unnamed mixture of equation vintages.

Locked Albini adjustments:

### A1 — combustible loading

```text
w_n = w_0 × (1 - S_T)
```

### A2 — reaction-velocity exponent

```text
A = 133 × sigma^-0.7913
```

with `sigma` in inverse feet for this empirical correlation.

### A3 — live moisture of extinction

Fine-fuel weighting:

```text
fine_dead = Σ load_dead × exp(-138 / SAV_dead)
fine_live = Σ load_live × exp(-500 / SAV_live)
```

followed by the Albini live-Mx relation and the dead-Mx lower bound.

### A4 — dead/live reaction intensity

Dead and live reaction-intensity contributions are calculated separately and **added** at the final intensity stage.

## 6. R2 formula-level implementation — complete for static fuels

`behavior/_rothermel_equations.py` now contains independently testable functions for:

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

The operational SAV load bins are explicitly represented using the published/native inverse-foot boundaries:

```text
>= 1200
>= 192
>= 96
>= 48
>= 16   1/ft
```

`behavior/_rothermel_base.py` assembles these R2 functions with the validated R1 heterogeneous fuel quantities.

## 7. Grade B zero-wind / zero-slope validation — complete

### FM1 — dead-only case

Pinned inputs:

```text
Fuel Model 1
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

PyFireCA's complete typed SI base-ROS chain matches this reference with a tight numerical tolerance.

### FM2 — static dead + live case

FM2 was deliberately chosen instead of a dynamic Scott--Burgan model because it includes nonzero live fuel while avoiding dynamic herbaceous load transfer.

Pinned fuel inputs include:

```text
dead loads        0.092 / 0.046 / 0.023 lb/ft²
live herb load    0.023 lb/ft²
dead SAV          3000 / 109 / 30 1/ft
live herb SAV     1500 1/ft
dead Mx           0.15
dead moisture     5/5/5 %
live herb         100 %
midflame wind     0
slope             0
```

Pinned official Behave result:

```text
2.3810521029916596 chains/hour
0.013305319151517395 m/s
```

This validates, together in one complete static heterogeneous case:

- dead + live surface-area weighting;
- SAV size-bin weighted combustible loading;
- Albini live moisture of extinction;
- dead and live moisture damping;
- dead + live reaction-intensity addition;
- heterogeneous heat sink;
- final no-wind/no-slope ROS.

The FM2 live moisture of extinction for the pinned case is:

```text
11.63009861291455 dry-mass fraction
```

The large value is a direct consequence of the Albini fine-dead/fine-live ratio for this low-live-load static fuel model; it is not clamped to 1.0 because moisture of extinction is not a probability.

## 8. Reproducible official regression workflow

`.github/workflows/behave7-r2-probe.yml` now acts as a pinned official reference regression despite its historical filename.

It:

1. checks out the exact Behave app/core commits;
2. builds the official `testSurface` executable;
3. patches only output stream precision, not scientific equations;
4. verifies FM1 and FM2 zero-wind/zero-slope expected values;
5. requires `1 passed / 0 failed` for each case.

Permanent fixture files:

```text
tests/validation/data/behave7_r2_zero_wind_zero_slope.csv
tests/validation/data/behave7_r2_live_fuel_zero_wind_zero_slope.csv
```

Fixture-integrity tests protect provenance and values from silent edits.

## 9. Current R2 scope boundary

**Validated:** static heterogeneous no-wind/no-slope surface ROS.

**Not yet validated/implemented:**

```text
dynamic herbaceous curing/load transfer
wind factor
slope factor
combined wind+slope direction
wind-speed limit / operational wind treatment
complete RothermelModel.compute() output
```

`compute_base_spread_rate_m_s()` deliberately raises for `fuel.dynamic=True` until load transfer is implemented explicitly.

## 10. R3 — wind and slope — next scientific stage

R3 starts only from the now-validated base ROS.

Work order:

```text
slope factor scalar validation
        ↓
wind factor scalar validation
        ↓
effective wind / wind-limit rules
        ↓
combined wind+slope vector direction
        ↓
off-axis directional spread checks
```

Direction conventions must remain separate from scalar factor validation:

- input wind is meteorological **from** direction;
- spread/downwind conversion is explicit;
- aspect is clockwise from geographic north;
- raster row orientation never changes geographic angle semantics.

## 11. R4 — common behavior output

After R3 is validated:

```text
RothermelModel.compute(RothermelInputs)
        ↓
FireBehaviorResult
```

At minimum the result will expose SI spread rate and direction; intensity/flame length will be added only where their calculation path is separately validated.

## 12. R5 / R6 later stages

R5:
- verified Anderson / Scott--Burgan fuel catalogue values;
- explicit dynamic herbaceous transfer;
- catalogue provenance and conversion tests.

R6:
- behavior-informed CA transition rule;
- no model-name branches in `Simulation`.

## 13. Validation discipline

Evidence grades remain:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent software comparison
Grade D  internal analytical/synthetic fixture
```

Do not weaken tolerances, mix equation variants, or overwrite external fixtures merely to make tests pass.
