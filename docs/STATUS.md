# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **R4 — validated static-fuel Rothermel behavior assembly**

## Current position

PyFireCA now has five working foundations:

```text
1. Wildfire CA reference core
2. Fire-behavior/data contracts
3. GIS landscape input/output baseline
4. Validated Albini-adjusted Rothermel R1–R3 spread path
5. Public RothermelModel.compute() → FireBehaviorResult assembly
```

The scientific path is now:

```text
RothermelFuelModel + RothermelFuelMoisture
                ↓
R1 heterogeneous fuel-bed quantities              ✓
                ↓
R2 no-wind/no-slope base ROS                       ✓ Grade B
                ↓
R3a slope factor                                   ✓ Grade B
R3b wind factor                                    ✓ Grade B
R3c effective wind / optional wind-limit handling  ✓ implemented
R3d non-collinear wind+slope magnitude             ✓ Grade B
                ↓
explicit geographic direction conversion           ✓ analytic/source-aligned
                ↓
RothermelModel.compute()                            ✓
                ↓
FireBehaviorResult
```

The next scientific gap is no longer base Rothermel ROS. It is **dynamic herbaceous fuel transfer and then the first behavior-informed CA propagation rule**.

## Completed

### CA core

- `FireState`: `UNBURNABLE / UNBURNED / BURNING / BURNED`;
- state-array validation;
- `RasterGrid`;
- Moore and Von Neumann neighborhoods;
- synchronous `TransitionRule` and `Simulation`;
- explicit NumPy RNG;
- deterministic `NeighborIgnitionRule` architectural baseline;
- no-cascade synchronous-update regression test;
- `build_initial_state(domain_mask, ignition_mask)` with rejection of ignition outside the domain.

### Common behavior/data boundary

- generic `FireBehaviorModel[InputT]`;
- immutable `FireBehaviorResult`;
- model-independent spread-rate/direction output contract;
- `SpatialLayer` for `(Y, X)` / `(T, Y, X)` arrays;
- `EnvironmentalData` with shared spatial/time-size validation;
- policy-free `snapshot()`;
- `MissingEnvironmentalDataError`;
- `require_complete_snapshot()` for explicit fail-fast validation.

Dynamic missing data are never silently interpolated and never silently converted into permanent `UNBURNABLE` state.

### GIS / landscape foundation

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

Simulation never silently reprojects or resamples. NoData affects the persistent domain only when caller-selected static layers explicitly define that domain.

Canonical state GeoTIFF output is:

```text
dtype          uint8
state codes    0..3
GeoTIFF NoData None
```

### Rothermel R1 — complete

Implemented and tested:

```text
SI ↔ ft/lb/Btu/min conversions
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
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

### Rothermel R2 — complete for static fuels

The reference line is explicitly **Albini-adjusted Rothermel**.

Implemented formula chain includes:

```text
combustible/net loading
SAV size-bin weighted combustible loading
mineral damping
moisture damping
live moisture of extinction
Albini reaction-velocity exponent
maximum and actual reaction velocity
dead/live reaction intensity
propagating flux
heat of preignition / effective heating
heat sink
no-wind/no-slope ROS
```

`compute_base_spread_result()` now exposes the validated base quantities required downstream without recomputing the R2 chain. The compatibility wrapper `compute_base_spread_rate_m_s()` remains available.

Pinned Grade B Behave 7 references:

```text
FM1 dead-only
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2 static dead + live
2.3810521029916596 chains/h
0.013305319151517395 m/s
```

### Rothermel R3 — wind and slope

Validated/implemented:

- slope factor `phi_s`;
- scalar wind factor `phi_w`;
- effective-wind inversion;
- explicit optional wind-speed limit;
- non-collinear wind/slope vector composition;
- meteorological wind-from → downwind-push conversion;
- downslope aspect → upslope conversion;
- relative-to-upslope → geographic bearing conversion.

Pinned Behave 7 scalar references include:

```text
FM1, 30% slope, zero wind
20.817222076028628 chains/h

FM1, zero slope, 100 ft/min direct-midflame wind
8.834274755440232 chains/h
```

Pinned non-collinear reference:

```text
FM1
30% slope
100 ft/min direct-midflame wind
wind push perpendicular to upslope

maximum ROS = 21.399596624626479 chains/h
```

The pinned Behave workflow passes for this magnitude. Direction geometry is tested analytically and aligned to the Behave vector formulation; it is not labelled as an independent Grade B direction output yet.

Wind-limit reference quantities for FM1:

```text
reaction intensity     159495.8270605292 W/m²
wind-speed limit       758.3986638051593 ft/min
                       3.85266521213021 m/s
limited high-wind ROS  1.6614603649165824 m/s
```

The official Behave workflow validates ROS at the computed wind-limit boundary. PyFireCA separately unit-tests the optional enable/exceeded/capping logic.

### Rothermel R4 — public model assembly

`RothermelModel` is exported from `pyfireca.behavior`.

```text
RothermelModel.compute(RothermelInputs)
        ↓
FireBehaviorResult
```

Current stable outputs:

```text
spread_rate_m_s
spread_direction_deg
```

Zero-wind/zero-slope direction is returned as `None` rather than inventing a head-fire direction for an isotropic case.

Validated/internal Rothermel quantities are exposed through `diagnostics`, including base ROS, reaction intensity, SAV, packing ratios, wind/slope factors, effective wind, and wind-limit state.

`fireline_intensity_w_m` and `flame_length_m` intentionally remain `None` until their own output equations are validated.

## Validation evidence

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
```

The R3 vector workflow now passes with the official `testSurface` executable. The R2/R3 scalar workflow was simplified to remove a fragile custom C++ wind-limit probe and uses official `testSurface` reference cases only.

## CI state

The R4 end-to-end model tests pass on:

```text
Python 3.11  ✓
Python 3.12  ✓
Python 3.13  ✓
GIS job      ✓
```

The final post-format quality run should be treated as the authoritative green baseline once the latest commit completes; do not cite an older run number as current truth.

## Key decisions now fixed

1. CA propagation and fire behavior remain separate.
2. Behavior outputs are standardized; model-native inputs remain model-specific.
3. NumPy remains the readable scientific reference path.
4. GIS file I/O remains outside CA numerical kernels.
5. Misaligned rasters fail explicitly.
6. Static NoData affects the persistent domain only through explicit layer selection.
7. Dynamic missing weather never silently changes permanent CA state.
8. Rothermel public input uses SI quantities and explicit midflame wind.
9. R2 follows the named Albini-adjusted Rothermel line.
10. Wind limit is an explicit model option and defaults to disabled.
11. Meteorological wind-from direction is never confused with downwind fire push.
12. Non-collinear wind and slope are vector-combined, not blindly added as scalar factors.
13. Zero-directional-effect cases return no artificial spread direction.
14. External validation values carry evidence grades and pinned provenance.
15. Fireline intensity/flame length are not exposed as validated outputs prematurely.

## Not implemented yet

### Immediate scientific work

- dynamic Scott–Burgan-style herbaceous curing/load transfer;
- validated standard Anderson / Scott–Burgan fuel catalogue values;
- first behavior-informed CA transition rule using physical ROS;
- explicit mapping from continuous ROS/direction to discrete CA neighbor travel/arrival time.

### Output science still deferred

- validated fireline intensity output;
- validated flame length output;
- directional off-axis ellipse spread beyond maximum-spread direction;
- residence time / heat-per-unit-area outputs.

### GIS/data work deliberately deferred

- physical timestamps and temporal interpolation;
- high-level multi-file landscape loader;
- explicit reprojection/resampling preprocessing helper;
- arrival-time raster convention;
- NetCDF/xarray adapter until a concrete weather integration requires it.

### Later research

- FBP;
- crown fire;
- spotting;
- suppression;
- Monte Carlo;
- active/sparse updates;
- event-driven scheduling;
- profiling-led Numba optimization;
- Torch/JAX/GPU/differentiable CA.

## Immediate next target

```text
validated static Rothermel behavior              ✓
        ↓
standard fuel catalogue + dynamic curing
        ↓
behavior-informed CA propagation rule
        ↓
continuous ROS → discrete neighbor travel time
        ↓
arrival-time / spread-shape validation
```

Do not jump to GPU or learned CA before the first physical behavior-informed CA path is validated end to end.
