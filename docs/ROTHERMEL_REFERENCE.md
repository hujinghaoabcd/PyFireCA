# Rothermel Reference Implementation Plan

> Status: active implementation/validation plan
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

The implementation is derived from published equations and authoritative explanatory material rather than copied from another software package.

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

The six-class structure allows the public input contract to represent classic/static models and later dynamic Scott--Burgan-style behavior without redesigning the API.

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

The published Rothermel correlations use US customary quantities such as feet, pounds, Btu, and minutes. PyFireCA therefore centralizes exact conversions in `src/pyfireca/behavior/_units.py` rather than scattering constants through scientific formulas.

Currently implemented and round-trip tested conversions cover:

```text
m ↔ ft
kg/m² ↔ lb/ft²
kg/m³ ↔ lb/ft³
1/m ↔ 1/ft
J/kg ↔ Btu/lb
m/s ↔ ft/min
```

No conversion depends on guessing a value's likely unit.

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

The current class does not yet embed Anderson 13 or Scott--Burgan 40 lookup tables. Catalogue data are deferred until source values, conversions, provenance, and regression tests are prepared.

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

Live moisture values are allowed to exceed `1.0` because dry-mass-basis moisture can exceed 100 percent.

Dynamic herbaceous load transfer is **not implemented yet**. The `dynamic` flag only preserves the capability needed for that later step.

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

### Wind direction

`wind_from_direction_deg` is a meteorological **from** direction:

```text
0°   wind from north
90°  wind from east
180° wind from south
270° wind from west
```

Any conversion to downwind/spread direction must be explicit in the equation implementation.

### Slope and aspect

- `slope_deg` is constrained to `[0, 90)`.
- `aspect_deg` is clockwise from geographic north and constrained to `[0, 360)`.

Raster row orientation must never silently redefine geographic direction conventions.

## 8. R1 — implemented base fuel quantities

R1 is now partially implemented with small pure functions and hand-computable tests.

### Surface-area weighting

`compute_surface_area_weights()` implements the heterogeneous-fuel weighting structure based on per-class relative surface area proportional to:

```text
SAV × oven-dry load / particle density
```

It returns:

- six within-category weights for dead/live fuel size classes;
- two category weights for total dead vs live fuel surface area.

The tests use an artificial three-loaded-class fuel bed so the expected fractions can be verified analytically rather than against another software package.

### Characteristic SAV

`compute_characteristic_sav_m_inv()` computes the surface-area-weighted characteristic SAV from the same dead/live and within-category weights.

### Packing ratio

`compute_packing_ratio()` computes occupied particle volume per fuel-bed volume from:

```text
sum(load / particle_density) / fuel-bed depth
```

### Oven-dry bulk density

`compute_bulk_density_kg_m3()` computes total oven-dry load divided by fuel-bed depth.

### Optimum packing ratio

`compute_optimum_packing_ratio()` evaluates the published correlation after explicitly converting characteristic SAV from `1/m` to `1/ft`, because the correlation coefficients are tied to the legacy unit convention.

### R1 validation status

Tests currently cover:

- exact dead/live surface-area weights for a hand-computable synthetic fuel bed;
- characteristic SAV;
- packing ratio;
- bulk density;
- optimum packing ratio at a known characteristic SAV input;
- zero behavior for a nonburnable model;
- invalid negative SAV rejection;
- exact/round-trip unit conversions.

The R1 tests pass in the Python 3.11/3.12/3.13 matrix. Quality failures encountered while adding them have been lint/format-only and are corrected as part of the same development pass.

## 9. R2 — no-wind / no-slope surface spread

R2 is deliberately **not implemented yet**.

Before coding reaction intensity and base ROS, PyFireCA must reconcile which published equation variants constitute its reference behavior. The original 1972 model and later Albini/Andrews operational formulations are not identical in every intermediate expression.

At minimum, R2 must explicitly resolve and document:

- the Albini replacement for the reaction-velocity exponent/correlation used in later implementations;
- the exact net-fuel-loading convention used by the selected reference formulation;
- live moisture-of-extinction treatment;
- dynamic herbaceous curing boundaries;
- whether a given correction belongs to the core Rothermel reference or to a named later extension.

Do **not** mix formulas from different vintages simply because they appear in existing software.

The next implementation should first create authoritative numerical fixtures for the selected formulation, then add formula-level functions for:

- mineral damping;
- moisture damping;
- net fuel loading;
- reaction velocity/intensity;
- propagating flux ratio;
- effective heating number;
- heat of preignition;
- heat source/sink;
- no-wind/no-slope ROS.

## 10. Later implementation stages

### R3 — wind and slope effects

Add wind and slope factors only after R2 is independently validated. Directional/vector conventions must be tested separately from scalar base ROS.

### R4 — common PyFireCA output

Implement `RothermelModel.compute(RothermelInputs) -> FireBehaviorResult` with SI output.

### R5 — standard fuel catalogues

Add independently verified Anderson/Scott--Burgan catalogue data and conversion tests only after the equation path is stable.

### R6 — behavior-informed CA integration

Use Rothermel output from a CA rule without adding model-name branches to `Simulation`.

## 11. Validation strategy

Each equation stage uses three levels where possible:

```text
formula-level test
        ↓
authoritative complete/reference calculation
        ↓
independent software comparison
```

Independent software comparison paths include SimFire and Pyretechnics only when the compared assumptions/variants are scientifically equivalent.

Differences must be diagnosed rather than hidden by loose tolerances. Potential causes include:

- equation vintage/correction set;
- unit conversion;
- wind convention;
- wind adjustment;
- dynamic-fuel handling;
- live moisture-of-extinction treatment;
- directional projection assumptions.

## 12. License / provenance rule

PyFireCA's Rothermel implementation is an independent implementation of published scientific equations.

Do not copy source text from reference software with different licensing. When a reference implementation reveals a discrepancy, return to the scientific reference, document the interpretation, and add a test capturing the resolved behavior.

## 13. Explicitly deferred

Not yet implemented:

- complete no-wind/no-slope equation chain;
- wind/slope equation chain;
- standard fuel catalogue constants;
- dynamic herbaceous curing;
- live moisture-of-extinction calculation;
- canopy wind-adjustment factors;
- crown fire;
- spotting;
- ellipse/wavelet propagation;
- CA distance accumulation.

These are added incrementally and independently validated.
