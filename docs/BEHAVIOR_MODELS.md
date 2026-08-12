# Fire-behavior models

PyFireCA keeps **fire behavior** separate from **CA / raster propagation**.

```text
model-specific inputs
        ↓
FireBehaviorModel
        ↓
FireBehaviorResult
        ↓
directional spread adapter
        ↓
arrival / CA propagation
```

The common output contract does **not** force all models to share the same input
variables. Rothermel and Canadian FBP are scientifically different systems and
therefore keep separate typed input dataclasses.

## Runtime independence policy

PyFireCA behavior models are implemented inside this repository.

The runtime implementation must **not** import or call Cell2Fire, cffdrs,
Pyretechnics, SimFire, KITRAL/C2FK, Behave, Prometheus, or another wildfire
behavior package. External projects may be used only for:

- locating primary scientific references;
- understanding architecture and model boundaries;
- obtaining independently generated regression values;
- comparing PyFireCA outputs during validation.

This rule keeps the scientific equations auditable and prevents PyFireCA from
becoming a thin wrapper around another simulator.

## Implemented models

### Rothermel surface fire

`RothermelModel` is the original PyFireCA surface-fire behavior baseline.

Native inputs include an explicit fuel bed, dead/live fuel moisture, midflame
wind, slope, aspect, and wind direction. The current implementation includes
Albini-adjusted Rothermel behavior, dynamic herbaceous curing, vector wind/slope
combination, and a Behave-style directional surface-fire ellipse.

### Canadian FBP

`FBPModel` is a self-contained scalar implementation of the Canadian Forest
Fire Behavior Prediction System.

Scientific basis:

- Forestry Canada Fire Danger Group (1992), ST-X-3;
- Wotton, Alexander & Taylor (2009), GLC-X-10.

Native inputs use the FBP variables rather than Rothermel variables:

- Canadian FBP fuel type;
- FFMC and BUI;
- 10-m wind speed and wind-from direction;
- slope percent and aspect;
- latitude, longitude, elevation and Julian day for foliar moisture;
- optional mixedwood, dead-fir, grass-curing, grass-load and canopy overrides.

The implemented equilibrium chain includes:

```text
FFMC
 ↓
fine-fuel moisture function
 ↓
zero-wind ISI
 ↓
fuel-specific zero-wind ROS
 ↓
slope-equivalent wind
 ↓
wind + slope vector
 ↓
final ISI
 ↓
fuel-specific RSI + BUI effect
 ↓
head / back ROS
 ↓
surface fuel consumption
 ↓
Van Wagner crown threshold / CFB
 ↓
C6 crown ROS correction
 ↓
total fuel consumption + head fire intensity
 ↓
FBP ellipse / directional ROS
```

Supported burnable types currently include C1-C7, D1/D2, M1-M4, O1a/O1b and
S1-S3. `NF` and `WA` return zero behavior.

`FBPComputation` keeps FBP-native quantities in their documented units.
`FBPModel.compute()` converts the quantities crossing into the generic PyFireCA
boundary:

- m/min → m/s;
- kW/m → W/m;
- FBP-specific secondary quantities → diagnostics.

`FBPEllipse` and `HomogeneousFBPDirectionalSpreadRate` then provide
direction-specific ROS for the arrival solver without assigning head ROS to
all neighbors.

### Van Wagner + Cruz crown fire

`CruzCrownFireModel` is a separate crown-fire behavior component.

It implements:

- Van Wagner critical surface fireline intensity for crown initiation;
- canopy-cover initiation gating;
- Cruz active crown-fire ROS;
- Van Wagner critical crown ROS;
- Cruz passive crown-fire ROS;
- crown fireline intensity from canopy fuel consumed along the flaming front.

This model is intentionally separate from Rothermel. It can later be used in a
composite surface/crown behavior model after the required surface-fire
intensity and canopy rasters are part of the landscape data contract.

## Reference projects and what we borrow

| Project | Behavior model / idea | PyFireCA use |
|---|---|---|
| Cell2Fire | Canadian FBP coupled to cell spread | FBP comparison and CA/behavior separation |
| C2FK | KITRAL behavior model | model/input audit; no runtime reuse |
| Pyretechnics | Rothermel surface + Van Wagner/Cruz crown components | crown-model decomposition and regression comparison |
| SimFire | Rothermel-centered Python simulator | API/manager organization reference |
| GridFire | raster fire-behavior workflow | raster-model integration reference |

Code from GPL projects is not copied into PyFireCA. Scientific equations are
implemented from their primary publications.

## Deferred behavior models

### KITRAL

KITRAL is valuable because C2FK demonstrates a Cell2Fire-compatible alternative
to Canadian FBP with its own fuel coefficients, slope/wind behavior, flame
geometry, intensity and crown logic.

It is **not** a small drop-in equation. Before implementation PyFireCA still
needs a pinned primary-source specification for:

- fuel-type catalogue and coefficients;
- temperature / relative-humidity moisture terms;
- surface ROS;
- slope effect;
- crown transition;
- active crown ROS;
- flame length / height.

The interface will follow the same rule as FBP: native typed inputs, a
self-contained implementation, and conversion only at the
`FireBehaviorResult` boundary.

### Additional candidates

These should be added only when a primary-source specification and independent
validation fixture are available:

- Scott & Burgan fuel-model catalogue for the existing Rothermel equations
  (fuel catalogue, **not** a separate behavior equation);
- Rothermel 1991 crown-fire spread components where scientifically required;
- region-specific empirical systems with clear published calibration domains.

## Validation rule for every new model

A model is not considered implemented merely because it returns a plausible
ROS. Each behavior model must have:

1. equation-level tests;
2. unit and direction tests;
3. at least one external published or independently generated fixture;
4. a clear statement of calibration domain and limitations;
5. a directional-spread contract before it is used by the CA arrival solver.
