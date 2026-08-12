# Fire-behavior model architecture

> Updated: 2026-08-13
>
> Scope: scientific design, implementation boundaries, model contracts, validation, and extension rules for `pyfireca.behavior`.

PyFireCA deliberately separates **fire behavior** from **spatial propagation**.
A behavior model estimates how fire behaves under local fuel, weather, and
terrain conditions. The CA / arrival layer decides how that local behavior is
used to move fire between raster cells.

```text
model-specific scientific inputs
              ↓
        behavior model
              ↓
model-native detailed result
              ↓
   FireBehaviorResult boundary
              ↓
directional spread-rate provider
              ↓
 StaticArrivalTimeSolver / CA
```

This separation is essential for PyFireCA research: changing Rothermel to FBP
must not require rewriting the arrival solver, while changing the CA
neighborhood or edge semantics must not require rewriting the fire-behavior
equations.

## 1. Runtime-independence rule

All behavior models shipped by PyFireCA are implemented inside this repository.

The PyFireCA runtime must **not** import or call:

```text
Cell2Fire
cffdrs / cffdrs_r
Pyretechnics
SimFire
GridFire
C2FK / KITRAL software
Behave / Prometheus
another wildfire-behavior package
```

External projects may be used only to:

- identify primary scientific references;
- understand model boundaries and software architecture;
- produce or locate independent validation values;
- compare outputs during regression testing;
- audit units, direction conventions, and known edge cases.

The numerical equations that run inside PyFireCA remain PyFireCA code. This
keeps the package scientifically auditable, avoids turning it into a wrapper,
and prevents incompatible external licenses from entering the MIT runtime.

The core runtime dependency list remains intentionally small:

```text
NumPy
PyYAML
```

Rasterio remains an optional GIS adapter dependency and is not a fire-behavior
dependency.

## 2. Common result boundary

`FireBehaviorResult` is the small model-independent boundary used by the rest
of the package. It contains quantities such as:

```text
spread_rate_m_s
spread_direction_deg
fireline_intensity_w_m
flame_length_m
diagnostics
```

The common result does **not** imply a common input schema. Rothermel and FBP
are different scientific systems and must retain different native inputs.

The rule is:

> Normalize outputs at the package boundary; never distort model inputs merely
> to make two models look identical.

## 3. Implemented behavior systems

### 3.1 Rothermel surface-fire model

`RothermelModel` is the original PyFireCA behavior baseline.

Native inputs include:

```text
explicit fuel-bed model
dead 1-h / 10-h / 100-h moisture
live herbaceous / woody moisture
midflame wind speed
meteorological wind-from direction
slope angle
aspect
```

The implemented chain includes:

```text
fuel-bed properties
→ dynamic herbaceous curing when applicable
→ no-wind/no-slope Rothermel ROS
→ wind factor
→ slope factor
→ wind/slope vector combination
→ maximum spread rate + direction
→ optional wind-speed limit
→ Behave/Catchpole surface-fire ellipse
→ arbitrary directional ROS
```

The Rothermel path has its own audited standard-fuel catalogue and scientific
regression fixtures. It does not share the Canadian FBP fuel-type system.

### 3.2 Canadian Fire Behavior Prediction System (FBP)

`FBPModel` is a **self-contained PyFireCA implementation** of the Canadian
Forest Fire Behavior Prediction System.

Primary scientific basis:

- Forestry Canada Fire Danger Group (1992), *Development and Structure of the
  Canadian Forest Fire Behavior Prediction System*, ST-X-3;
- Wotton, Alexander & Taylor (2009), *Updates and revisions to the 1992
  Canadian Forest Fire Behavior Prediction System*, GLC-X-10.

External implementations such as Cell2Fire and CFFDRS software were used only
as comparison references. PyFireCA does not import or call them.

#### Native FBP inputs

FBP intentionally uses its own input contract:

```text
Canadian FBP fuel type
FFMC
BUI
10-m wind speed [km/h]
wind-from direction [deg]
slope [%]
aspect [deg]
latitude / longitude
elevation
Julian day
```

Optional model-specific quantities include:

```text
percent conifer        M1/M2
percent dead fir       M3/M4
grass fuel load        O1a/O1b
grass curing           O1a/O1b
day of minimum FMC
canopy overrides
```

PyFireCA does **not** derive these from Rothermel fuel-moisture rasters and does
not silently convert midflame wind into 10-m wind.

#### Implemented FBP equilibrium chain

```text
FFMC
 ↓
fine-fuel moisture content/function
 ↓
zero-wind Initial Spread Index
 ↓
fuel-specific zero-wind ROS
 ↓
FBP slope factor
 ↓
slope-equivalent wind
 ↓
10-m wind + slope vector combination
 ↓
net wind and spread azimuth
 ↓
head/back ISI
 ↓
fuel-specific RSI
 ↓
BUI effect
 ↓
head/back ROS
 ↓
surface fuel consumption
 ↓
foliar moisture content/effect
 ↓
critical crown intensity + critical ROS
 ↓
crown fraction burned
 ↓
C6 crown-spread correction
 ↓
total fuel consumption
 ↓
head fire intensity
 ↓
length-to-breadth / flank ROS
```

Supported codes:

```text
C1 C2 C3 C4 C5 C6 C7
D1 D2
M1 M2 M3 M4
O1a O1b
S1 S2 S3
NF WA
```

`NF` and `WA` are non-burnable. At raster level they are removed from the
simulation domain rather than treated as zero-ROS cells that the graph could
enter and later leave.

#### Native result

`FBPComputation` retains FBP-native quantities such as:

```text
head/back/flank ROS [m/min]
spread azimuth
net wind speed [km/h]
length-to-breadth ratio
surface/crown/total fuel consumption [kg/m²]
head fire intensity [kW/m]
crown fraction burned
foliar moisture
critical intensity / ROS
ISI
BUI effect
slope factor
fire type
```

`FBPModel.compute()` converts only the quantities crossing the common package
boundary:

```text
m/min → m/s
kW/m  → W/m
FBP secondary variables → diagnostics
```

### 3.3 FBP directional ellipse

`FBPEllipse` and `HomogeneousFBPDirectionalSpreadRate` convert the FBP
head/back/flank solution into arbitrary radial spread rates.

This is deliberately separate from the Rothermel surface ellipse. PyFireCA does
not reuse a Rothermel eccentricity merely because both models produce
approximately elliptical fire growth.

The FBP directional adapter constructs the translating ellipse from native:

```text
head ROS
back ROS
flank ROS
heading
```

and solves the ray/ellipse intersection for each raster-neighbor bearing. The
head and backing values are therefore preserved exactly.

### 3.4 Van Wagner + Cruz crown-fire component

`CruzCrownFireModel` is a second independently implemented behavior component.
It currently represents crown behavior rather than a complete replacement for
surface-fire behavior.

Implemented equations include:

```text
Van Wagner critical surface fireline intensity
canopy-cover crown-initiation gate
Cruz active crown-fire ROS
Van Wagner critical crown ROS
Cruz passive crown-fire ROS
crown fireline intensity
```

The component has its own `CruzCrownInputs` contract including surface
intensity, canopy cover/base/height/bulk density, foliar/fine-fuel moisture,
10-m wind, and direction.

It is intentionally not hidden inside `RothermelModel`. A later composite
surface+crown model can combine the two explicitly after canopy layers and a
validated surface-intensity path are part of the landscape contract.

## 4. FBP spatial architecture

FBP is not limited to scalar calculations. The current static spatial chain is:

```text
10 aligned FBP raster layers
          ↓
StaticRasterFBPInputsProvider
          ↓
FBPInputs(row, col)
          ↓
FBPModel
          ↓
FBPComputation
          ↓
FBPEllipse
          ↓
StaticSpatialFBPDirectionalSpreadRate
          ↓
directional ROS(row, col, offset)
          ↓
StaticArrivalTimeSolver
```

`StaticSpatialFBPDirectionalSpreadRate` lazily caches one homogeneous FBP
behavior state per source cell so its outgoing Moore-8 edges do not recompute
the entire FBP system eight times.

The edge semantic is still the current baseline rule:

> The source cell controls outgoing edge ROS.

Target-cell/interface coupling remains a separate CA research question and is
not hidden inside FBP.

## 5. FBP raster data contract

`StaticRasterFBPInputsProvider` requires exactly these model-native static
layers:

| Layer | Required unit |
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

All layers must be static, aligned, and complete inside the burnable domain.
Wrong units are rejected instead of converted implicitly.

Current physical geometry is the same conservative geometry used by the
Rothermel file simulator:

```text
north-up
square cells
metric cell_size_m
cell_size_m == affine pixel size
immediate physical neighbors
```

## 6. Model-aware YAML / CLI workflow

The existing version-1 Rothermel configuration remains backward-compatible:

```yaml
version: 1
cell_size_m: 30
inputs:
  fuel_model: ...
  # Rothermel layers
```

Absence of a `behavior` block means the established Rothermel schema.

Canadian FBP is explicit:

```yaml
version: 1
behavior:
  model: fbp
  julian_day: 180
  percent_conifer: 50
  percent_dead_fir: 35
  grass_fuel_load_kg_m2: 0.35
  grass_curing_percent: 80

cell_size_m: 30
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
```

Both then use the same user commands:

```bash
pyfireca validate config.yml
pyfireca run config.yml
```

The dispatcher selects a model-specific configuration/workflow and both return
the same `StaticWildfireSimulationResult` / `StaticRunArtifacts` output
contract.

## 7. Validation strategy

A behavior model is not considered implemented merely because it returns a
plausible ROS.

Every new model must have:

1. equation-level unit tests;
2. strict unit and direction-convention tests;
3. at least one published or independently generated external regression
   fixture;
4. documented calibration/application domain;
5. a directional-spread contract before CA/arrival use;
6. spatial integration tests if raster simulation is supported;
7. a real file/CLI end-to-end test before it is advertised as a simulator
   option.

Current FBP tests protect representative Wotton-2009 cases including C1, C6,
M3, M4, and O1a, plus non-crowning and non-fuel behavior. The GIS test writes
real FBP GeoTIFFs, validates the YAML, runs the CLI, and checks generated
arrival/perimeter/provenance artifacts.

## 8. Reference projects and their role

| Project | Relevant behavior | PyFireCA role |
|---|---|---|
| Cell2Fire | Canadian FBP + cell spread | behavior/CA separation and independent output comparison |
| Pyretechnics | surface Rothermel + crown components | crown-model decomposition and independent checks |
| SimFire | Rothermel-centered Python simulator | API/manager organization reference |
| GridFire | raster fire-behavior workflow | raster integration/experiment reference |
| C2FK | KITRAL + Cell2Fire | candidate-model audit only |

These projects are **references, not runtime dependencies**.

## 9. KITRAL and other future models

KITRAL is a genuine candidate independent empirical behavior system, especially
for Chilean vegetation. It is not a small interchangeable formula. A complete
implementation requires a pinned primary-source specification for at least:

```text
fuel classes and coefficients
surface ROS
wind response
slope response
temperature / humidity or moisture terms
length-to-breadth behavior
surface intensity / flame geometry
crown transition
active crown behavior
calibration domain
```

PyFireCA will not implement a partial `KITRALModel` merely to increase the model
count. The same self-contained implementation and validation rules used for FBP
apply.

Scott & Burgan 40 remains a different category: it expands the Rothermel fuel
catalogue and is **not** a separate fire-behavior equation system.

## 10. Extension rule

A future behavior model should normally add model-specific modules such as:

```text
behavior/<model>.py
behavior/<model>_directional.py
behavior/<model>_layers.py
behavior/<model>_spatial.py
behavior/<model>_landscape.py
```

Only create modules that the model actually needs. The arrival solver, GIS
output writer, ignition representation, and run-result object should remain
unchanged unless the new model introduces a scientifically necessary new
contract.
