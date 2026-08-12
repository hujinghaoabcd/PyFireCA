# PyFireCA Project Status

> Updated: 2026-08-13
>
> Current milestone: **S9 — static baseline release candidate**

## Current position

PyFireCA now has a complete first-pass static wildfire simulator, not only a scientific kernel:

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

User entry points:

```bash
pyfireca validate run.yml
pyfireca run run.yml
```

The implementation priority is no longer feature completion. The code baseline is at **release-candidate readiness**; new PyFireCA-specific CA innovations remain frozen in `docs/FUTURE_RESEARCH.md` until the baseline release gate is closed.

## Release-candidate summary

Implemented and tested:

```text
synchronous CA architecture reference
static physical arrival solver
strict GIS/data contracts
Albini-adjusted Rothermel R1–R5
Behave/Catchpole off-axis surface spread
Anderson FM1–FM13 + Scott–Burgan GR1
heterogeneous static raster behavior
single/multiple/delayed ignition
programmatic simulator API
version-1 YAML
validate/run CLI
reproducible run directory
GeoTIFF + GeoJSON outputs
input SHA-256 + fuel provenance
```

## Scientific baseline

### CA reference path

Available:

```text
FireState
RasterGrid
MooreNeighborhood
VonNeumannNeighborhood
TransitionRule
NeighborIgnitionRule
Simulation
```

The synchronous reference remains step-count based and has no hidden physical `dt`.

### Physical arrival path

Available:

```text
StaticArrivalTimeSolver
arrival_times_to_state
square-grid distance/bearing helpers
direction-specific edge travel time
```

Contract:

```text
travel_time = physical_edge_distance / direction_specific_ROS
```

The physical baseline uses immediate-neighbor edges so a larger neighborhood cannot silently skip an intermediate barrier.

### Heterogeneous edge semantics

Current default:

> **The source cell controls outgoing edge ROS.**

Source/target averaging, half-cell coupling, interface resistance, and adaptive edge rules remain explicit future research variants, not hidden baseline behavior.

## Rothermel validation truth

Selected reference line:

> **Albini-adjusted Rothermel surface fire behavior.**

Pinned Grade B values include:

```text
FM1 base
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2 base
2.3810521029916596 chains/h
0.013305319151517395 m/s

FM1, 30% slope
20.817222076028628 chains/h

FM1, 100 ft/min DirectMidflame wind
8.834274755440232 chains/h

FM1, 30% slope + perpendicular wind
21.399596624626479 chains/h

GR1 dynamic, live-herb moisture 60%, zero wind/slope
0.71419316836403091 chains/h
0.003990911424818205 m/s

FM1 FromIgnitionPoint 90° off-axis
5.2277130003983068 chains/h
0.02921246024622574 m/s
```

Fireline intensity/flame length remain outside validated baseline public outputs.

## Audited fuel catalogue

Current public baseline:

```text
Anderson FM1–FM13
Scott–Burgan GR1 (101)
```

Anderson records were audited directly against pinned USFS Fire Lab Behave core:

```text
firelab/behave
commit 29888c7ad364aa18cfb340f4c25a8e395f24260f
src/behave/fuelModels.cpp
```

Tests verify native record values, SI conversion, valid computation for FM1–FM13, and unchanged FM1/FM2/GR1 reference outputs.

The remaining Scott–Burgan catalogue does not block the first static release.

## Static input contract

Version-1 file workflow requires exactly:

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

All rasters must share shape, CRS, and full affine alignment.

Current physical geometry is deliberately fail-closed:

```text
north-up
square cells
explicit metric cell_size_m
cell_size_m matches affine pixel size
```

No moisture/slope/wind-height/angle conversion is silently inferred.

## User-facing simulator API

Stable baseline objects:

```text
IgnitionEvent
build_ignition_times
StaticWildfireSimulationRequest
StaticWildfireSimulationResult
run_static_wildfire_simulation
```

Result API includes:

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

## YAML / CLI

Runtime configuration dependency:

```text
PyYAML
```

CLI uses standard-library `argparse`.

Commands:

```bash
pyfireca validate config.yml
pyfireca run config.yml
```

Version-1 configuration is strict and does not expose research-only neighborhood/interface variants.

Example:

```text
examples/static_run.yml
```

Manual:

```text
docs/RUNNING_SIMULATOR.md
```

## Run-directory contract

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

`metadata.json` records input SHA-256, raster geometry, ignition events, encountered fuel models, and pinned fuel-catalogue provenance.

Spatial output semantics:

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

Run metrics have one canonical location: root `metrics.json`.

## CI / package truth

The repository now has five release-relevant CI paths:

```text
quality
Python 3.11
Python 3.12
Python 3.13
GIS
package
```

The package gate has already successfully verified:

```text
wheel build
sdist build
clean wheel install
pyfireca --help
clean [gis] wheel install
Rasterio import
clean installed-wheel generation of 10 GeoTIFFs
pyfireca validate on those files
pyfireca run on those files
expected result files
```

This means the documented install → CLI workflow has been exercised from the **built wheel**, not only from an editable checkout.

A runtime/distribution version-equality regression now protects `pyfireca.__version__` against `pyproject.toml` drift.

## Package metadata audit

Completed:

```text
name/version
author
keywords
Python classifiers
project URLs
console script
optional GIS extra
```

`CITATION.cff` no longer contains a premature release date because the repository currently has no tag or GitHub release.

### Remaining release blocker: license

There is currently **no root LICENSE file** and no package license declaration.

This is intentionally not auto-fixed because selecting MIT/BSD/Apache/GPL/etc. is a project/legal policy choice, not a formatting decision.

Before release:

```text
choose license
→ add LICENSE
→ declare matching pyproject license metadata
→ rerun package/CI gate
```

## Documentation state

Current authoritative documentation has been synchronized to the implemented simulator:

```text
README.md
README.zh-CN.md
docs/RUNNING_SIMULATOR.md
docs/DESIGN.md
docs/VALIDATION.md
docs/STATIC_RASTER_WORKFLOW.md
docs/ROTHERMEL_REFERENCE.md
docs/SIMULATOR_ROADMAP.md
docs/DEVELOPMENT_PRIORITY.md
docs/DEVELOPMENT.md
docs/STATUS.md
docs/HANDOFF.md
docs/SESSION_LOG.md
docs/RELEASE_CHECKLIST.md
CHANGELOG.md
```

Old authoritative claims that R2/arrival/CLI were still future work or that the catalogue only contained FM1/FM2/GR1 have been removed where they affected current guidance.

## Immediate next target

No new scientific feature should be added now.

Remaining gate:

```text
1. choose/add project license
2. confirm latest final main commit all green
3. choose first baseline version/tag
4. freeze release notes
5. create tag/GitHub release
6. add actual date-released to CITATION.cff
7. record released commit/tag in STATUS/HANDOFF
```

The code-level baseline is otherwise complete enough to freeze.

## Deferred beyond the first static baseline

```text
remaining Scott–Burgan models
affine-aware rotated/non-square geometry
time-varying weather scheduler
WRF/NetCDF/xarray
fireline intensity/flame length public validation
FBP
crown fire
spotting
suppression
Monte Carlo
profiling-led Numba
Torch/JAX/GPU/differentiable CA
new PyFireCA-specific CA neighborhood/interface methods
```

Research ideas remain in `docs/FUTURE_RESEARCH.md` and should not be resumed until the baseline release gate closes.
