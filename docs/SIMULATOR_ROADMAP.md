# Simple Simulator Completion Roadmap

> Priority: **complete the baseline simulator before implementing PyFireCA-specific CA innovations**.

## Goal

Deliver a small but complete, modern, reproducible wildfire simulator built on the already validated PyFireCA foundations.

The target is not yet a full operational wildfire system. The first complete simulator should be deterministic, understandable, GIS-ready, and scientifically traceable.

## Completion definition

The baseline simulator is considered complete when a user can run this workflow without writing internal framework code:

```text
configuration + raster inputs + ignition
        ↓
input validation
        ↓
standard fuel lookup
        ↓
Rothermel fire behavior
        ↓
Behave/Catchpole directional spread
        ↓
physical arrival propagation
        ↓
arrival/state/fire-footprint outputs
        ↓
run metadata + reproducible result directory
```

## Phase S1 — stabilize current static core

- finish any remaining Ruff/CI formatting debt;
- preserve the current synchronous CA reference and static physical-arrival solver;
- preserve strict north-up square-cell semantics for the first complete release;
- do not add new custom neighborhood or edge-coupling methods to the default simulator.

## Phase S2 — fuel catalogue for normal use

Current audited subset:

```text
FM1
FM2
GR1
```

Next target:

- audit Anderson 13 standard models;
- then audit Scott–Burgan 40 models if practical within the simple-simulator scope;
- preserve pinned source provenance for every record;
- add catalogue regression tests.

The simulator must never silently use unaudited guessed fuel parameters.

## Phase S3 — complete static landscape input

Required raster layers:

```text
fuel model
1-h dead moisture
10-h dead moisture
100-h dead moisture
live herbaceous moisture
live woody moisture
midflame wind speed
wind-from direction
slope
aspect
```

Requirements:

- GeoTIFF read support;
- strict alignment checks;
- domain mask / NoData semantics;
- explicit units;
- clear error messages;
- one documented preprocessing contract.

Keep the first complete simulator limited to north-up square metric grids rather than prematurely generalizing affine geometry.

## Phase S4 — ignition and simulation entry point

Add a user-facing simulation request/configuration object or equivalent small API that accepts:

```text
landscape
ignition location/mask/time
neighborhood
wind-limit option
output settings
```

The default physical simulator should use the validated baseline, not experimental CA variants.

Support at least:

- one ignition cell;
- multiple simultaneous ignition cells;
- optional specified ignition times.

## Phase S5 — outputs

Produce a stable result object and GIS outputs:

```text
arrival_time.tif
state.tif
burned_mask.tif
perimeter.gpkg or GeoJSON
metadata.json
resolved_config.yml/json
metrics.json (basic run statistics)
```

Minimum summary metrics:

```text
burned area
first/last arrival time
number of burned cells
runtime
```

The perimeter/vector output may be derived from the raster footprint; no advanced fire-front solver is required.

## Phase S6 — configuration and CLI

Provide one straightforward command, for example:

```text
pyfireca run config.yml
pyfireca validate config.yml
```

Configuration should expose only meaningful baseline options.

Do not expose experimental research switches in the default CLI.

## Phase S7 — reproducible run directory

Each run should create a self-contained result directory such as:

```text
runs/<run-id>/
├── config.resolved.yml
├── metadata.json
├── environment.json
├── metrics.json
├── log.txt
└── outputs/
    ├── arrival_time.tif
    ├── state.tif
    ├── burned_mask.tif
    └── perimeter.gpkg
```

Metadata should include at least:

```text
PyFireCA version
git commit when available
Python version
input paths/hashes where practical
fuel catalogue provenance
configuration
runtime
```

## Phase S8 — examples and documentation

Provide at least three end-to-end examples:

1. homogeneous synthetic fire;
2. heterogeneous two/three-fuel raster landscape;
3. file-based GeoTIFF landscape run.

Documentation should include:

```text
Getting Started
Input Data Contract
Configuration
Running a Simulation
Outputs
Scientific Assumptions
Validation
Limitations
```

README remains the landing page; detailed simulator usage belongs in docs.

## Phase S9 — validation before baseline freeze

Before calling the simple simulator complete:

- all existing Rothermel/Behave Grade B tests remain green;
- end-to-end synthetic arrival results are deterministic;
- file-based GIS example is covered by a smoke/integration test;
- output rasters preserve geometry and dtype conventions;
- CLI/config validation is tested;
- Python 3.11/3.12/3.13 + GIS CI are green;
- one tagged baseline release can be reproduced from documentation.

## Explicitly deferred until after baseline completion

These are not required for the first simple simulator:

```text
new PyFireCA-specific neighborhood method
adaptive/directional CA innovation
new interface-coupling research method
WRF coupling
time-varying weather scheduler
NetCDF/xarray pipeline
crown fire
spotting
suppression
Monte Carlo
fireline-intensity/flame-length public output
FBP
Numba optimization
GPU / Torch / JAX
```

Some of these may later become ordinary simulator features, but they must not delay the first clean static baseline.

## Development rule

Until this roadmap is complete:

> Prefer completing missing user-facing simulator workflow over creating new scientific variants.

Any promising research idea should be written to `docs/FUTURE_RESEARCH.md` and deferred rather than implemented immediately.
