# PyFireCA Development Handoff

> Updated: 2026-08-13
>
> Purpose: continue from repository truth without reconstructing scientific and engineering decisions from chat history.

## 1. Highest-priority instruction

**Do not implement a new PyFireCA-specific CA innovation yet.**

The simple static simulator is functionally complete, MIT-licensed, and has passed the built-wheel release-candidate gate. The remaining work is intentional publication, not feature completion.

Current gate:

```text
choose first baseline version/tag
→ freeze release notes
→ create tag/GitHub release
→ add real release date to CITATION.cff
→ record released commit/tag
→ then reopen CA research
```

Research ideas remain preserved in:

```text
docs/FUTURE_RESEARCH.md
```

## 2. Repository and scope

Repository:

```text
hujinghaoabcd/PyFireCA
```

Scope:

> Wildfire cellular automata / raster spread simulation.

Urban CA projects remain engineering/GIS references only. PyTorchFire/differentiable CA is not part of the current baseline.

## 3. Current release-ready baseline

User workflow:

```bash
pyfireca validate run.yml
pyfireca run run.yml
```

Complete path:

```text
version-1 YAML
→ 10 aligned GeoTIFFs
→ strict validation
→ ignition events
→ Albini-adjusted Rothermel
→ Behave/Catchpole directional surface spread
→ static physical earliest arrival
→ GeoTIFF / WGS84 GeoJSON outputs
→ reproducible run directory
```

The first release line is intentionally:

```text
static weather
north-up square metric rasters
immediate Moore-8 physical arrival
source-cell-controlled outgoing ROS
```

## 4. Read these first next session

```text
1. docs/RELEASE_CHECKLIST.md
2. docs/STATUS.md
3. docs/HANDOFF.md
4. CHANGELOG.md
5. CITATION.cff
6. docs/FUTURE_RESEARCH.md
```

Only after a real baseline release should you return to research-method design.

## 5. Scientific decisions that must not be casually reversed

1. Fire behavior and propagation are separate layers.
2. NumPy remains the readable reference implementation.
3. GIS I/O stays outside numerical behavior kernels.
4. Public physical quantities use explicit units.
5. The operational Rothermel reference line is **Albini-adjusted Rothermel**.
6. Wind entering Rothermel is explicit **midflame wind**.
7. Wind-from, downwind push, downslope aspect, and upslope are distinct semantics.
8. Wind/slope effects are vector-combined when non-collinear.
9. Wind-speed limiting is optional and disabled by default.
10. Dynamic herbaceous curing is load redistribution before the common Rothermel chain.
11. External numerical references retain evidence grade + pinned provenance.
12. Fuel records are public only after pinned-source audit.
13. Maximum/head ROS is never assigned to every raster neighbor.
14. Off-axis surface spread uses Behave/Catchpole `FromIgnitionPoint`.
15. One synchronous CA step has no hidden physical duration.
16. Physical arrival uses distance / direction-specific ROS.
17. Current physical geometry is north-up + square-cell.
18. Physical propagation uses immediate-neighbor edges to prevent hidden barrier skipping.
19. Current heterogeneous baseline is **source-cell-controlled outgoing ROS**.
20. Research-only interface/neighborhood variants remain absent from the version-1 YAML/CLI.
21. Static raster units are strict and never silently converted.
22. Dynamic weather requires a separately designed time-dependent scheduler.
23. Fireline intensity/flame length remain outside validated baseline public outputs.

## 6. Validated Rothermel truth

Pinned upstream:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Protected Grade B values include:

```text
FM1 base                         0.024733996158492002 m/s
FM2 base                         0.013305319151517395 m/s
FM1 30% slope                    20.817222076028628 chains/h
FM1 100 ft/min wind              8.834274755440232 chains/h
FM1 slope + perpendicular wind   21.399596624626479 chains/h
GR1 dynamic                      0.003990911424818205 m/s
FM1 90° off-axis                 0.02921246024622574 m/s
```

Do not change scientific formulas to address an engineering/style-only CI failure.

## 7. Fuel catalogue truth

Current audited baseline:

```text
FM1–FM13    Anderson 13
GR1 (101)   Scott–Burgan
```

Anderson records are pinned to Behave core `src/behave/fuelModels.cpp` at commit `29888c7ad364aa18cfb340f4c25a8e395f24260f`.

Remaining Scott–Burgan models do not block this first release.

## 8. Input and simulator contract

Required GeoTIFF keys:

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

All layers share shape, CRS and full affine transform. The physical baseline additionally requires north-up square cells and explicit metric `cell_size_m` matching affine pixel size.

User-facing API:

```text
IgnitionEvent
StaticWildfireSimulationRequest
StaticWildfireSimulationResult
run_static_wildfire_simulation
StaticRunConfig
validate_static_run
run_static_config
```

## 9. Run-directory contract

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

`metadata.json` records SHA-256 for all ten input rasters plus encountered fuel-model provenance.

## 10. CI/package truth

Release-candidate CI covers:

```text
quality
Python 3.11
Python 3.12
Python 3.13
GIS
package
```

The final MIT package gate has passed all of the following:

```text
wheel + sdist build
License-Expression: MIT in wheel metadata
LICENSE packaged in wheel
LICENSE packaged in sdist
clean wheel install
pyfireca --help
clean [gis] wheel install
Rasterio import
creation of 10 GeoTIFF inputs from the installed wheel environment
pyfireca validate
pyfireca run
result-file assertions
```

Therefore the user-facing install/CLI workflow is proven from the built distribution, not only editable source.

## 11. License and package metadata

Project license:

```text
MIT
Copyright (c) 2026 Jinghao Hu
```

Package declaration:

```toml
license = "MIT"
license-files = ["LICENSE"]
```

Minimum build backend:

```text
hatchling >= 1.27
```

There are currently no GitHub tags or releases. `CITATION.cff` deliberately has no `date-released` until a real release exists.

## 12. Research work already observed but frozen

Stored in:

```text
docs/FUTURE_RESEARCH.md
```

Examples include VN4 vs Moore8 lattice bias, Manhattan/octile analytical arrival error, resolution versus directional convergence, and source-cell versus interface coupling.

Do not resume these before the baseline release is published.

## 13. Exact next actions

Start with `docs/RELEASE_CHECKLIST.md`.

The package version currently is:

```text
0.1.0a0
```

A matching first alpha tag would naturally be:

```text
v0.1.0a0
```

if that version is selected.

Publication sequence:

```text
1. choose release version/tag
2. freeze release notes from CHANGELOG.md
3. create tag/GitHub release
4. add actual date-released to CITATION.cff
5. record release tag/commit in STATUS.md and HANDOFF.md
6. only then reopen the paper-innovation line
```

No new scientific feature should be implemented before those publication steps are complete.

## 14. Explicitly deferred beyond the baseline

```text
remaining Scott–Burgan catalogue
rotated/non-square affine-aware geometry
time-varying weather scheduler
WRF/NetCDF/xarray
fireline intensity/flame length public validation
FBP
crown fire
spotting
suppression
Monte Carlo
Numba optimization
GPU / Torch / JAX / differentiable CA
new PyFireCA-specific CA innovations
```
