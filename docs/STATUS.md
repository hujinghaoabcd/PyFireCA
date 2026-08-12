# Project status

> Updated: 2026-08-13

PyFireCA is currently an **alpha, static raster wildfire simulator and CA research framework**. The baseline simulator is complete enough to run reproducible GIS experiments, while CA-method innovation remains intentionally deferred until the simulator and behavior-model layer are stable.

## Current stable architecture

```text
GIS / raster inputs
      ↓
model-specific behavior inputs
      ↓
┌──────────────────────────────┐
│ Fire behavior                │
│ Rothermel                    │
│ Canadian FBP                 │
│ Van Wagner + Cruz component  │
└──────────────┬───────────────┘
               ↓
       directional ROS
               ↓
    StaticArrivalTimeSolver
               ↓
  arrival / state / footprint
               ↓
GeoTIFF / GeoJSON / metadata
```

The classic synchronous CA reference path (`RasterGrid`, `Neighborhood`,
`TransitionRule`, `Simulation`) remains separate from the physical
arrival-time wildfire baseline.

## Implemented behavior models

### Rothermel

Status: **integrated simulator path**.

Includes:

- audited Anderson FM1-FM13 fuel models plus GR1;
- dynamic herbaceous curing;
- no-wind/no-slope Rothermel ROS;
- wind/slope effects and vector combination;
- directional surface-fire ellipse;
- static heterogeneous raster provider;
- YAML / CLI / GIS workflow.

### Canadian FBP

Status: **integrated simulator path**.

Implemented directly inside PyFireCA; no runtime dependency on Cell2Fire,
cffdrs, or another FBP package.

Includes:

- C1-C7, D1/D2, M1-M4, O1a/O1b, S1-S3, NF/WA semantics;
- FFMC/BUI fire-weather inputs;
- 10-m wind and slope-vector interaction;
- head/back ROS;
- fuel consumption;
- foliar moisture;
- crown fraction burned and C6 crown correction;
- fire intensity;
- FBP head/back/flank ellipse;
- per-cell spatial provider and cache;
- static raster arrival simulation;
- model-specific YAML schema;
- CLI `validate` / `run` workflow;
- real Rasterio end-to-end tests.

### Van Wagner + Cruz crown fire

Status: **implemented and tested component; not yet composed into the default raster surface-fire simulator**.

The current component implements crown initiation, active/passive crown ROS, and
crown intensity. A full surface+crown raster workflow requires an explicit
canopy data contract and validated surface-intensity coupling.

### KITRAL

Status: **reference audited, not implemented**.

Do not wrap C2FK. Pin primary equations, coefficients, calibration domain, and
independent validation fixtures before adding a self-contained KITRAL model.

## Runtime dependency policy

Behavior equations must be owned by PyFireCA. External wildfire simulators are
reference/oracle material only.

Current core runtime dependencies remain:

```text
numpy
PyYAML
```

GIS extra:

```text
rasterio
```

No `cffdrs`, Cell2Fire, Pyretechnics, SimFire, or other behavior package is a
PyFireCA runtime dependency.

## User-facing file workflows

### Rothermel version-1 YAML

Legacy version-1 files remain valid and omit the `behavior` block.

### FBP version-1 YAML

FBP files explicitly declare:

```yaml
behavior:
  model: fbp
  julian_day: 180
```

with model-specific FBP rasters.

Both use:

```bash
pyfireca validate config.yml
pyfireca run config.yml
```

and produce the same result-directory contract:

```text
config.resolved.yml
metadata.json
environment.json
metrics.json
log.txt
outputs/
  arrival_time.tif
  state.tif
  burned_mask.tif
  perimeter.geojson
```

## Validation status

Current CI gates include:

```text
Ruff lint
Ruff format
Python 3.11
Python 3.12
Python 3.13
GIS / Rasterio workflows
wheel + sdist build
clean wheel install
console-script smoke
MIT distribution metadata
```

FBP additionally has:

- Wotton-2009 scalar regression cases;
- direction/ellipse tests;
- spatial-provider tests;
- real GeoTIFF + YAML + CLI end-to-end tests.

## Research line status

The CA-method innovation line is **recorded but frozen** in
`FUTURE_RESEARCH.md`.

Stored topics include:

```text
lattice bias / directional discretization
VN4 vs Moore8 analytical error
cell-size vs direction-set convergence
heterogeneous interface coupling
future extended/dynamic neighborhoods
```

Do not resume these merely because FBP is now implemented. The simulator and
behavior model layer should remain the active engineering priority until the
next explicit research phase.

## Current documentation of record

```text
DESIGN.md
BEHAVIOR_MODELS.md
BEHAVIOR_MODEL_HANDOFF.md
RUNNING_SIMULATOR.md
VALIDATION.md
FUTURE_RESEARCH.md
HANDOFF.md
STATUS.md
```

## Immediate next work

1. Keep the new FBP/Rothermel multi-model workflow fully green in CI.
2. Synchronize README and simulator documentation with the multi-model state.
3. Decide whether the next behavior task is:
   - complete Scott-Burgan fuel catalogue for Rothermel, or
   - define canopy raster contract and compose the existing Cruz crown component.
4. Audit KITRAL from primary literature before implementation.
5. Continue to defer new CA-method innovation until explicitly restarted.

## Release

No release/tag should be created yet. The project remains at `0.1.0a0` during
active development.
