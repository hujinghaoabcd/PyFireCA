# PyFireCA Development Handoff

> Updated: 2026-08-13
>
> Purpose: continue from repository truth without reconstructing scientific and engineering decisions from chat history.

## 1. Highest-priority instruction

**Do not implement a new PyFireCA-specific CA innovation yet.**

The simple static simulator is now functionally complete and has passed built-wheel end-to-end validation. The remaining task is release freeze, not new science.

Current gate:

```text
license decision
→ final all-green main commit
→ choose baseline tag/version
→ release/tag
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

Urban CA projects remain engineering/GIS references only.

PyTorchFire/differentiable CA is not part of the current baseline.

## 3. Current release-candidate baseline

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
4. docs/DEVELOPMENT_PRIORITY.md
5. docs/SIMULATOR_ROADMAP.md
6. docs/RUNNING_SIMULATOR.md
7. docs/FUTURE_RESEARCH.md
```

Only after the release gate closes should you return to research-method design.

## 5. Current core files

```text
src/pyfireca/
├── config.py
├── cli.py
├── workflow.py
├── simulator.py
├── outputs.py
├── ignition.py
├── data.py
├── gis.py
├── arrival.py
├── propagation.py
├── state.py
├── grid.py
├── neighborhood.py
├── rules.py
├── simulation.py
└── behavior/
    ├── fuel_catalog.py
    ├── rothermel.py
    ├── rothermel_model.py
    ├── rothermel_layers.py
    ├── rothermel_landscape.py
    ├── rothermel_spatial.py
    ├── rothermel_directional.py
    ├── _surface_ellipse.py
    ├── _rothermel_base.py
    ├── _rothermel_dynamic.py
    ├── _rothermel_effects.py
    ├── _rothermel_vectors.py
    ├── _rothermel_equations.py
    ├── _directions.py
    └── _units.py
```

Key tests:

```text
tests/test_fuel_catalog.py
tests/test_simulator.py
tests/test_config.py
tests/test_outputs.py
tests/test_output_rasterio.py
tests/test_workflow_rasterio.py
tests/test_cli.py
tests/test_cli_rasterio.py
tests/test_package_metadata.py
```

## 6. Scientific decisions that must not be casually reversed

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
14. Off-axis surface spread uses Behave/Catchpole `FromIgnitionPoint`, not `FromPerimeter` or cosine projection.
15. One synchronous CA step has no hidden physical duration.
16. Physical arrival uses distance / direction-specific ROS.
17. Current physical geometry is north-up + square-cell.
18. The physical baseline uses immediate-neighbor edges so long-range hops cannot skip barriers.
19. Current heterogeneous baseline is **source-cell-controlled outgoing ROS**.
20. Interface averaging/half-cell/interface resistance are future named hypotheses.
21. Static raster units are strict and never silently converted.
22. Static providers must not be mutated to fake dynamic weather.
23. Dynamic weather requires a separately designed time-dependent scheduler.
24. Fireline intensity/flame length remain outside validated baseline public outputs.
25. Research-only variants remain absent from version-1 YAML/CLI.

## 7. Validated Rothermel truth

Pinned upstream:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Protected Grade B values include:

```text
FM1 base
0.024733996158492002 m/s

FM2 base
0.013305319151517395 m/s

FM1 30% slope
20.817222076028628 chains/h

FM1 100 ft/min DirectMidflame wind
8.834274755440232 chains/h

FM1 30% slope + perpendicular wind
21.399596624626479 chains/h

GR1 dynamic, live-herb moisture 60%
0.003990911424818205 m/s

FM1 FromIgnitionPoint 90° off-axis
0.02921246024622574 m/s
```

Do not change scientific formulas to address an engineering/style-only CI failure.

## 8. Fuel catalogue truth

Current audited baseline:

```text
FM1–FM13    Anderson 13
GR1 (101)   Scott–Burgan
```

Anderson records are pinned to:

```text
src/behave/fuelModels.cpp
commit 29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Remaining Scott–Burgan models do not block the first baseline release.

## 9. Static input contract

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

All layers must share:

```text
shape
CRS
full affine transform
```

Physical baseline additionally requires:

```text
north-up
square cells
explicit cell_size_m
cell_size_m matches affine pixel size
```

Fuel-model NoData defines permanent domain exterior in the version-1 file workflow. Required behavior NoData/nonfinite values inside the domain fail explicitly.

## 10. User-facing API

Ignition:

```text
IgnitionEvent
build_ignition_times
```

Simulator:

```text
StaticWildfireSimulationRequest
StaticWildfireSimulationResult
run_static_wildfire_simulation
```

Config/workflow:

```text
StaticRasterInputPaths
StaticRunConfig
load_static_run_config
StaticRunArtifacts
validate_static_run
run_static_config
```

Spatial outputs:

```text
StaticSimulationOutputPaths
write_static_simulation_outputs
write_burned_perimeter_geojson
```

## 11. Run-directory contract

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

Important semantics:

```text
arrival_time.tif
  float64 seconds
  -1 file NoData

state.tif
  terminal FireState
  0 UNBURNABLE
  1 in-domain unreachable UNBURNED
  3 BURNED

burned_mask.tif
  uint8 0/1

perimeter.geojson
  source CRS polygonization
  → EPSG:4326 before serialization
```

`metrics.json` exists only at the run root.

## 12. CI/package truth

CI currently includes:

```text
quality
Python 3.11
Python 3.12
Python 3.13
GIS
package
```

The `package` job has already passed a clean built-wheel workflow including:

```text
wheel + sdist build
clean wheel install
pyfireca --help
clean [gis] wheel install
Rasterio import
creation of 10 GeoTIFF inputs from the installed wheel environment
pyfireca validate
pyfireca run
result-file assertions
```

Therefore the user-facing install/CLI workflow is proven from the built distribution, not just editable source.

`tests/test_package_metadata.py` protects runtime/distribution version equality.

## 13. Current package metadata

Added/reviewed:

```text
name/version
author
keywords
Python classifiers
project URLs
console script
GIS extra
```

There are currently no GitHub tags or releases. `CITATION.cff` deliberately has no `date-released` until a real release exists.

## 14. Only unresolved pre-release policy item: LICENSE

Repository root currently has **no LICENSE file** and `pyproject.toml` has no license declaration.

Do not guess the license.

Before tag/release:

```text
choose project license
→ add LICENSE
→ add matching pyproject license metadata/classifier if appropriate
→ rerun full CI/package gate
```

This is the only intentional project-policy blocker left in the code/package audit.

## 15. Research work already observed but frozen

Stored in:

```text
docs/FUTURE_RESEARCH.md
```

Examples:

```text
VN4 vs Moore8 lattice bias
Manhattan/octile analytical arrival error
resolution != directional convergence
extended/adaptive neighborhood ideas
source-cell vs half-cell/interface coupling
```

Do not resume these until the baseline release gate closes.

## 16. Exact next actions

Start with `docs/RELEASE_CHECKLIST.md`.

Then:

```text
1. resolve license choice
2. add LICENSE + package metadata
3. run/confirm latest main CI all green
4. choose first baseline version/tag
5. freeze CHANGELOG release notes
6. create GitHub tag/release
7. add actual date-released to CITATION.cff
8. record release tag/commit in STATUS.md and HANDOFF.md
```

No new scientific feature should be implemented before these steps are complete.

## 17. Explicitly deferred beyond the baseline

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
