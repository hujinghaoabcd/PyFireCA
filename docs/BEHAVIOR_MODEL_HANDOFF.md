# Behavior-model development handoff

> Updated: 2026-08-13
>
> Purpose: preserve the scientific and engineering decisions made while expanding PyFireCA from a Rothermel-only simulator into a multi-model behavior framework.

## 1. Highest-priority rule

**Behavior models must be implemented inside PyFireCA.**

Do not add runtime wrappers around Cell2Fire, cffdrs, Pyretechnics, SimFire,
GridFire, C2FK, Behave, Prometheus, or another fire-behavior package.

External code may be inspected for model decomposition and independent
regression values, but PyFireCA runtime equations must remain self-contained.

This decision was made explicitly during development and must not be relaxed for
convenience without a deliberate project-level decision.

## 2. Current behavior inventory

### Fully integrated surface / combined system

```text
Rothermel
Canadian FBP
```

Both can produce directional source-cell ROS and feed the shared static
`StaticArrivalTimeSolver`.

### Implemented component model

```text
Van Wagner + Cruz crown fire
```

This is implemented and tested as a separate component. It is not yet connected
as the default crown extension of the Rothermel raster simulator because the
landscape contract does not yet include all required canopy/intensity layers.

### Audited but not implemented

```text
KITRAL
```

Do not create a superficial KITRAL adapter from C2FK internals. First pin the
primary equations, fuel coefficients, units, calibration domain, and external
fixtures.

## 3. Canadian FBP implementation files

```text
src/pyfireca/behavior/_fbp_constants.py
src/pyfireca/behavior/fbp.py
src/pyfireca/behavior/fbp_directional.py
src/pyfireca/behavior/fbp_layers.py
src/pyfireca/behavior/fbp_spatial.py
src/pyfireca/behavior/fbp_landscape.py
src/pyfireca/fbp_simulator.py
src/pyfireca/fbp_config.py
src/pyfireca/fbp_workflow.py
src/pyfireca/run_config.py
```

### `_fbp_constants.py`

Owns PyFireCA's Canadian FBP fuel coefficients and canopy lookup values. It is
runtime data, not an import from another implementation.

### `fbp.py`

Owns the scalar equilibrium equations and native data structures:

```text
FBPInputs
FBPComputation
FBPFireType
FBPModel
```

Do not rewrite this module as a vectorized raster implementation merely for
speed. It is the readable scientific reference implementation. Profile the
spatial workflow first; accelerate only measured hotspots later.

`fbp.py` is intentionally excluded from Ruff's auto-formatter so equation
layout remains readable, while Ruff lint still checks the file.

### `fbp_directional.py`

Owns:

```text
FBPEllipse
HomogeneousFBPDirectionalSpreadRate
```

Important decision: FBP does **not** use the Rothermel/Behave ellipse helper.
The adapter uses FBP's native head/back/flank rates and ray/ellipse
intersection, preserving head and backing rates exactly.

### `fbp_layers.py`

Maps aligned `SpatialLayer`s to one `FBPInputs(row, col)`.

Required units are strict and fail closed. No hidden unit conversion is
allowed.

### `fbp_spatial.py`

Caches one homogeneous FBP provider per source cell. Outgoing edges reuse the
source-cell FBP state and ellipse.

The current edge semantic remains:

> source cell controls outgoing edge ROS.

Do not add source-target averaging here. Interface coupling is a separate CA
research dimension.

### `fbp_landscape.py`

Thin assembly:

```text
LandscapeInput
→ StaticRasterFBPInputsProvider
→ StaticSpatialFBPDirectionalSpreadRate
→ StaticArrivalTimeSolver
```

It enforces the same current geometry as Rothermel:

```text
north-up
square metric cell
cell_size_m matches affine transform
```

### `fbp_simulator.py`

High-level in-memory API:

```text
StaticFBPSimulationRequest
run_static_fbp_simulation
```

The result is the common `StaticWildfireSimulationResult`, so output code is
shared with Rothermel.

### `fbp_config.py`

Owns FBP-specific YAML structures:

```text
StaticFBPRasterInputPaths
StaticFBPRunConfig
load_static_fbp_run_config
```

Do not merge these fields into `StaticRunConfig` merely to have one giant
configuration object. Rothermel and FBP have materially different scientific
inputs.

### `fbp_workflow.py`

Owns FBP file I/O assembly, validation, provenance, and the common run-directory
writer.

Input rasters are read once. Validation reuses the constructed landscape and
must happen before creating the output run directory.

### `run_config.py`

Model-aware CLI dispatcher.

Current version-1 rule:

```text
no behavior block      → legacy Rothermel schema
behavior.model: fbp    → explicit FBP schema
```

This preserves all existing Rothermel config files.

A later configuration version can make both models explicit, but do not break
version-1 merely for cosmetic symmetry.

## 4. FBP raster contract

Required keys:

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

Required units:

```text
fbp_fuel_type          code
ffmc                    code
bui                     index
wind_speed_10m          km/h
wind_from_direction     deg
slope_percent           percent
aspect                  deg
latitude                deg
longitude               deg
elevation               m
```

Do not infer:

```text
Rothermel moisture → FFMC/BUI
midflame wind → 10-m wind
slope degrees → slope percent
projected coordinates → latitude/longitude
```

If a preprocessing utility is added later, it must be explicit and outside the
behavior kernel.

## 5. FBP fuel-code semantics

Current raster codes:

```text
1  C1
2  C2
3  C3
4  C4
5  C5
6  C6
7  C7
8  D1
9  D2
10 M1
11 M2
12 M3
13 M4
14 O1a
15 O1b
16 S1
17 S2
18 S3
19 NF
20 WA
```

`NF` and `WA` must not remain inside the burnable arrival graph. The FBP file
loader removes 19/20 from the simulation domain; the lower-level provider also
rejects them if a caller incorrectly marks them burnable.

## 6. Validation truth

Representative Wotton-2009 values currently protected include:

```text
C1
ROS  5.556055013652935 m/min
HFI  3139.248959888172 kW/m
CFB  0.6460598615576801
RAZ  174.69644784656137 deg

C6
ROS  42.78072962636479 m/min
HFI  36676.84532562521 kW/m
CFB  0.910886906644051
RAZ  180 deg

M3
ROS  9.355199377218359 m/min
HFI  4002.8596994291224 kW/m
CFB  0.3159538851361391
RAZ  13.30574360051394 deg

M4
ROS  36.09755174601528 m/min
HFI  35165.57694213195 kW/m
CFB  0.9994490848202203
RAZ  43.98157656980864 deg

O1a
ROS  134.67179731130906 m/min
HFI  40401.53919339272 kW/m
CFB  0
RAZ  40.70778526492166 deg
```

Do not change scientific equations to silence formatting or engineering-only CI
failures.

## 7. Crown component files

```text
src/pyfireca/behavior/crown.py
tests/test_crown_behavior.py
```

Implemented:

```text
van_wagner_critical_fireline_intensity_w_m
van_wagner_crown_fire_initiates
cruz_active_crown_ros_m_min
van_wagner_critical_crown_ros_m_min
cruz_passive_crown_ros_m_min
CruzCrownInputs
CruzCrownFireModel
```

The model needs a surface-fire intensity to decide crown initiation. Do not
silently fabricate this from an unvalidated Rothermel output. Connect crown fire
to the raster simulator only after the required surface-intensity/canopy data
contract is explicit and scientifically validated.

## 8. Testing layers

FBP currently has tests at four levels:

```text
equation / scalar regression
directional ellipse
spatial provider / arrival integration
real Rasterio + YAML + CLI end to end
```

Important files:

```text
tests/test_fbp.py
tests/test_fbp_spatial.py
tests/test_fbp_config.py
tests/test_fbp_workflow_rasterio.py
```

The GIS CI job explicitly includes the FBP file-workflow test.

## 9. What external projects contributed

### Cell2Fire

Learned/checked:

```text
FBP as behavior provider for cell spread
behavior/propagation separation
FBP output comparison
```

Do not copy GPL runtime code.

### Pyretechnics

Learned/checked:

```text
surface vs crown behavior decomposition
Van Wagner / Cruz combination
clear component boundaries
```

PyFireCA crown equations are independently implemented.

### SimFire

Mainly confirms a Rothermel-centered Python software organization. It does not
currently justify a new independent behavior-model name in PyFireCA.

### C2FK / KITRAL

Confirms KITRAL is a meaningful alternative behavior system and exposes the
breadth of inputs/components required. It is not permission to copy the model
implementation. Pin primary literature before coding.

## 10. Immediate next behavior work

Do **not** resume CA innovation yet merely because multiple behavior models now
exist.

Reasonable next behavior tasks, in order:

```text
1. finish documentation synchronization
2. keep Rothermel + FBP CLI workflows green
3. add complete Scott–Burgan fuel catalogue to the Rothermel fuel layer
   if desired (catalogue expansion, not a new behavior model)
4. define canopy raster contract before composing Rothermel + Cruz crown
5. audit KITRAL primary equations and validation domain
6. only then implement KITRAL if the reference is sufficiently complete
```

The paper-innovation line on CA neighborhoods/lattice/interface coupling remains
stored in `docs/FUTURE_RESEARCH.md` and should stay separate from behavior-model
completion.
