# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: continue development without reconstructing scientific or architectural context from chat history.

## 1. Identity and protected scope

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. The primary research target remains the CA; fire-behavior models provide physically meaningful local spread inputs to that CA.

Protected extension points:

```text
State
Neighborhood
Transition Rule
Time stepping / scheduler
```

Do not casually reverse these decisions:

1. wildfire-specific scope;
2. NumPy is the scientific reference path;
3. Numba only after profiling;
4. Torch/JAX/GPU/differentiable CA deferred;
5. Level Set/front tracking are comparison methods only;
6. fire behavior and CA propagation remain separate;
7. GIS I/O stays outside numerical kernels;
8. behavior outputs standardized, model-native inputs remain typed/model-specific;
9. Rothermel first, FBP later;
10. Rothermel public inputs use explicit SI units and midflame wind;
11. R2 is explicitly **Albini-adjusted Rothermel**;
12. wind and slope are vector-combined when non-collinear;
13. meteorological wind-from, downwind push, downslope aspect, and upslope bearing are separate concepts;
14. the optional operational wind limit defaults to disabled;
15. external numerical references carry evidence grades and pinned provenance;
16. GIS alignment, domain semantics, and dynamic missing-data handling are explicit rather than inferred.

## 2. Current source tree

```text
src/pyfireca/
├── __init__.py
├── state.py
├── grid.py
├── neighborhood.py
├── rules.py
├── simulation.py
├── data.py
├── gis.py
└── behavior/
    ├── __init__.py
    ├── base.py
    ├── _units.py
    ├── _directions.py
    ├── rothermel.py
    ├── _rothermel_equations.py
    ├── _rothermel_base.py
    ├── _rothermel_effects.py
    ├── _rothermel_vectors.py
    └── rothermel_model.py
```

Do not create empty future modules merely to match an architecture diagram.

## 3. CA core truth

Canonical states:

```text
UNBURNABLE = 0
UNBURNED   = 1
BURNING    = 2
BURNED     = 3
```

Reference transitions are **synchronous**. `TransitionRule.next_state()` reads the complete old state and returns a complete next state; `Simulation` replaces the grid only after evaluation finishes.

`NeighborIgnitionRule` remains an architecture-only baseline, not physical wildfire behavior.

`build_initial_state(domain_mask, ignition_mask)` maps domain/ignition explicitly and rejects ignition outside the domain.

## 4. Behavior/data contract

CA-facing behavior output:

```text
spread_rate_m_s            required
spread_direction_deg       optional, [0, 360), clockwise from north
fireline_intensity_w_m     optional
flame_length_m              optional
diagnostics                 optional
```

For current `RothermelModel`:

- spread rate is implemented;
- maximum-spread direction is implemented when a directional effect exists;
- zero-wind/zero-slope returns `spread_direction_deg=None`;
- `fireline_intensity_w_m=None`;
- `flame_length_m=None`;
- Rothermel-specific validated intermediate quantities live in `diagnostics`.

Do not populate intensity/flame-length fields until their output paths receive independent validation.

`SpatialLayer` supports `(Y, X)` and `(T, Y, X)`. `EnvironmentalData` requires one spatial shape and one dynamic time length.

```text
snapshot(...)
    policy-free array access

require_complete_snapshot(required_layers, time_index=...)
    explicit fail-fast gate
```

Missing dynamic inputs are never silently filled or converted into persistent domain state.

## 5. GIS baseline — stable and paused

Implemented:

```text
RasterMetadata
RasterAlignmentError
validate_raster_alignment
validate_named_raster_alignment
read_raster
write_raster
write_state_raster
nodata_mask
build_domain_mask
LandscapeInput
```

Alignment requires identical shape, canonical CRS, and affine transform within explicit tolerance. Simulation never silently reprojects/resamples.

NoData rule:

> **NoData is metadata until explicitly converted into domain semantics.**

Only explicitly selected static layers may define persistent `UNBURNABLE` cells. Dynamic missing wind/moisture uses the fail-fast snapshot gate instead.

State GeoTIFF:

```text
dtype          uint8
state codes    0..3
GeoTIFF NoData None
```

## 6. Rothermel public input truth

Fixed six-class order:

```text
DEAD_1H
DEAD_10H
DEAD_100H
DEAD_HERBACEOUS
LIVE_HERBACEOUS
LIVE_WOODY
```

`RothermelInputs`:

```text
fuel
moisture
midflame_wind_speed_m_s
wind_from_direction_deg
slope_deg
aspect_deg
```

Conventions:

- wind speed is **midflame**;
- wind direction is meteorological **from** direction;
- aspect is geographic **downslope** bearing;
- public geographic bearings are clockwise from north;
- 10-m/20-ft wind adjustment remains external.

## 7. R1 — complete

Implemented and tested:

```text
SI ↔ ft/lb/Btu/min conversions
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
```

## 8. R2 — validated static heterogeneous base ROS

Target formulation:

> **Albini-adjusted Rothermel surface fire**

Implemented:

```text
combustible/net loading
SAV size-bin weighted combustible load
mineral damping
moisture damping
live moisture of extinction
Albini reaction-velocity exponent
maximum and actual reaction velocity
dead/live reaction intensity
propagating flux
heat-of-preignition/effective-heating terms
heat sink
no-wind/no-slope ROS
```

`_rothermel_base.py` exposes:

```text
BaseSpreadResult
compute_base_spread_result(...)
compute_base_spread_rate_m_s(...)
```

The latter remains a compatibility wrapper.

Pinned Grade B references:

```text
FM1
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2 static dead+live
2.3810521029916596 chains/h
0.013305319151517395 m/s
```

Dynamic fuel models still raise until herbaceous load transfer is explicit.

## 9. R3 — wind, slope, and direction

### R3a slope

Pinned FM1 30% slope, zero-wind result:

```text
20.817222076028628 chains/h
```

Public slope is degrees, so 30% slope is `atan(0.3)` in the model input.

### R3b wind

Pinned FM1 zero-slope, 100 ft/min direct-midflame result:

```text
8.834274755440232 chains/h
```

### R3c optional wind limit

FM1 reference quantities:

```text
reaction intensity 159495.8270605292 W/m²
limit              758.3986638051593 ft/min
                   3.85266521213021 m/s
limited ROS        1.6614603649165824 m/s
```

`RothermelModel(use_wind_speed_limit=False)` is the default.

The official pinned Behave regression validates ROS at the computed boundary wind speed. Python unit tests validate enable/exceeded/capping semantics.

### R3d non-collinear vector composition

Do **not** use `1 + phi_w + phi_s` for non-collinear wind and slope.

```text
slope_rate = R0 * phi_s
wind_rate  = R0 * phi_w
x = slope_rate + wind_rate*cos(delta)
y = wind_rate*sin(delta)
Rmax = R0 + hypot(x, y)
```

Pinned perpendicular case:

```text
FM1
30% slope
100 ft/min wind
wind push 90° from upslope
maximum ROS = 21.399596624626479 chains/h
```

The pinned Behave workflow passes for **maximum spread magnitude**.

Direction is computed from `atan2(y, x)` and converted through explicit geographic adapters. It is analytically tested and aligned to Behave source logic, but is not labelled as an independent Grade B direction output yet.

## 10. R4 — public model assembly — implemented

Public API:

```python
from pyfireca.behavior import RothermelModel

result = RothermelModel().compute(inputs)
```

Assembly:

```text
compute_base_spread_result
        ↓
phi_s + phi_w
        ↓
wind/slope vector composition
        ↓
effective wind
        ↓
optional wind limit
        ↓
geographic direction conversion
        ↓
FireBehaviorResult
```

Diagnostics include:

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

End-to-end tests cover base, slope-only, wind-only, perpendicular wind+slope, optional high-wind cap, dynamic-fuel rejection, and input-option validation.

## 11. Validation provenance

Evidence grades:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal analytical/synthetic fixture
```

Pinned operational revisions:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Workflows:

```text
.github/workflows/behave7-r2-probe.yml
.github/workflows/behave7-r3-vector.yml
```

The R3 vector workflow is green after fixing CSV line endings. The scalar workflow no longer modifies/builds a custom C++ wind-limit probe; it uses official `testSurface` cases only.

## 12. CI truth

The R4 functional suite has already passed on:

```text
Python 3.11  ✓
Python 3.12  ✓
Python 3.13  ✓
GIS          ✓
```

After formatting-only cleanup, use the latest all-green run as the canonical CI baseline; do not preserve an obsolete run ID in this handoff.

## 13. Exact next work

Do **not** return to R1/R2 unless a regression appears. The immediate scientific line is now:

```text
1. Verify/finalize standard fuel catalogue values
2. Implement explicit dynamic herbaceous curing/load transfer
3. Add catalogue + dynamic-fuel reference cases
4. Design first behavior-informed CA transition rule
5. Convert continuous ROS/direction to discrete neighbor travel/arrival time
6. Validate spread geometry and arrival time
```

The first CA coupling should consume `FireBehaviorResult`; `Simulation` must not branch on model names.

## 14. Deferred work

Do not pull forward yet:

```text
physical timestamp/interpolation framework
NetCDF/xarray adapter
FBP
crown fire
spotting
suppression
Monte Carlo framework
Numba optimization
Torch/JAX/GPU
learned/differentiable CA
```

Fireline intensity/flame length should also remain deferred until their equations are separately validated.

## 15. Files to read first next session

```text
1. docs/STATUS.md
2. docs/HANDOFF.md
3. docs/ROTHERMEL_REFERENCE.md
4. docs/VALIDATION.md
5. src/pyfireca/behavior/rothermel_model.py
6. src/pyfireca/behavior/_rothermel_base.py
7. src/pyfireca/behavior/_rothermel_effects.py
8. src/pyfireca/behavior/_rothermel_vectors.py
9. src/pyfireca/behavior/_directions.py
10. src/pyfireca/behavior/rothermel.py
```

The handoff describes repository truth, not planned work that was never implemented.
