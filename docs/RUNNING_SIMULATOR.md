# Running the static simulator

> Updated: 2026-08-13

PyFireCA currently supports two self-contained static raster behavior paths:

```text
Rothermel surface-fire behavior
Canadian FBP behavior
```

Both feed the same physical earliest-arrival propagation engine and produce the
same GIS result directory. Experimental PyFireCA-specific CA variants remain
outside the default simulator.

## 1. Install

For file-based GIS runs:

```bash
python -m pip install -e ".[gis]"
```

Development:

```bash
python -m pip install -e ".[dev,gis]"
```

CLI:

```bash
pyfireca --help
pyfireca validate config.yml
pyfireca run config.yml
```

## 2. Shared static assumptions

Both current behavior paths are intentionally fail-closed:

```text
static raster environment
north-up grid
square pixels
explicit metric cell size
aligned rasters
Moore-8 physical propagation baseline
source-cell-controlled outgoing edge ROS
static edge travel times
```

The arrival solver uses:

```text
cell-local behavior
→ direction-specific ROS
→ edge distance / ROS
→ edge travel time
→ earliest arrival time
```

Dynamic weather, WRF/NetCDF time-varying forcing, spotting, suppression, and
new PyFireCA-specific CA methods are not yet part of this workflow.

## 3. Choose the behavior path

### 3.1 Rothermel: legacy version-1 schema

Existing version-1 Rothermel configs remain valid and **do not** need a
`behavior` block.

Example:

```text
examples/static_run.yml
```

Required raster keys and units:

| Key | Unit |
|---|---|
| `fuel_model` | integer code |
| `dead_1h_moisture` | fraction |
| `dead_10h_moisture` | fraction |
| `dead_100h_moisture` | fraction |
| `live_herbaceous_moisture` | fraction |
| `live_woody_moisture` | fraction |
| `midflame_wind_speed` | m/s |
| `wind_from_direction` | deg |
| `slope` | deg |
| `aspect` | deg |

Example:

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
    time_s: 0

output:
  directory: runs/rothermel-example
```

Current audited Rothermel fuel catalogue includes Anderson FM1-FM13 and GR1.

### 3.2 Canadian FBP: explicit behavior schema

Example:

```text
examples/static_fbp_run.yml
```

FBP must explicitly declare the model:

```yaml
behavior:
  model: fbp
```

Required raster keys and units:

| Key | Unit |
|---|---|
| `fbp_fuel_type` | integer code |
| `ffmc` | code |
| `bui` | index |
| `wind_speed_10m` | km/h |
| `wind_from_direction` | deg |
| `slope_percent` | percent |
| `aspect` | deg |
| `latitude` | deg |
| `longitude` | deg |
| `elevation` | m |

Example:

```yaml
version: 1

behavior:
  model: fbp
  julian_day: 180
  percent_conifer: 50
  percent_dead_fir: 35
  grass_fuel_load_kg_m2: 0.35
  grass_curing_percent: 80

cell_size_m: 30.0

inputs:
  fbp_fuel_type: data/fbp_fuel_type.tif
  ffmc: data/ffmc.tif
  bui: data/bui.tif
  wind_speed_10m: data/wind_speed_10m.tif
  wind_from_direction: data/wind_from_direction.tif
  slope_percent: data/slope_percent.tif
  aspect: data/aspect.tif
  latitude: data/latitude.tif
  longitude: data/longitude.tif
  elevation: data/elevation.tif

ignitions:
  - row: 100
    col: 100
    time_s: 0

output:
  directory: runs/fbp-example
```

Supported numeric FBP codes:

```text
1  C1       10 M1
2  C2       11 M2
3  C3       12 M3
4  C4       13 M4
5  C5       14 O1a
6  C6       15 O1b
7  C7       16 S1
8  D1       17 S2
9  D2       18 S3
19 NF
20 WA
```

`NF` and `WA` become unburnable domain cells in the file workflow.

FBP is implemented inside PyFireCA; the runtime does not call Cell2Fire,
cffdrs, or another FBP package.

## 4. No hidden cross-model conversions

PyFireCA intentionally does not translate one model's input rasters into the
other model's inputs.

Examples of operations that are **not** performed implicitly:

```text
Rothermel fuel moisture → FFMC/BUI
midflame wind → 10-m FBP wind
slope degrees → FBP slope percent
FBP fuel code → Anderson fuel model
projected x/y → FBP latitude/longitude
```

If such preprocessing is added later, it will be an explicit preprocessing
step rather than behavior-kernel magic.

## 5. Raster alignment and domain

All rasters in one run must share:

```text
shape
CRS
full affine transform
pixel size
extent/alignment
```

NoData in a required behavior layer is allowed outside the permanent burnable
domain but fails validation inside the domain.

Rothermel uses its fuel-model raster NoData contract for the domain. FBP also
removes explicit `NF` and `WA` cells from the burnable domain.

## 6. Ignitions

Both models use the same ignition contract:

```yaml
ignitions:
  - row: 100
    col: 120
    time_s: 0
  - row: 110
    col: 130
    time_s: 600
```

Supported:

- one ignition;
- multiple simultaneous ignitions;
- delayed ignitions with physical seconds;
- repeated cell events, where the earliest event wins.

Ignition outside the burnable domain fails validation.

## 7. Validate

```bash
pyfireca validate config.yml
```

Validation checks the model-specific schema and the shared spatial contracts.
A successful validation does not create the configured output directory.

Examples of failures that are caught before a run:

```text
unknown/missing YAML keys
missing raster file
misaligned rasters
wrong model-specific units
unsupported fuel code
NoData inside burnable domain
non-square / rotated grid
cell_size_m mismatch
invalid ignition
```

## 8. Run

```bash
pyfireca run config.yml
```

The configured output directory must be absent or empty. PyFireCA does not
silently overwrite an existing run.

## 9. Common result directory

Both Rothermel and FBP produce:

```text
runs/<run-name>/
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

Stores the resolved model-specific configuration and absolute paths.

### `metadata.json`

Contains scientific/run provenance.

Shared information includes:

```text
raster geometry
ignitions
input SHA-256 hashes
```

Rothermel records audited fuel-catalogue provenance. FBP records the model name,
scientific references, Julian day, encountered FBP codes, and the fact that the
runtime implementation is self-contained.

### `environment.json`

Records PyFireCA/Python/platform/Git information when available.

### `metrics.json`

Minimum metrics:

```text
domain_cell_count
burned_cell_count
unreachable_domain_cell_count
burned_area_m2
first_arrival_s
last_arrival_s
runtime_s
```

### `arrival_time.tif`

- `float64` seconds;
- finite cells contain first-arrival times;
- file NoData is `-1`.

### `state.tif`

Terminal canonical state:

```text
0 UNBURNABLE
1 UNBURNED / unreachable
3 BURNED
```

### `burned_mask.tif`

`uint8` final footprint: 0/1.

### `perimeter.geojson`

The burned raster footprint is polygonized and transformed to WGS84 before
GeoJSON serialization.

## 10. Python APIs

### Model-aware file workflow

```python
from pyfireca import load_run_config, run_config

config = load_run_config("config.yml")
result, artifacts = run_config(config)
```

### Rothermel-specific file workflow

```python
from pyfireca import load_static_run_config, run_static_config
```

### FBP-specific file workflow

```python
from pyfireca import load_static_fbp_run_config, run_static_fbp_config
```

### In-memory FBP workflow

```python
from pyfireca import StaticFBPSimulationRequest, run_static_fbp_simulation
```

The model-aware CLI and file workflows remain thin assembly layers. Scientific
behavior stays in `pyfireca.behavior`; spatial propagation stays in the arrival
solver.

## 11. Crown-fire component status

The separate `CruzCrownFireModel` is implemented and tested, but is not yet an
option in the static file workflow. Connecting it correctly requires an
explicit canopy/input contract and validated surface-fire intensity coupling.

## 12. Research scope

The current simulator exists to provide a stable base before original CA
innovation. Neighborhood/lattice/interface research is documented separately in
`FUTURE_RESEARCH.md` and is not activated by selecting Rothermel or FBP.
