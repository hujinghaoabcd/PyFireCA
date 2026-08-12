# Running the Baseline Static Simulator

PyFireCA's first user-facing simulator is intentionally narrow: a deterministic,
static-weather, raster wildfire run using the validated Rothermel behavior path,
Behave/Catchpole directional surface spread, and physical earliest-arrival
propagation.

This document describes the baseline workflow. Experimental CA variants are not
part of the default simulator.

## 1. Install

For file-based GIS runs, install the GIS extra:

```bash
python -m pip install -e ".[gis]"
```

Development installs normally use:

```bash
python -m pip install -e ".[dev,gis]"
```

The installed console entry point is:

```bash
pyfireca
```

## 2. Baseline assumptions

The first complete simulator is deliberately fail-closed:

```text
static raster environment only
north-up raster only
square pixels only
metric cell size supplied explicitly
one aligned grid for all input rasters
Moore-8 physical propagation baseline
Rothermel surface fire behavior
Behave/Catchpole FromIgnitionPoint directional spread
source-cell-controlled outgoing edge ROS
```

It does **not** silently convert 10-m wind to midflame wind, percent moisture to
fractions, percent slope to degrees, or radians to degrees.

Dynamic weather, WRF/NetCDF coupling, crown fire, spotting, suppression, and
new PyFireCA-specific CA research variants remain outside this baseline.

## 3. Required input rasters

The configuration references exactly ten aligned GeoTIFF layers:

| Key | Meaning | Required unit |
|---|---|---|
| `fuel_model` | Standard fuel-model number | integer code |
| `dead_1h_moisture` | 1-h dead fuel moisture | fraction |
| `dead_10h_moisture` | 10-h dead fuel moisture | fraction |
| `dead_100h_moisture` | 100-h dead fuel moisture | fraction |
| `live_herbaceous_moisture` | live herb moisture | fraction |
| `live_woody_moisture` | live woody moisture | fraction |
| `midflame_wind_speed` | midflame wind speed | m/s |
| `wind_from_direction` | meteorological wind-from bearing | degrees |
| `slope` | slope angle | degrees |
| `aspect` | downslope aspect bearing | degrees |

All rasters must share:

```text
shape
CRS
full affine transform
pixel size
extent/alignment
```

The `fuel_model` layer defines the permanent simulation domain through its
NoData mask. NoData in required behavior layers is allowed outside that domain
but fails validation inside it.

### Fuel catalogue

The current audited baseline contains:

```text
Anderson FM1–FM13
Scott–Burgan GR1 (101)
```

The Anderson records and GR1 provenance are pinned to the USFS Fire Lab Behave
core revision recorded by PyFireCA. Unknown/unaudited fuel codes fail explicitly.

## 4. Configuration file

Use configuration version 1. See:

```text
examples/static_run.yml
```

Minimal structure:

```yaml
version: 1
cell_size_m: 30.0
use_wind_speed_limit: false

inputs:
  fuel_model: data/fuel_model.tif
  dead_1h_moisture: data/dead_1h_moisture.tif
  dead_10h_moisture: data/dead_10h_moisture.tif
  dead_100h_moisture: data/dead_100h_moisture.tif
  live_herbaceous_moisture: data/live_herbaceous_moisture.tif
  live_woody_moisture: data/live_woody_moisture.tif
  midflame_wind_speed: data/midflame_wind_speed.tif
  wind_from_direction: data/wind_from_direction.tif
  slope: data/slope.tif
  aspect: data/aspect.tif

ignitions:
  - row: 100
    col: 120
    time_s: 0.0

output:
  directory: runs/static-example
```

Relative paths are resolved against the YAML file's directory, not the current
shell working directory.

### Ignition events

Each ignition is explicit:

```yaml
ignitions:
  - row: 100
    col: 120
    time_s: 0
  - row: 110
    col: 130
    time_s: 600
```

The baseline supports:

- one ignition cell;
- multiple simultaneous ignition cells;
- multiple ignitions with specified physical times;
- duplicate cell events, where the earliest event wins.

Ignitions outside the burnable domain fail validation.

## 5. Validate before running

```bash
pyfireca validate examples/static_run.yml
```

Validation checks the configuration and referenced inputs, including:

```text
required YAML keys
input file existence
raster alignment
north-up square-grid geometry
explicit cell-size consistency
NoData/domain semantics
fuel-model catalogue membership
static Rothermel input completeness
ignition bounds and domain membership
```

A successful validation does not create the run output directory.

## 6. Run

```bash
pyfireca run examples/static_run.yml
```

The command validates the same baseline contracts and then executes the static
physical-arrival simulation.

The configured run directory must be empty if it already exists. PyFireCA does
not overwrite a previous result directory silently.

## 7. Result directory

A completed run has this baseline structure:

```text
runs/static-example/
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

### `config.resolved.yml`

Stores the fully resolved configuration, including absolute input/output paths.

### `metadata.json`

Stores scientific/run provenance, including:

```text
raster shape / CRS / affine transform / cell size
ignition events
fuel models encountered
pinned fuel-catalogue source commit
SHA-256 for every input raster
```

### `environment.json`

Stores execution-environment information such as:

```text
PyFireCA version
Python version
platform
GitHub commit when available from the execution environment
```

### `metrics.json`

Current minimum run statistics:

```text
domain cell count
burned cell count
unreachable domain cell count
burned area (m²)
first arrival (s)
last arrival (s)
runtime (s)
```

### `outputs/arrival_time.tif`

- dtype: `float64`;
- unit: seconds;
- finite values are first-arrival times;
- file NoData value: `-1` for cells without finite arrival.

Arrival times themselves are physically non-negative, so `-1` cannot conflict
with a valid arrival.

### `outputs/state.tif`

Terminal canonical state:

```text
0  UNBURNABLE / outside domain
1  UNBURNED / in-domain but unreachable
3  BURNED / eventually reached
```

It is deliberately a terminal state, not an arbitrary `BURNING` snapshot.
Programmatic users can generate physical-time snapshots with
`StaticWildfireSimulationResult.state_at(...)`.

### `outputs/burned_mask.tif`

`uint8` final footprint:

```text
0  not eventually burned
1  eventually burned
```

### `outputs/perimeter.geojson`

The final burned raster footprint is polygonized and transformed from the input
raster CRS to WGS84 before GeoJSON serialization. The file therefore follows a
portable longitude/latitude GeoJSON coordinate convention instead of embedding
projected raster coordinates as if they were RFC-7946 coordinates.

## 8. Python API

The same baseline can be driven without the CLI:

```python
from pyfireca import load_static_run_config, run_static_config

config = load_static_run_config("run.yml")
result, artifacts = run_static_config(config)

print(result.burned_area_m2)
print(artifacts.outputs.arrival_time)
```

For in-memory workflows, use:

```python
from pyfireca import (
    IgnitionEvent,
    StaticWildfireSimulationRequest,
    build_ignition_times,
    run_static_wildfire_simulation,
)
```

The file/config/CLI layers are thin assembly around the same validated
simulation objects; they do not implement a second scientific model.

## 9. What this baseline is for

The purpose of this release line is to establish a simple, complete,
reproducible simulator before introducing new PyFireCA-specific CA methods.

Research ideas on neighborhood topology, lattice bias, and heterogeneous
interface coupling are intentionally recorded separately in
`docs/FUTURE_RESEARCH.md` and are not default simulator behavior.
