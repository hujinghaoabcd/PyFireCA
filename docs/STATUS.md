# PyFireCA Project Status

> Updated: 2026-08-13
>
> Current milestone: **S8/S9 — static baseline simulator release polish**

## Current position

PyFireCA now has a complete first-pass static simulator path rather than only a scientific kernel:

```text
YAML configuration
        ↓
10 aligned GeoTIFF input rasters
        ↓
strict GIS / unit / NoData / fuel validation
        ↓
explicit ignition events
        ↓
Albini-adjusted Rothermel
        ↓
Behave/Catchpole directional surface ROS
        ↓
static physical earliest-arrival propagation
        ↓
arrival / terminal state / burned footprint
        ↓
GeoTIFF + WGS84 GeoJSON outputs
        ↓
resolved config + hashes + metadata + metrics + log
```

The user can now drive the same baseline from either the Python API or:

```bash
pyfireca validate run.yml
pyfireca run run.yml
```

The current priority is **release-quality baseline completion**. New PyFireCA-specific CA innovations remain recorded in `docs/FUTURE_RESEARCH.md` and are not being implemented until the simple simulator baseline is frozen.

## Baseline capabilities now implemented

### 1. CA reference core

Available and tested:

```text
FireState
RasterGrid
MooreNeighborhood
VonNeumannNeighborhood
TransitionRule
NeighborIgnitionRule
Simulation
```

The original synchronous reference path remains step-count based. It has no hidden physical `dt`.

### 2. Physical static arrival baseline

Available:

```text
StaticArrivalTimeSolver
arrival_times_to_state
square-grid distance/bearing helpers
direction-specific edge travel time
```

Physical propagation contract:

```text
travel_time = physical_edge_distance / direction_specific_ROS
```

Long-range neighborhoods are not silently accepted by the physical arrival baseline because they could skip intermediate barriers.

### 3. Fire-behavior/data/GIS contracts

Implemented:

```text
FireBehaviorModel
FireBehaviorResult
SpatialLayer
EnvironmentalData
LandscapeInput
RasterMetadata
validate_raster_alignment
read_raster / write_raster
write_state_raster
NoData/domain validation
```

Static domain semantics are explicit. Missing dynamic/static behavior data never silently become a different permanent fire state.

## Rothermel reference status

### R1 — heterogeneous fuel-bed quantities — complete

Validated SI/native-unit handling and fuel-bed derived quantities include:

```text
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

Pinned Behave references:

```text
FM1
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2
2.3810521029916596 chains/h
0.013305319151517395 m/s
```

### R3 — wind/slope/maximum spread — Grade B

Pinned references include:

```text
FM1, 30% slope, zero wind
20.817222076028628 chains/h

FM1, zero slope, 100 ft/min DirectMidflame wind
8.834274755440232 chains/h

FM1, 30% slope + perpendicular 100 ft/min wind
21.399596624626479 chains/h maximum ROS
```

Implemented:

```text
slope factor
wind factor
effective-wind inversion
optional wind-speed limit
non-collinear wind/slope vector composition
wind-from/downwind direction semantics
aspect/upslope direction semantics
```

### R4 — public Rothermel model — complete

```text
RothermelModel.compute(RothermelInputs)
→ FireBehaviorResult
```

Stable validated public behavior outputs currently emphasize:

```text
spread_rate_m_s
spread_direction_deg
```

Fireline intensity/flame length are not yet presented as validated public simulator outputs.

### R5 — dynamic herbaceous curing — Grade B

Pinned GR1 case:

```text
GR1 / model 101
live herb moisture = 60%
zero wind / zero slope
0.71419316836403091 chains/h
0.003990911424818205 m/s
```

The dynamic herbaceous load-transfer path is integrated into the same Rothermel base equations rather than implemented as a separate model.

## Standard fuel catalogue

The audited public baseline now includes:

```text
Anderson FM1–FM13
Scott–Burgan GR1 (101)
```

Anderson 13 values were audited directly against the pinned USFS Fire Lab Behave core file:

```text
src/behave/fuelModels.cpp
commit 29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Tests verify:

- FM1–FM13 native source fields;
- all Anderson models convert into the SI `RothermelFuelModel` contract;
- all 13 can compute positive zero-wind/zero-slope spread under a valid test moisture set;
- existing FM1/FM2/GR1 Grade B regressions remain unchanged;
- unaudited codes fail explicitly.

The full Scott–Burgan 40 catalogue is **not required to block the first simple simulator release** and remains future catalogue work.

## Directional surface spread — Grade B

PyFireCA uses the pinned Behave/Catchpole ignition-point surface ellipse path:

```text
L/W = 0.936 exp(0.1147 U) + 0.461 exp(-0.0692 U) - 0.397
e = sqrt((L/W)^2 - 1) / (L/W)
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

Pinned FM1 90° off-axis case:

```text
5.2277130003983068 chains/h
0.02921246024622574 m/s
```

The physical raster baseline never assigns head ROS to every neighbor.

## Static heterogeneous raster simulator

### Input layers

The version-1 static file workflow requires exactly:

```text
fuel_model                   integer code
dead_1h_moisture             fraction
dead_10h_moisture            fraction
dead_100h_moisture           fraction
live_herbaceous_moisture     fraction
live_woody_moisture          fraction
midflame_wind_speed          m/s
wind_from_direction          degrees
slope                        degrees
aspect                       degrees
```

All files must share shape, CRS and full affine alignment.

The baseline remains deliberately fail-closed:

```text
north-up only
square cells only
explicit metric cell_size_m
cell_size_m must match affine pixel size
```

No percent/radian/wind-height conversions are hidden inside the adapter.

### Per-cell behavior

```text
StaticRasterRothermelInputsProvider
→ StaticSpatialRothermelDirectionalSpreadRate
→ StaticArrivalTimeSolver
```

Current baseline edge semantic:

> **The source cell controls the outgoing edge ROS.**

Alternative interface coupling remains a research comparison and is not a default CLI option.

## User-facing simulator API

New stable baseline objects:

```text
IgnitionEvent
build_ignition_times
StaticWildfireSimulationRequest
StaticWildfireSimulationResult
run_static_wildfire_simulation
```

Supported ignition use cases:

```text
single ignition
multiple simultaneous ignitions
delayed ignition events
duplicate events → earliest event wins
```

`StaticWildfireSimulationResult` provides:

```text
arrival_times_s
burned_mask
burned_cell_count
burned_area_m2
first_arrival_s
last_arrival_s
unreachable_domain_cell_count
state_at(...)
burned_mask_at(...)
summary_metrics()
```

## YAML configuration and CLI

Runtime dependency:

```text
PyYAML
```

CLI intentionally uses the Python standard library `argparse`; no extra CLI framework was introduced.

Public commands:

```bash
pyfireca validate config.yml
pyfireca run config.yml
```

Configuration version 1 is strict:

- unknown top-level keys fail;
- all ten raster inputs are required;
- relative paths resolve relative to the YAML file;
- ignition list must be non-empty;
- output directory is explicit;
- the baseline CLI does not expose research-only CA variants.

Example:

```text
examples/static_run.yml
```

Detailed guide:

```text
docs/RUNNING_SIMULATOR.md
```

## Reproducible run directory

A completed file-based run now produces:

```text
runs/<run>/
├── config.resolved.yml
├── metadata.json
├── environment.json
├── metrics.json
├── log.txt
└── outputs/
    ├── arrival_time.tif
    ├── state.tif
    ├── burned_mask.tif
    └── perimeter.geojson
```

### Provenance

`metadata.json` records:

```text
raster geometry
ignition events
fuel models encountered
pinned catalogue source commit
SHA-256 of every input raster
```

`environment.json` records:

```text
PyFireCA version
Python version
platform
GitHub commit when supplied by the execution environment
```

### Spatial output semantics

```text
arrival_time.tif
  float64 seconds
  -1 file NoData for no finite arrival

state.tif
  terminal canonical state
  0 UNBURNABLE
  1 in-domain UNBURNED/unreachable
  3 BURNED/reachable

burned_mask.tif
  uint8 0/1 eventual footprint

perimeter.geojson
  polygonized burned footprint
  source CRS → WGS84 before serialization
```

Run statistics exist only once at the run root as `metrics.json`; they are not duplicated inside `outputs/`.

## Integration/CI truth

The repository now tests three levels:

1. base unit/regression tests under Python 3.11/3.12/3.13;
2. GIS read/write and output round trips with Rasterio;
3. real file workflow and CLI integration using temporary GeoTIFF input sets.

Recent functional runs confirm:

```text
Python 3.11  pass
Python 3.12  pass
Python 3.13  pass
GIS workflow pass
real YAML → GeoTIFF → simulator → outputs pass
```

Ruff lint/format remains a mandatory quality gate. A Ruff-only failure must not be misinterpreted as a scientific regression.

## Fixed development priority

The current priority is **not** to implement the previously identified lattice/interface innovations.

Until the simple simulator baseline is frozen:

```text
complete user-facing workflow
→ documentation
→ release integration checks
→ baseline tag/release preparation
→ only then resume new CA research methods
```

Research ideas are stored in:

```text
docs/FUTURE_RESEARCH.md
```

and must remain separate from default simulator behavior.

## Immediate next target

The major simulator workflow is now present. Remaining baseline tasks are release polish rather than new fire science:

```text
1. keep final CI all green
2. synchronize handoff/development/changelog docs
3. add/refresh end-to-end examples and usage documentation
4. review packaging and clean-install behavior
5. perform one release-readiness audit
6. freeze/tag the first simple static baseline when ready
```

Optional catalogue expansion, dynamic weather, WRF, FBP, crown fire, spotting,
suppression, Monte Carlo, GPU work, and PyFireCA-specific CA innovations do not
block this baseline milestone.

## Validation provenance

Evidence grades:

```text
Grade A  primary/authoritative worked value
Grade B  pinned official operational software regression
Grade C  independent implementation comparison
Grade D  internal analytical/synthetic fixture
```

Pinned upstream revisions:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

External workflows remain under `.github/workflows/behave7-*`.

## Deferred beyond the first static baseline

- remaining Scott–Burgan catalogue models;
- affine-aware rotated/non-square raster geometry;
- time-varying weather scheduler;
- WRF/NetCDF/xarray integration;
- fireline-intensity/flame-length public validation;
- FBP;
- crown fire;
- spotting;
- suppression;
- Monte Carlo;
- profiling-led Numba;
- Torch/JAX/GPU/differentiable CA;
- new PyFireCA-specific CA neighborhood/interface methods.
