# PyFireCA Development Session Log

## 2026-08-13 — Complete static simulator baseline and release-readiness gate

### Session objective

Turn the already validated PyFireCA scientific kernel into a complete first-pass user-facing wildfire simulator without introducing new PyFireCA-specific CA research methods.

The governing priority for this session was:

> **Finish the simple baseline simulator first; preserve new CA innovation ideas in documentation and defer implementation.**

---

## 1. Anderson 13 fuel catalogue completed

The standard fuel catalogue was expanded from:

```text
FM1
FM2
GR1
```

to:

```text
Anderson FM1–FM13
Scott–Burgan GR1 (101)
```

The Anderson records were not copied from an unverified secondary table. They were audited directly from the pinned USFS Fire Lab Behave core source:

```text
firelab/behave
commit 29888c7ad364aa18cfb340f4c25a8e395f24260f
src/behave/fuelModels.cpp
```

Tests now verify:

```text
native record fields
pinned source commit
FM1–FM13 SI conversion
positive zero-wind/zero-slope computation for all 13 models
unchanged FM1/FM2 Grade B reference ROS
unchanged GR1 dynamic Grade B reference ROS
explicit rejection of unaudited model numbers
```

The full Scott–Burgan 40 catalogue remains future work and is not a blocker for the first static simulator release.

---

## 2. User-facing ignition API added

Implemented:

```text
IgnitionEvent
build_ignition_times
```

Supported semantics:

```text
single ignition
multiple simultaneous ignitions
delayed ignition events
duplicate-cell events → earliest time wins
```

Validation rejects:

```text
negative/nonfinite time
out-of-bounds ignition
ignition outside the burnable simulation domain
empty ignition event list
```

Ignition events are converted into the same `ignition_times_s` field consumed by the existing arrival solver; no second propagation implementation was introduced.

---

## 3. Complete programmatic static simulator API added

Implemented:

```text
StaticWildfireSimulationRequest
StaticWildfireSimulationResult
run_static_wildfire_simulation
```

The simulator is a thin assembly around the already validated static landscape factory and arrival solver:

```text
LandscapeInput
→ Rothermel landscape factory
→ directional edge ROS
→ StaticArrivalTimeSolver
→ StaticWildfireSimulationResult
```

The result object exposes:

```text
arrival_times_s
domain_mask
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

Default physical neighborhood remains immediate Moore-8.

Tests cover:

```text
single ignition
multiple ignition
repeated event earliest-time behavior
arrival → state conversion
burned footprint and area
summary metrics
out-of-domain ignition rejection
```

---

## 4. Stable spatial output layer added

Implemented:

```text
write_static_simulation_outputs
write_burned_perimeter_geojson
terminal_state_from_result
StaticSimulationOutputPaths
```

Current spatial-output contract:

```text
outputs/
├── arrival_time.tif
├── state.tif
├── burned_mask.tif
└── perimeter.geojson
```

### Arrival raster

```text
dtype     float64
unit      seconds
NoData    -1
```

A negative NoData marker is safe because valid physical arrival time is non-negative.

### Terminal state raster

```text
0  UNBURNABLE / outside domain
1  UNBURNED / in-domain but unreachable
3  BURNED / eventually reached
```

The file is deliberately terminal state rather than an arbitrary burning-time snapshot.

### Burned mask

```text
uint8
0 / 1
```

### Perimeter GeoJSON

The final burned raster footprint is polygonized in the raster CRS and then transformed to:

```text
EPSG:4326
```

before GeoJSON serialization. Projected raster coordinates are therefore not mislabeled as standard GeoJSON longitude/latitude coordinates.

Rasterio integration tests write and read these outputs for real.

---

## 5. Version-1 YAML configuration added

Runtime dependency added:

```text
PyYAML
```

Implemented:

```text
StaticRasterInputPaths
StaticRunConfig
load_static_run_config
```

The version-1 config requires exactly ten static input rasters:

```text
fuel_model
dead_1h_moisture
dead_10h_moisture
dead_100h_moisture
live_herbaceous_moisture
live_woody_moisture
midflame_wind_speed
wind_from_direction
slope
aspect
```

Configuration behavior:

- relative paths resolve relative to the YAML file;
- unknown top-level keys fail;
- missing raster keys fail;
- unknown raster keys fail;
- ignition list must be non-empty;
- output directory is explicit;
- research-only neighborhood/interface switches are not exposed.

Example:

```text
examples/static_run.yml
```

---

## 6. Reproducible file workflow completed

Implemented:

```text
load_static_landscape
build_static_request_from_config
validate_static_run
run_static_config
StaticRunArtifacts
```

Complete file path:

```text
YAML
→ ten GeoTIFFs
→ strict alignment/unit/NoData/fuel validation
→ LandscapeInput
→ ignition events
→ validated static simulator
→ reproducible run directory
```

The landscape is loaded once for the request/run path; run metadata reuses the loaded landscape rather than reading the ten rasters a second time.

Input validation occurs before a new output directory is created.

Non-empty existing result directories are rejected rather than silently overwritten.

---

## 7. Reproducible run directory completed

Current run contract:

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

`metadata.json` records:

```text
raster shape / CRS / transform / cell size
ignition events
fuel models encountered
pinned catalogue source commit
SHA-256 for every input raster
```

`environment.json` records:

```text
PyFireCA package version
Python version
platform
Git commit when supplied by the execution environment
```

`metrics.json` is the **single canonical run-metrics file**. A duplicate copy under `outputs/` was removed before release freeze to avoid future inconsistency.

---

## 8. CLI added

The package now registers:

```toml
[project.scripts]
pyfireca = "pyfireca.cli:main"
```

Commands:

```bash
pyfireca validate config.yml
pyfireca run config.yml
```

The CLI uses standard-library `argparse` rather than adding Typer/Click.

It remains a thin boundary:

```text
CLI
→ load_static_run_config
→ validate_static_run / run_static_config
```

No scientific behavior or propagation equations are duplicated in CLI code.

Unit tests verify CLI dispatch/error handling.

A dedicated Rasterio integration test creates real temporary GeoTIFFs and runs both `validate` and `run` through the CLI entry function.

---

## 9. GIS end-to-end CI expanded

The dedicated GIS job now covers:

```text
GIS metadata/alignment
Rasterio input/output
simulation spatial output round trip
YAML → GeoTIFF → simulator → run directory
real CLI validate/run workflow
```

The complete file workflow has passed under the GIS job.

Multiple intermediate red runs during development were Ruff formatting failures while Python/GIS functional tests were green. Scientific code was not altered merely to satisfy formatting.

---

## 10. Packaging release gate added

A new CI `package` job now requires:

```text
wheel build
source-distribution build
clean wheel installation
pyfireca --help from clean wheel
import pyfireca from clean wheel
clean built-wheel installation with [gis] extra
import rasterio after [gis] installation
```

This is intentionally stronger than editable-source testing and should catch missing package files, entry points, or optional-dependency metadata before tagging.

---

## 11. Documentation synchronized

Updated/added:

```text
README.md
README.zh-CN.md
docs/RUNNING_SIMULATOR.md
docs/STATUS.md
docs/HANDOFF.md
docs/SIMULATOR_ROADMAP.md
docs/DEVELOPMENT.md
docs/RELEASE_CHECKLIST.md
CHANGELOG.md
```

README now describes the real static simulator rather than saying Rothermel is still future work.

`docs/RUNNING_SIMULATOR.md` documents:

```text
installation
scientific assumptions
required raster layers and units
YAML schema
ignition events
validate/run CLI
result directory
GeoTIFF/GeoJSON semantics
Python API
baseline limitations
```

Research ideas remain isolated in:

```text
docs/FUTURE_RESEARCH.md
```

---

## 12. Fixed baseline scope after this session

The first release baseline is:

```text
static weather
north-up square metric raster
strict aligned GeoTIFF inputs
Anderson FM1–FM13 + GR1
Albini-adjusted Rothermel
Behave/Catchpole directional surface spread
source-cell-controlled heterogeneous outgoing ROS
immediate Moore-8 physical arrival propagation
single/multiple/delayed ignition
GeoTIFF + WGS84 GeoJSON output
YAML + CLI + reproducible run directory
```

Explicitly not blockers:

```text
full Scott–Burgan 40 catalogue
dynamic weather / WRF
rotated/non-square geometry
FBP
crown fire
spotting
suppression
Monte Carlo
fireline intensity/flame length public output
Numba/GPU
new PyFireCA-specific CA methods
```

---

## 13. Exact next work

Do **not** resume lattice/interface/neighborhood method development yet.

Next steps are release-readiness only:

```text
1. inspect the new package CI job
2. fix packaging/metadata issues if it finds any
3. review pyproject package metadata
4. search documentation for stale pre-Rothermel/pre-CLI claims
5. verify latest main CI all green simultaneously
6. complete docs/RELEASE_CHECKLIST.md
7. decide the first baseline tag/version only after all required checks pass
```

The next developer/session should begin with:

```text
docs/RELEASE_CHECKLIST.md
docs/STATUS.md
docs/HANDOFF.md
docs/SIMULATOR_ROADMAP.md
```
