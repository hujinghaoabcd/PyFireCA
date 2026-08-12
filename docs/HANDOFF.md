# PyFireCA development handoff

> Updated: 2026-08-13
>
> This is the current handoff entrypoint. Read this before continuing development.

## 1. Project objective

PyFireCA is a **wildfire-specific**, modular, modern scientific software
framework for cellular-automata / raster fire-spread simulation.

The current development priority is still:

> finish and stabilize the simple simulator and its behavior-model layer before
> returning to original CA-method innovation.

Urban CA projects were used only as engineering/GIS references. PyFireCA is not
an urban/general GeoCA framework.

## 2. Hard constraints

### Do not publish yet

The package remains `0.1.0a0`. MIT is configured, but no tag/release should be
created until the user explicitly restarts release work.

### Behavior models must be self-contained

Do not add runtime calls to another fire behavior package.

Forbidden as runtime behavior engines include:

```text
Cell2Fire
cffdrs / cffdrs_r
Pyretechnics
SimFire
GridFire
C2FK
Behave / Prometheus
```

These may be used for literature tracing, architecture study, and independent
regression comparison only.

### Do not resume the custom CA paper method yet

Research ideas are stored in `FUTURE_RESEARCH.md`. Record new ideas there but
do not implement extended/adaptive neighborhoods, new edge coupling, or other
original CA methods unless that phase is explicitly restarted.

### PyTorchFire remains out of scope

No differentiable CA, neural CA, Torch/JAX backend, GPU backend, or gradient
calibration in the current development line.

## 3. Current main simulation architecture

```text
                       PyFireCA
                           │
             model-specific data contract
                           │
           ┌───────────────┴───────────────┐
           │                               │
      Rothermel                        Canadian FBP
           │                               │
 directional surface ROS             FBP directional ROS
           └───────────────┬───────────────┘
                           ↓
                StaticArrivalTimeSolver
                           ↓
               StaticWildfireSimulationResult
                           ↓
                 common GIS output writer
```

Separate from this physical arrival path, the repository retains the simple
synchronous CA reference:

```text
RasterGrid
→ Neighborhood
→ TransitionRule
→ Simulation.step()
```

Do not collapse these two concepts into one implementation.

## 4. Rothermel path

The original baseline remains stable and backward compatible.

Main files:

```text
behavior/rothermel.py
behavior/_rothermel_equations.py
behavior/_rothermel_base.py
behavior/_rothermel_dynamic.py
behavior/_rothermel_effects.py
behavior/_rothermel_vectors.py
behavior/_surface_ellipse.py
behavior/rothermel_model.py
behavior/rothermel_directional.py
behavior/rothermel_layers.py
behavior/rothermel_spatial.py
behavior/rothermel_landscape.py
config.py
workflow.py
simulator.py
```

Legacy version-1 YAML with no `behavior` block means Rothermel.

## 5. Canadian FBP path

FBP has now been implemented directly in PyFireCA and connected to the same
arrival/output infrastructure.

Read `BEHAVIOR_MODEL_HANDOFF.md` before modifying it.

Main files:

```text
behavior/_fbp_constants.py
behavior/fbp.py
behavior/fbp_directional.py
behavior/fbp_layers.py
behavior/fbp_spatial.py
behavior/fbp_landscape.py
fbp_simulator.py
fbp_config.py
fbp_workflow.py
run_config.py
```

The FBP input schema is intentionally different from Rothermel.

Required raster keys:

```text
fbp_fuel_type
ffmc
bui
wind_speed_10m
wind_from_direction
slope_percent
aspect
latitude
longitude
elevation
```

Do not infer these from the Rothermel layers.

FBP YAML explicitly declares:

```yaml
behavior:
  model: fbp
  julian_day: 180
```

The CLI dispatcher lives in `run_config.py`.

## 6. Crown-fire component

`behavior/crown.py` contains the self-contained Van Wagner + Cruz component.
It is tested but **not yet connected as a default extension of Rothermel**.

Do not wire it in by simply taking an unvalidated surface intensity. Before
composition, define:

```text
canopy cover
canopy base height
canopy height
canopy bulk density
foliar moisture
fine-fuel moisture
surface fireline intensity provenance
10-m wind
```

as explicit, validated data contracts.

## 7. KITRAL

C2FK confirms KITRAL is a meaningful independent behavior system, but PyFireCA
has not implemented it yet.

Before coding:

1. identify the primary published equations;
2. pin the fuel coefficients and units;
3. document the Chilean calibration/application domain;
4. define typed inputs and outputs;
5. obtain independent numerical fixtures;
6. only then implement PyFireCA-native equations.

Do not wrap or copy C2FK runtime code.

## 8. Config and CLI compatibility

Current model dispatch:

```text
version: 1, no behavior block
→ old Rothermel loader/workflow

version: 1, behavior.model: fbp
→ FBP loader/workflow
```

This asymmetry is intentional for backward compatibility.

Do not break all existing Rothermel YAML merely to make the schema visually
symmetric. A later configuration version may make all behavior models explicit.

Common CLI:

```bash
pyfireca validate config.yml
pyfireca run config.yml
```

Common output contract:

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

## 9. Tests that must stay green

General gates:

```text
ruff check .
ruff format --check .
pytest
```

Python matrix:

```text
3.11
3.12
3.13
```

GIS integration includes both Rothermel and FBP real-raster workflows.

Important FBP tests:

```text
tests/test_fbp.py
tests/test_fbp_spatial.py
tests/test_fbp_config.py
tests/test_fbp_workflow_rasterio.py
```

Important crown test:

```text
tests/test_crown_behavior.py
```

Do not regenerate scientific reference expectations simply because a code
change disagrees with them. Investigate the equation/units/directions first.

## 10. Scientific validation policy

For a new behavior model, require:

```text
primary scientific reference
self-contained implementation
equation tests
unit/direction tests
external numerical fixture
directional spread contract
spatial integration test
CLI/GIS test before user-facing support
```

This is now the minimum standard established by Rothermel and FBP.

## 11. Engineering rules

Continue to preserve:

```text
src/ layout
pyproject.toml as project configuration
NumPy reference implementation
strict input units
explicit RNG where stochastic behavior is introduced
logging rather than scattered print in library code
no silent raster resampling
no silent unit conversion
real GIS round-trip tests
reproducible input SHA-256 metadata
```

Avoid adding abstraction solely for hypothetical future backends.

## 12. Next recommended sequence

At the current handoff point:

```text
1. finish documentation synchronization for Rothermel + FBP
2. keep new multi-model CLI workflow fully green
3. optionally expand Scott–Burgan fuel catalogue for Rothermel
4. define canopy raster/data contract
5. compose existing Cruz crown component only after validation
6. perform primary-source KITRAL audit
7. implement KITRAL only if reference specification is complete
8. return to CA-method innovation later
```

## 13. Documentation map

Read in this order:

```text
STATUS.md
HANDOFF.md                 ← this file
BEHAVIOR_MODELS.md         ← behavior architecture/design
BEHAVIOR_MODEL_HANDOFF.md  ← detailed implementation handoff
RUNNING_SIMULATOR.md       ← user workflow
VALIDATION.md
FUTURE_RESEARCH.md         ← frozen paper ideas
```

The repository should remain understandable from these documents without
requiring recovery of chat history.
