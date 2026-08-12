# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **R6 — physical-time arrival propagation baseline**

## Current position

PyFireCA now has seven working foundations:

```text
1. Wildfire CA reference core
2. Fire-behavior/data contracts
3. GIS landscape input/output baseline
4. Validated Albini-adjusted Rothermel R1–R4 path
5. Dynamic Scott–Burgan herbaceous curing/load transfer
6. Audited standard-fuel catalogue subset
7. Static directional-ROS → travel-time → arrival-time propagation baseline
```

Current scientific path:

```text
standard/dynamic fuel + moisture + wind + slope
                  ↓
          RothermelModel.compute()
                  ↓
       maximum ROS + direction
                  ↓
      directional spread model          ← next science gate
                  ↓
    direction-specific neighbor ROS
                  ↓
     distance / ROS = travel time        ✓
                  ↓
       earliest arrival time             ✓
                  ↓
 physical-time FireState snapshot        ✓
```

The major missing scientific link is now **validated off-axis directional spread**, not base Rothermel ROS, dynamic curing, or physical travel time.

## Completed

### CA core

- `FireState`: `UNBURNABLE / UNBURNED / BURNING / BURNED`;
- `RasterGrid`;
- Moore and Von Neumann neighborhoods;
- synchronous `TransitionRule` and `Simulation` reference path;
- explicit NumPy RNG;
- deterministic `NeighborIgnitionRule` architectural baseline;
- `build_initial_state(domain_mask, ignition_mask)`;
- synchronous no-cascade regression tests.

The original synchronous `Simulation` remains unchanged. Physical-time propagation is implemented as a separate baseline rather than silently assigning a `dt` to one CA step.

### Common behavior/data boundary

- generic `FireBehaviorModel[InputT]`;
- immutable `FireBehaviorResult`;
- model-independent spread-rate/direction output;
- `SpatialLayer` for `(Y, X)` and `(T, Y, X)`;
- `EnvironmentalData` alignment checks;
- policy-free `snapshot()`;
- `require_complete_snapshot()` fail-fast missing-data gate.

Dynamic missing weather is never silently interpolated or converted into persistent `UNBURNABLE` state.

### GIS / landscape baseline

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

Simulation never silently reprojects/resamples. Static NoData affects the persistent domain only through explicit caller selection.

Canonical state GeoTIFF:

```text
dtype          uint8
state codes    0..3
GeoTIFF NoData None
```

## Rothermel validation status

### R1 — heterogeneous fuel-bed quantities — complete

Implemented and tested:

```text
SI ↔ ft/lb/Btu/min conversions
surface-area weights
characteristic SAV
packing ratio
bulk density
optimum packing ratio
```

Fixed six-class order:

```text
DEAD_1H
DEAD_10H
DEAD_100H
DEAD_HERBACEOUS
LIVE_HERBACEOUS
LIVE_WOODY
```

### R2 — Albini-adjusted base ROS — Grade B

Formula path includes:

```text
combustible/net loading
SAV size-bin weighted loading
mineral damping
moisture damping
live moisture of extinction
Albini reaction-velocity exponent
reaction velocity/intensity
propagating flux
preignition heat
heat sink
no-wind/no-slope ROS
```

Pinned Behave 7 references:

```text
FM1 dead-only
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2 static dead + live
2.3810521029916596 chains/h
0.013305319151517395 m/s
```

### R3 — wind, slope, and maximum-spread vector

Pinned Grade B references:

```text
FM1, 30% slope, zero wind
20.817222076028628 chains/h

FM1, zero slope, 100 ft/min direct-midflame wind
8.834274755440232 chains/h

FM1, 30% slope + 100 ft/min perpendicular wind push
21.399596624626479 chains/h maximum ROS
```

Implemented:

- slope factor;
- scalar wind factor;
- effective-wind inversion;
- optional wind-speed limit;
- non-collinear wind/slope vector combination;
- meteorological wind-from → downwind push;
- downslope aspect → upslope;
- relative direction → geographic bearing.

Maximum-spread magnitude is externally Grade B for the perpendicular case. Direction is source-aligned and analytically tested but is not labelled as an independent Grade B direction output.

### R4 — public behavior model — complete

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

Zero wind + zero slope returns `spread_direction_deg=None` rather than inventing a head-fire direction.

Rothermel-specific diagnostics include base ROS, reaction intensity, SAV, packing ratios, wind/slope factors, effective wind, dynamic herbaceous transfer, and wind-limit state.

`fireline_intensity_w_m` and `flame_length_m` remain `None` until separately validated.

## R5 — dynamic herbaceous curing/load transfer — Grade B

Pinned operational transfer rule:

```text
live herb moisture < 0.30
    transfer fraction = 1.0

0.30 <= moisture <= 1.20
    transfer fraction = 1.333 - 1.11 * moisture

moisture > 1.20
    transfer fraction = 0.0
```

Operational life-state semantics preserved:

- transferred dead herb uses live-herb SAV;
- transferred dead herb uses dead-fuel heat/density/mineral properties;
- transferred dead herb uses dead 1-h moisture;
- herbaceous load is conserved;
- redistribution is resolved before the common R1/R2 path.

Pinned GR1 case:

```text
fuel model            GR1 / 101
dead moisture         5 / 5 / 5 %
live herb moisture    60 %
live woody moisture   90 %
wind                   0
slope                  0

Behave 7 ROS
0.71419316836403091 chains/h
0.003990911424818205 m/s
```

`RothermelModel.compute()` reproduces this Grade B result end to end.

External workflow:

```text
.github/workflows/behave7-r5-dynamic-probe.yml
```

The workflow has been promoted from a probe to a fixed regression.

## Audited standard-fuel catalogue

Public module:

```text
pyfireca.behavior.fuel_catalog
```

Current deliberately small audited subset:

```text
1    FM1
2    FM2
101  GR1
```

The catalogue stores the pinned Behave values in native source units, then explicitly converts them to PyFireCA's SI `RothermelFuelModel` contract.

Public API:

```text
StandardFuelModelRecord
available_standard_fuel_model_numbers()
get_standard_fuel_model_record(number)
get_standard_fuel_model(number)
```

FM1, FM2, and GR1 catalogue-generated models are regression-tested against their existing Grade B ROS results. Unknown models fail explicitly as “not audited yet”; the package does not pretend all Anderson/Scott–Burgan records have already been reviewed.

## R6 — physical travel-time and arrival baseline

### Physical edge geometry

Public module:

```text
pyfireca.propagation
```

Implemented:

```text
square_grid_neighbor_distance_m(offset, cell_size_m)
spread_travel_time_s(distance_m, directional_spread_rate_m_s)
square_grid_neighbor_travel_time_s(...)
```

Scientific contract:

```text
travel_time = physical_distance / direction_specific_ROS
```

A positive distance with zero ROS is unreachable (`+inf`).

This layer does **not** derive off-axis ROS from the maximum/head-fire ROS.

### Static event-driven arrival solver

Public API:

```text
DirectionalSpreadRateProvider
ConstantDirectionalSpreadRate
StaticArrivalTimeSolver
arrival_times_to_state
```

`StaticArrivalTimeSolver` uses a Dijkstra-style earliest-arrival calculation for static non-negative edge travel times.

Inputs:

```text
domain_mask
ignition_times_s
```

Finite non-negative ignition values are external ignition times; `+inf` means no initial ignition. Multiple ignition times, barriers, anisotropic directional providers, Moore/Von Neumann geometry, zero ROS, and invalid edge rates are tested.

### Physical time → CA state

`arrival_times_to_state(..., time_s, burn_duration_s)` maps:

```text
outside domain                      → UNBURNABLE
before arrival                      → UNBURNED
arrival <= t < arrival + duration   → BURNING
t >= arrival + duration             → BURNED
```

`burn_duration_s` is explicit because arrival time alone cannot distinguish `BURNING` from `BURNED`.

The original synchronous `Simulation` and the physical-time arrival solver intentionally coexist as separate reference propagation approaches.

## Validation provenance

Evidence grades:

```text
Grade A  primary/authoritative worked value
Grade B  pinned official operational software regression
Grade C  independent implementation comparison
Grade D  internal analytical/synthetic fixture
```

Pinned operational revisions:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave core
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Stable external workflows:

```text
.github/workflows/behave7-r2-probe.yml
.github/workflows/behave7-r3-vector.yml
.github/workflows/behave7-r5-dynamic-probe.yml
```

## CI state

Functional tests covering R1–R6, dynamic GR1, audited catalogue, GIS, travel-time, arrival-time, and physical-time snapshots pass across:

```text
Python 3.11  ✓
Python 3.12  ✓
Python 3.13  ✓
GIS          ✓
```

Use the latest post-format all-green run as the canonical CI baseline.

## Key decisions now fixed

1. Fire behavior and CA propagation remain separate.
2. NumPy remains the readable scientific reference path.
3. GIS I/O stays outside numerical kernels.
4. Dynamic weather missing data never silently alter persistent state.
5. Rothermel inputs use SI quantities and explicit midflame wind.
6. R2 is explicitly Albini-adjusted Rothermel.
7. Wind limit is optional and disabled by default.
8. Wind-from, wind-push, downslope aspect, and upslope are separate semantics.
9. Non-collinear wind/slope effects are vector-combined.
10. Dynamic herbaceous curing is a load-transfer preprocessing stage, not a second Rothermel implementation.
11. Standard fuel records are exposed only after audit against pinned provenance.
12. One synchronous CA step has no hidden physical duration.
13. Physical travel time requires a direction-specific ROS.
14. Maximum/head ROS is not silently projected onto off-axis neighbors.
15. Static earliest-arrival propagation remains separate from future time-dependent weather scheduling.
16. Fireline intensity/flame length are not declared validated prematurely.

## Not implemented yet

### Immediate scientific work

- validated ellipse / directional spread relation away from maximum-spread direction;
- backing and flanking ROS validation;
- a Rothermel directional-ROS provider for raster neighbor edges;
- end-to-end Rothermel → directional ROS → arrival-time spread-shape validation.

### Catalogue work

- remaining Anderson 13 records;
- remaining Scott–Burgan 40 records;
- nonburnable standard records and public grouping/metadata.

### Output science still deferred

- fireline intensity output;
- flame length output;
- residence time / heat-per-unit-area outputs.

### Dynamic data work deliberately deferred

- physical timestamp interpolation;
- time-dependent arrival/event scheduler;
- NetCDF/xarray adapter;
- high-level WRF/weather coupling.

### Later research

- FBP;
- crown fire;
- spotting;
- suppression;
- Monte Carlo;
- sparse/event optimization;
- profiling-led Numba;
- Torch/JAX/GPU/differentiable CA.

## Immediate next target

```text
validated maximum Rothermel spread               ✓
dynamic curing                                   ✓
audited reference fuel subset                    ✓
physical edge travel time                        ✓
static earliest-arrival baseline                 ✓
        ↓
validated elliptical directional spread
        ↓
Rothermel directional edge provider
        ↓
end-to-end anisotropic fire-shape validation
```

Do not jump to GPU or learned CA before this physical behavior-to-arrival path is validated end to end.
