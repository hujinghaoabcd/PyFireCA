# PyFireCA Project Status

> Updated: 2026-08-13
>
> Current milestone: **S9 — static baseline release-ready**

## Current position

PyFireCA now has a complete first-pass static wildfire simulator and has passed the full release-candidate engineering gate.

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

The code baseline is now technically ready for release. New PyFireCA-specific CA innovations remain frozen in `docs/FUTURE_RESEARCH.md` until a baseline tag/release is intentionally created.

## Release-ready baseline

Implemented and tested:

```text
synchronous CA architecture reference
static physical arrival solver
strict GIS/data contracts
Albini-adjusted Rothermel
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
MIT license + packaged license metadata
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

The physical baseline uses immediate-neighbor edges so larger-neighborhood hops cannot silently skip barriers.

### Heterogeneous edge semantics

Current default:

> **The source cell controls outgoing edge ROS.**

Source/target averaging, half-cell coupling, interface resistance, and adaptive edge rules remain future research variants rather than hidden baseline behavior.

## Rothermel validation truth

Selected reference line:

> **Albini-adjusted Rothermel surface fire behavior.**

Protected Grade B references include:

```text
FM1 base
0.024733996158492002 m/s

FM2 base
0.013305319151517395 m/s

FM1, 30% slope
20.817222076028628 chains/h

FM1, 100 ft/min DirectMidflame wind
8.834274755440232 chains/h

FM1, 30% slope + perpendicular wind
21.399596624626479 chains/h

GR1 dynamic, live-herb moisture 60%, zero wind/slope
0.003990911424818205 m/s

FM1 FromIgnitionPoint 90° off-axis
0.02921246024622574 m/s
```

Fireline intensity and flame length remain outside validated baseline public outputs.

## Audited fuel catalogue

Current public baseline:

```text
Anderson FM1–FM13
Scott–Burgan GR1 (101)
```

Anderson records are audited against pinned USFS Fire Lab Behave core:

```text
firelab/behave
commit 29888c7ad364aa18cfb340f4c25a8e395f24260f
src/behave/fuelModels.cpp
```

Remaining Scott–Burgan models do not block this first static baseline.

## Static file workflow

Version-1 input requires exactly ten aligned rasters:

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

Current geometry is deliberately fail-closed:

```text
north-up
square cells
explicit metric cell_size_m
cell_size_m matches affine pixel size
```

No moisture/slope/wind-height/angle conversion is silently inferred.

## User API and CLI

Stable baseline API:

```text
IgnitionEvent
StaticWildfireSimulationRequest
StaticWildfireSimulationResult
run_static_wildfire_simulation
StaticRunConfig
validate_static_run
run_static_config
```

CLI:

```bash
pyfireca validate config.yml
pyfireca run config.yml
```

Version-1 configuration is strict and does not expose research-only neighborhood/interface variants.

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

`metadata.json` records input SHA-256, raster geometry, ignition events, encountered fuel models, and pinned catalogue provenance.

## CI / package truth

Release-relevant CI currently covers:

```text
quality
Python 3.11
Python 3.12
Python 3.13
GIS
package
```

The final MIT release-candidate package gate has passed:

```text
wheel build
sdist build
License-Expression: MIT verification
LICENSE present in wheel
LICENSE present in sdist
clean wheel install
pyfireca --help
clean [gis] wheel install
Rasterio import
clean installed-wheel generation of ten GeoTIFFs
pyfireca validate
pyfireca run
expected result-file assertions
```

The install → CLI workflow is therefore verified from built distributions, not only from an editable checkout.

## License/package metadata

License:

```text
MIT
Copyright (c) 2026 Jinghao Hu
```

Repository/package representation:

```text
LICENSE
pyproject.toml: license = "MIT"
pyproject.toml: license-files = ["LICENSE"]
Hatchling >= 1.27
```

CI directly verifies the SPDX license expression and packaged license files.

There are currently no GitHub tags or releases. `CITATION.cff` therefore deliberately has no `date-released` field yet.

## Documentation state

Authoritative documentation is synchronized around the release-ready static baseline:

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

## Immediate next target

No new scientific feature should be added before the intentional release decision.

Remaining publication actions:

```text
1. choose first baseline version/tag
2. freeze release notes
3. create tag/GitHub release
4. add actual date-released to CITATION.cff
5. record released commit/tag in STATUS/HANDOFF
6. only then reopen the paper-innovation line
```

The current package version is `0.1.0a0`; a matching tag such as `v0.1.0a0` would preserve version consistency if selected for the first alpha release.

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

Research ideas remain in `docs/FUTURE_RESEARCH.md` and should not resume until the baseline release gate closes.
