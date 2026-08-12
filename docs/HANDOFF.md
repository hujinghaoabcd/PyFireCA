# PyFireCA Development Handoff

> Updated: 2026-08-13
>
> Purpose: continue from repository truth without reconstructing scientific and engineering decisions from chat history.

## 1. Highest-priority instruction

**Complete and freeze the simple baseline simulator before implementing new PyFireCA-specific CA innovations.**

This priority overrides the older R9 experimentation direction.

Research ideas already discovered are preserved in:

```text
docs/FUTURE_RESEARCH.md
```

Do not currently implement:

```text
extended/adaptive neighborhood innovation
new lattice-bias correction method
new interface-coupling method
other PyFireCA-specific paper method
```

The baseline completion plan is:

```text
docs/SIMULATOR_ROADMAP.md
```

Any new promising research idea should be recorded and deferred until the baseline is frozen.

## 2. Repository identity and scope

Repository:

```text
hujinghaoabcd/PyFireCA
```

Scope:

> Wildfire cellular-automata / raster spread simulation.

Urban CA repositories are engineering/GIS references only. Urban simulation is not product scope.

PyTorchFire/differentiable CA is not part of the current development line.

## 3. Current user-visible baseline

The project is no longer only a CA/scientific kernel. A user can now run:

```bash
pyfireca validate run.yml
pyfireca run run.yml
```

Current complete path:

```text
version-1 YAML
        ↓
10 GeoTIFF layers
        ↓
strict validation
        ↓
ignition events
        ↓
per-cell Rothermel
        ↓
Behave/Catchpole directional spread
        ↓
static physical earliest arrival
        ↓
GIS result files
        ↓
reproducible run directory
```

The first release line is intentionally **static weather + north-up square metric raster**.

## 4. Files to read first next session

Start here:

```text
1. docs/DEVELOPMENT_PRIORITY.md
2. docs/SIMULATOR_ROADMAP.md
3. docs/STATUS.md
4. docs/HANDOFF.md
5. docs/RUNNING_SIMULATOR.md
6. docs/ROTHERMEL_REFERENCE.md
7. docs/FUTURE_RESEARCH.md
```

Then implementation:

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

User examples:

```text
examples/static_run.yml
examples/static_raster_rothermel.py
```

Key tests:

```text
tests/test_simulator.py
tests/test_config.py
tests/test_outputs.py
tests/test_output_rasterio.py
tests/test_workflow_rasterio.py
tests/test_cli.py
tests/test_cli_rasterio.py
tests/test_fuel_catalog.py
```

## 5. Scientific decisions that must not be casually reversed

1. Fire behavior and propagation are separate layers.
2. NumPy is the readable reference implementation.
3. Optimize only after profiling.
4. GIS I/O stays outside the numerical behavior kernel.
5. Public physical quantities use explicit units.
6. The operational Rothermel reference line is Albini-adjusted Rothermel.
7. Wind entering Rothermel is explicit **midflame wind**.
8. `wind_from`, downwind push, downslope aspect, and upslope are separate directional semantics.
9. Wind/slope effects are vector-combined when non-collinear.
10. Wind-speed limiting is optional and disabled by default.
11. Dynamic herbaceous curing is load redistribution before the common R1/R2 path.
12. External numerical references retain provenance grades and pinned upstream commits.
13. Fuel catalogue records are public only after pinned-source audit.
14. Maximum/head ROS must never be silently assigned to every raster neighbor.
15. Off-axis surface spread uses Behave/Catchpole `FromIgnitionPoint`, not `FromPerimeter`.
16. Surface ellipse L/W uses effective wind, including limited effective wind when limiting is active.
17. One synchronous CA step has no hidden physical duration.
18. Physical arrival uses direction-specific ROS and physical edge distance.
19. Current physical raster geometry is explicitly north-up and square-cell.
20. Current heterogeneous baseline uses **source-cell-controlled outgoing edge ROS**.
21. Alternative interface coupling is research material, not a hidden baseline tweak.
22. Static raster units are strict; do not silently convert percentages/radians/wind heights.
23. Static providers must not be mutated to fake dynamic weather.
24. Dynamic weather requires a separately designed time-dependent scheduler.
25. Fireline intensity and flame length remain outside validated baseline public outputs.

## 6. Two propagation paths still coexist

### Synchronous architecture reference

```text
Simulation
NeighborIgnitionRule
```

Purpose: reference CA semantics and architecture testing.

It is not the current physically timed wildfire baseline.

### Physical baseline

```text
StaticArrivalTimeSolver
```

Contract:

```text
directional ROS
→ distance
→ edge travel time
→ earliest arrival
```

The physical solver currently restricts propagation to immediate-neighbor edges so extended neighborhoods cannot silently skip intermediate barriers.

## 7. Validated Rothermel truth

Pinned upstream:

```text
firelab/behave-app
a3cfcd5903188d73445948af16644868225bb9d5

firelab/behave
29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Grade B references currently protected by tests/workflows:

```text
FM1 base
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2 base
2.3810521029916596 chains/h
0.013305319151517395 m/s

FM1 30% slope
20.817222076028628 chains/h

FM1 100 ft/min DirectMidflame wind
8.834274755440232 chains/h

FM1 30% slope + perpendicular wind
21.399596624626479 chains/h

GR1 dynamic, live herb moisture 60%, zero wind/slope
0.71419316836403091 chains/h
0.003990911424818205 m/s

FM1 FromIgnitionPoint 90° off-axis
5.2277130003983068 chains/h
0.02921246024622574 m/s
```

Do not change scientific formulas merely to satisfy a style/CI failure. Recent history contained many Ruff-only red runs while all functional jobs were green.

## 8. Fuel catalogue truth

The public audited catalogue now contains:

```text
FM1–FM13    Anderson 13
GR1 (101)   Scott–Burgan dynamic grass
```

FM1–FM13 were audited directly from pinned Behave core:

```text
src/behave/fuelModels.cpp
commit 29888c7ad364aa18cfb340f4c25a8e395f24260f
```

Tests verify source fields, SI conversion and computation.

Do not claim the complete Scott–Burgan 40 catalogue yet.

The remaining Scott–Burgan models do **not** block the first simple simulator baseline.

## 9. Static file input contract

Configuration version:

```text
1
```

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

All layers must be:

```text
same shape
same CRS
same full affine transform
static
```

Geometry baseline:

```text
north-up
square cells
positive x step
negative y step
explicit cell_size_m
cell_size_m matches affine pixel size
```

NoData rule:

- fuel-model NoData defines the permanent domain exterior;
- required behavior NoData outside the domain is allowed;
- missing/nonfinite required values inside the domain fail validation.

## 10. Ignition API

User-facing:

```text
IgnitionEvent(row, col, time_s=0)
build_ignition_times(shape, events)
```

Behavior:

```text
single ignition                     supported
multiple simultaneous ignitions     supported
delayed ignition                     supported
duplicate cell events               earliest time wins
outside-domain ignition              rejected
```

## 11. User simulation API

```text
StaticWildfireSimulationRequest
StaticWildfireSimulationResult
run_static_wildfire_simulation
```

The request contains:

```text
LandscapeInput
cell_size_m
ignition_times_s
optional neighborhood
optional use_wind_speed_limit
```

Default neighborhood is immediate Moore-8.

The result exposes:

```text
arrival_times_s
domain_mask
burned_mask
burned_cell_count
burned_area_m2
first_arrival_s
last_arrival_s
unreachable_domain_cell_count
state_at(time_s, burn_duration_s)
burned_mask_at(time_s)
summary_metrics()
```

## 12. YAML configuration

Implemented in:

```text
src/pyfireca/config.py
```

Public:

```text
StaticRasterInputPaths
StaticRunConfig
load_static_run_config
```

Rules:

- relative paths resolve relative to the YAML file;
- unknown root keys fail;
- missing input keys fail;
- ignition list must be non-empty;
- output directory is explicit;
- no research-only edge/neighborhood variants appear in the baseline config.

Example:

```text
examples/static_run.yml
```

## 13. CLI

Packaging entry point:

```toml
[project.scripts]
pyfireca = "pyfireca.cli:main"
```

Commands:

```bash
pyfireca validate run.yml
pyfireca run run.yml
```

CLI uses standard-library `argparse`. Do not introduce Typer/Click without a real requirement.

CLI is deliberately thin and calls `config.py` + `workflow.py` rather than containing scientific logic.

## 14. Reproducible file workflow

Implemented in:

```text
src/pyfireca/workflow.py
```

Public:

```text
StaticRunArtifacts
validate_static_run
run_static_config
```

`validate_static_run` reads and validates the actual GeoTIFFs but does not create a result directory.

`run_static_config` validates first, then requires the configured output directory to be absent or empty before writing results.

The landscape is loaded once per build/request path; run metadata reuses that loaded landscape rather than re-reading ten rasters.

## 15. Run-directory contract

Current structure:

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

Root roles:

```text
config.resolved.yml  fully resolved paths/options
metadata.json         scientific/input provenance
environment.json      runtime environment
metrics.json          single canonical run metrics file
log.txt               concise run-completion summary
```

`metadata.json` records SHA-256 for all ten input rasters and the pinned source commit for every encountered fuel model.

Spatial outputs:

```text
arrival_time.tif
  float64 seconds
  -1 file NoData where no finite arrival exists

state.tif
  terminal FireState
  0 UNBURNABLE
  1 in-domain but unreachable UNBURNED
  3 eventually BURNED

burned_mask.tif
  uint8 0/1 eventual footprint

perimeter.geojson
  burned raster footprint polygonized in source CRS
  then transformed to EPSG:4326 before serialization
```

Do not reintroduce duplicate `outputs/metrics.json`; run metrics have one canonical location at the run root.

## 16. Tests and CI

Main matrix:

```text
Python 3.11
Python 3.12
Python 3.13
```

Separate GIS job installs:

```text
.[dev,gis]
```

GIS job now covers:

```text
raster metadata/alignment
Rasterio read/write
simulation spatial outputs
full file-based run workflow
real YAML CLI validate/run workflow
```

Important integration tests:

```text
tests/test_workflow_rasterio.py
tests/test_cli_rasterio.py
```

These tests create real temporary GeoTIFFs, run the simulator, and verify output files/provenance.

## 17. Research work already observed but frozen

Research findings from the prior CA-discretization work are preserved in:

```text
docs/FUTURE_RESEARCH.md
```

Examples:

```text
VN4 vs Moore8 lattice bias
Manhattan/octile analytical error relation
resolution != directional convergence
source-cell vs half-cell interface coupling
```

Do not continue 16/24-direction or adaptive-neighborhood implementation now.

## 18. What remains before the baseline can be frozen

The major simulator workflow exists. Remaining work should be release polish:

```text
1. keep final code/docs CI green
2. synchronize DEVELOPMENT / SESSION_LOG / CHANGELOG
3. verify README and RUNNING_SIMULATOR instructions against a clean install
4. review packaging metadata and wheel build
5. add a release/readiness checklist
6. perform one final repository audit
7. freeze/tag the first static simulator baseline when ready
```

Do not let optional science expansion delay this list.

## 19. Explicitly deferred beyond the baseline

```text
full Scott–Burgan 40 catalogue
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
