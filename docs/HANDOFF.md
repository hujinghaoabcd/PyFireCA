# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: continue development from repository truth without reconstructing prior decisions from chat history.

## 1. Identity and protected scope

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. Fire-behavior equations provide physical local spread quantities; CA/event propagation remains a separate layer.

Protected extension points:

```text
State
Neighborhood
Transition rule
Time stepping / event scheduler
Behavior model
Directional spread model
```

Do not casually reverse these decisions:

1. wildfire-specific scope;
2. NumPy is the readable scientific reference path;
3. optimize only after profiling;
4. fire behavior and CA propagation remain separate;
5. GIS I/O stays outside numerical kernels;
6. behavior outputs are standardized while model-native inputs remain typed;
7. Rothermel first, FBP later;
8. R2 is explicitly Albini-adjusted Rothermel;
9. SI public inputs, explicit midflame wind;
10. wind-from, wind-push, downslope aspect, and upslope are distinct semantics;
11. non-collinear wind/slope are vector-combined;
12. wind limit is optional and disabled by default;
13. dynamic herbaceous curing is a preprocessing redistribution before R1/R2;
14. fuel records are public only after pinned-source audit;
15. one synchronous CA step has **no hidden physical duration**;
16. physical edge propagation requires **direction-specific ROS**;
17. do not project maximum/head ROS onto off-axis neighbors without a validated directional spread model;
18. external numerical references carry evidence grades and pinned provenance.

## 2. Current source tree to know first

```text
src/pyfireca/
├── __init__.py
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
    ├── __init__.py
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

`Simulation` is the original **synchronous discrete reference path**. `TransitionRule.next_state()` reads one complete old state and returns one complete next state; `step_index` is not physical time.

`NeighborIgnitionRule` remains an architecture-only baseline, not a scientifically physical fire-spread rule.

`build_initial_state(domain_mask, ignition_mask)` maps persistent domain and ignition explicitly.

## 4. Physical-time propagation baseline

This now exists separately from `Simulation`.

### Geometry

`pyfireca.propagation`:

```text
square_grid_neighbor_distance_m
spread_travel_time_s
square_grid_neighbor_travel_time_s
```

Contract:

```text
travel_time_s = physical_distance_m / direction_specific_ROS_m_s
```

Zero directional ROS across positive distance yields `+inf`.

The square-grid helper takes explicit `cell_size_m`; it does not reinterpret the existing ambiguous `RasterGrid.cell_size` as metres.

### Static event / arrival solver

`pyfireca.arrival`:

```text
DirectionalSpreadRateProvider
ConstantDirectionalSpreadRate
StaticArrivalTimeSolver
arrival_times_to_state
```

`StaticArrivalTimeSolver` is Dijkstra-style earliest-arrival propagation for **static non-negative edge travel times**.

Inputs:

```text
domain_mask      bool (Y, X)
ignition_times_s float (Y, X)
```

Finite non-negative ignition values are external ignition times. `+inf` means no initial ignition. Finite ignition outside the domain is rejected.

The directional provider is called with:

```text
source row
source col
neighbor offset
```

and must return the already-resolved directional ROS in m/s.

The solver does not know or inspect Rothermel model names.

### Physical time → FireState

```text
arrival_times_to_state(domain, arrival, time_s=..., burn_duration_s=...)
```

Semantics:

```text
outside domain                      UNBURNABLE
before arrival                      UNBURNED
arrival <= t < arrival + duration   BURNING
t >= arrival + duration             BURNED
```

`burn_duration_s` is explicit. Arrival time alone cannot identify burning vs burned.

## 5. Behavior/data contract

CA-facing output:

```text
spread_rate_m_s            required
spread_direction_deg       optional, geographic bearing
fireline_intensity_w_m     optional
flame_length_m              optional
diagnostics                 optional
```

Current `RothermelModel`:

- maximum spread rate implemented;
- maximum-spread geographic direction implemented when directional forcing exists;
- zero wind/slope gives `spread_direction_deg=None`;
- `fireline_intensity_w_m=None`;
- `flame_length_m=None`;
- Rothermel-native intermediate quantities remain diagnostics.

Do not fill intensity/flame length until their output equations receive their own validation.

`SpatialLayer` supports `(Y, X)` / `(T, Y, X)`. `EnvironmentalData.require_complete_snapshot()` is the explicit fail-fast gate for required weather/moisture inputs.

## 6. GIS truth

Stable baseline:

```text
RasterMetadata
validate_raster_alignment
read_raster
write_raster
write_state_raster
nodata_mask
build_domain_mask
LandscapeInput
```

NoData is metadata until caller-selected static layers explicitly define a persistent domain. Dynamic weather NoData does not create permanent `UNBURNABLE` cells.

State GeoTIFF:

```text
dtype          uint8
state codes    0..3
GeoTIFF NoData None
```

## 7. Rothermel R1–R4 truth

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

### R1

Validated heterogeneous fuel-bed quantities:

```text
surface-area weights
characteristic SAV
packing ratio
bulk density
optimum packing ratio
```

### R2 — Grade B static base ROS

Pinned references:

```text
FM1
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2 static dead+live
2.3810521029916596 chains/h
0.013305319151517395 m/s
```

### R3 — wind/slope

Pinned references:

```text
FM1 30% slope
20.817222076028628 chains/h

FM1 100 ft/min direct-midflame wind
8.834274755440232 chains/h

FM1 30% slope + perpendicular 100 ft/min wind
21.399596624626479 chains/h maximum ROS
```

The perpendicular **magnitude** is Grade B. Direction is source-aligned + analytically tested, not independently Grade B.

### R4 public assembly

```text
RothermelModel.compute(RothermelInputs)
        ↓
FireBehaviorResult
```

Do not return to R1/R2 unless a regression appears.

## 8. R5 dynamic herbaceous curing — Grade B complete

Pinned operational rule:

```text
M_live_herb < 0.30       transfer = 1.0
0.30 <= M <= 1.20       transfer = 1.333 - 1.11*M
M > 1.20                 transfer = 0.0
```

Operational semantics:

- transferred dead-herb SAV inherits live-herb SAV;
- dead-herb physical properties use dead-fuel values;
- dead-herb moisture maps to dead 1-h moisture;
- live+dead herbaceous load is conserved;
- the resolved fuel is then passed through the same R1/R2 path.

Pinned GR1 case:

```text
model        101 / GR1
dead M       5/5/5 %
live herb M  60 %
live woody M 90 %
wind         0
slope        0

0.71419316836403091 chains/h
0.003990911424818205 m/s
```

`RothermelModel.compute()` matches this end to end.

Workflow:

```text
.github/workflows/behave7-r5-dynamic-probe.yml
```

Despite the filename, it is now a fixed regression, not an intentional failing probe.

## 9. Standard fuel catalogue

Public:

```text
pyfireca.behavior.fuel_catalog
```

Currently audited models only:

```text
1    FM1
2    FM2
101  GR1
```

The native source values are stored with pinned Behave provenance and converted to SI only at the `RothermelFuelModel` boundary.

Public API:

```text
StandardFuelModelRecord
available_standard_fuel_model_numbers
get_standard_fuel_model_record
get_standard_fuel_model
```

Do not claim all Anderson 13 / Scott–Burgan 40 records are already available. Unknown numbers fail explicitly until audited.

## 10. Validation provenance

Evidence grades:

```text
Grade A  primary/authoritative worked value
Grade B  pinned official operational software regression
Grade C  independent implementation comparison
Grade D  internal analytical/synthetic fixture
```

Pinned software:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Stable workflows:

```text
.github/workflows/behave7-r2-probe.yml
.github/workflows/behave7-r3-vector.yml
.github/workflows/behave7-r5-dynamic-probe.yml
```

## 11. CI truth

Functional suites covering R1–R6, dynamic GR1, catalogue, arrival propagation, physical-time state snapshots, and GIS have passed on:

```text
Python 3.11
Python 3.12
Python 3.13
GIS
```

If quality is red while those are green, inspect Ruff formatter/lint before changing scientific code. Use the latest post-format all-green run as canonical truth.

## 12. Exact next scientific work

Do **not** insert `RothermelModel.spread_rate_m_s` directly into every Moore neighbor.

The missing layer is:

```text
validated maximum ROS                         ✓
        ↓
validated ellipse / directional spread       NEXT
        ↓
backing + flanking + arbitrary-angle ROS
        ↓
DirectionalSpreadRateProvider for Rothermel
        ↓
StaticArrivalTimeSolver
        ↓
anisotropic arrival/perimeter validation
```

The next code-reading target should be pinned Behave's fire-size / elliptical directional-spread implementation, followed by independent analytical tests and at least one external directional case if the official API exposes one cleanly.

## 13. Deferred work

Do not pull forward yet:

```text
full Anderson 13 + Scott–Burgan 40 audit
physical timestamp interpolation
full time-dependent event scheduler
NetCDF/xarray weather adapter
fireline intensity output
flame length output
FBP
crown fire
spotting
suppression
Monte Carlo
Numba optimization
Torch/JAX/GPU
learned/differentiable CA
```

## 14. Files to read first next session

```text
1. docs/STATUS.md
2. docs/HANDOFF.md
3. docs/ROTHERMEL_REFERENCE.md
4. src/pyfireca/behavior/rothermel_model.py
5. src/pyfireca/behavior/_rothermel_dynamic.py
6. src/pyfireca/behavior/fuel_catalog.py
7. src/pyfireca/propagation.py
8. src/pyfireca/arrival.py
9. tests/test_rothermel_model.py
10. tests/test_arrival.py
```

The handoff describes repository truth, not planned work that was never implemented.
