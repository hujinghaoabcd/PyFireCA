# Rothermel Reference Implementation Plan

> Status: implementation/validation plan
>
> Updated: 2026-08-12

## 1. Role in PyFireCA

Rothermel is the first fire-behavior family selected for a readable PyFireCA reference implementation.

This is a **development-order decision**, not a statement that Rothermel is preferred over FBP for all wildfire CA research. FBP remains required for later Cell2Fire-oriented comparisons.

Rothermel is implemented first because PyFireCA can compare its calculations against multiple independent paths while keeping the CA propagation logic unchanged.

The intended boundary is:

```text
RothermelFuelModel
       +
RothermelFuelMoisture
       +
wind / slope / aspect
       ↓
RothermelInputs
       ↓
Rothermel behavior calculation
       ↓
FireBehaviorResult
       ↓
CA transition rule
```

## 2. Primary scientific references

The implementation should be derived from published equations and authoritative explanatory material rather than copied from another software package.

Primary references:

1. Rothermel, R. C. (1972). *A mathematical model for predicting fire spread in wildland fuels*. USDA Forest Service Research Paper INT-115.
2. Albini, F. A. (1976). *Estimating wildfire behavior and effects*. USDA Forest Service General Technical Report INT-30.
3. Andrews, P. L. (2018). *The Rothermel surface fire spread model and associated developments: A comprehensive explanation*. USDA Forest Service RMRS-GTR-371. DOI: `10.2737/RMRS-GTR-371`.
4. Scott, J. H., & Burgan, R. E. (2005). *Standard fire behavior fuel models: A comprehensive set for use with Rothermel's surface fire spread model*. USDA Forest Service RMRS-GTR-153. DOI: `10.2737/RMRS-GTR-153`.

Independent software implementations such as SimFire and Pyretechnics are comparison targets, not sources to copy.

## 3. Six-class fuel ordering

PyFireCA fixes the Rothermel fuel-class order as:

```text
0  DEAD_1H
1  DEAD_10H
2  DEAD_100H
3  DEAD_HERBACEOUS
4  LIVE_HERBACEOUS
5  LIVE_WOODY
```

The six-class structure is chosen so the input contract can represent classic/static models as well as later dynamic Scott--Burgan-style fuel behavior without redesigning the public data structure.

A model with no load in a class stores zero load. Physical particle properties for an unloaded class may also be zero because they do not participate in the calculation.

## 4. Public-unit policy

The PyFireCA public Rothermel contract uses SI units:

| Quantity | PyFireCA unit |
| --- | --- |
| fuel-bed depth | m |
| fuel load | kg/m² |
| surface-area-to-volume ratio | 1/m |
| heat content | J/kg |
| particle density | kg/m³ |
| moisture | dry-mass fraction |
| wind speed | m/s |
| slope | degrees |
| direction/aspect | degrees clockwise from geographic north |

Published/reference implementations may use ft, lb, Btu, minutes, or other native conventions. Any legacy-unit conversion required by the reference equation implementation must be explicit, named, and tested.

No conversion should depend on guessing a value's likely unit.

## 5. Fuel-model contract

`RothermelFuelModel` currently stores:

```text
code
depth_m
dead_moisture_of_extinction_fraction
loads_kg_m2[6]
sav_ratio_m_inv[6]
heat_content_j_kg[6]
particle_density_kg_m3[6]
total_mineral_fraction[6]
effective_mineral_fraction[6]
dynamic
burnable
```

For burnable models:

- fuel-bed depth must be positive;
- dead moisture of extinction must be positive;
- total load must be positive;
- each loaded class must have positive SAV ratio, heat content, and particle density.

Nonburnable models may use zero-valued physical properties.

The current class does not yet embed Anderson 13 or Scott--Burgan 40 lookup tables. Catalogue data should be added only after source values, unit conversions, tests, and citation provenance are prepared.

## 6. Moisture contract

External moisture inputs are currently:

```text
dead_1h_fraction
dead_10h_fraction
dead_100h_fraction
live_herbaceous_fraction
live_woody_fraction
```

`RothermelFuelMoisture.as_six_class_values()` expands them to the six-class order by initially assigning dead-herbaceous moisture from dead 1-h moisture.

Live moisture values are allowed to exceed `1.0` because moisture expressed on a dry-mass basis can exceed 100 percent.

Dynamic herbaceous load transfer is **not implemented yet**. The `dynamic` flag only preserves the fuel-model capability needed for that later step.

## 7. Wind and terrain conventions

`RothermelInputs` currently uses:

```text
midflame_wind_speed_m_s
wind_from_direction_deg
slope_deg
aspect_deg
```

### Midflame wind

The Rothermel input receives midflame wind directly. Conversion from 10-m or 20-ft wind using a wind-adjustment factor belongs in a separate explicit preprocessing/behavior utility.

This keeps the Rothermel calculation independent of canopy/exposure assumptions that are not intrinsic to its basic input contract.

### Wind direction

`wind_from_direction_deg` is a meteorological **from** direction:

```text
0°   wind from north
90°  wind from east
180° wind from south
270° wind from west
```

Any conversion to a downwind/spread vector must be explicit in the equation implementation.

### Slope and aspect

- `slope_deg` is constrained to `[0, 90)`.
- `aspect_deg` is clockwise from geographic north and constrained to `[0, 360)`.

Image-row orientation must never be allowed to silently redefine geographic direction conventions.

## 8. Implementation stages

Do not implement the model as one monolithic function.

Recommended sequence:

### R1 — unit conversion and base fuel quantities

Implement/test explicit conversions needed by published equations and derive base quantities such as:

- net fuel load;
- bulk density;
- packing ratio;
- optimum packing ratio;
- weighted fuel characteristics.

### R2 — no-wind / no-slope surface spread

Implement/test the reaction and heat-transfer chain required for base surface ROS.

This gives a clean reference case before directional effects are introduced.

### R3 — wind and slope effects

Add wind and slope factors with explicit direction conventions.

Separate vector/directional handling from scalar base ROS where practical.

### R4 — common PyFireCA output

Return validated `FireBehaviorResult` values in SI units.

### R5 — standard fuel catalogues

Add independently verified Anderson/Scott--Burgan catalogue data and conversion tests only after the equation path is stable.

### R6 — behavior-informed CA integration

Use Rothermel output from a CA rule without adding `if model == "rothermel"` logic to `Simulation`.

## 9. Validation strategy

Each equation stage should have tests at three levels:

```text
formula-level unit test
        ↓
complete reference calculation
        ↓
independent implementation comparison
```

Planned comparison sources include:

- authoritative worked/reference values when available;
- SimFire for an independent NumPy-oriented implementation path;
- Pyretechnics for a richer multi-class implementation path.

Differences must be diagnosed rather than hidden by loose tolerances. Potential causes include:

- unit conversion;
- wind convention;
- wind adjustment;
- dynamic-fuel handling;
- Albini/Behave-era corrections;
- directional projection assumptions.

## 10. License / provenance rule

PyFireCA's Rothermel implementation must be an independent implementation of published scientific equations.

Do not copy source text from reference software with incompatible or different licensing. When a reference implementation reveals a discrepancy, return to the scientific reference, document the interpretation, and add a test that captures the resolved behavior.

## 11. Explicitly deferred

Not yet part of the Rothermel implementation:

- equation chain itself;
- standard fuel catalogue constants;
- dynamic herbaceous curing calculation;
- live moisture-of-extinction calculation;
- canopy wind-adjustment factors;
- crown fire;
- spotting;
- ellipse/wavelet propagation;
- CA distance accumulation.

These should be added incrementally and validated independently.
