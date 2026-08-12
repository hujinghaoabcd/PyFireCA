# PyFireCA Development Session Log

## 2026-08-12 — Foundation, Rothermel R1, validation provenance, and GIS contract

### Session objective

Move PyFireCA from an empty repository to a modern, tested wildfire-CA research codebase while preserving a compact architecture and detailed development handoff.

The session intentionally avoided implementing a large monolithic wildfire model. Work was staged so CA mechanics, fire behavior, validation evidence, and GIS concerns remain independently testable.

---

## 1. CA reference core established

Implemented:

```text
FireState
RasterGrid
Neighborhood protocol
MooreNeighborhood
VonNeumannNeighborhood
TransitionRule
Simulation
NeighborIgnitionRule
```

Reference update semantics are explicitly synchronous:

```text
State(t)
   ↓
rule reads complete old state
   ↓
compute State(t+1)
   ↓
Simulation replaces state once
```

A regression test verifies that a newly ignited cell cannot propagate again in the same step.

The deterministic `NeighborIgnitionRule` remains an architectural baseline only; it is not claimed to represent realistic wildfire physics.

---

## 2. Common behavior/data contracts established

Implemented:

```text
FireBehaviorModel[InputT]
FireBehaviorResult
SpatialLayer
EnvironmentalData
```

`FireBehaviorResult` standardizes the CA-facing behavior boundary while model-native inputs remain separate.

Common result convention:

```text
spread_rate_m_s            required
spread_direction_deg       optional, clockwise from geographic north
fireline_intensity_w_m     optional
flame_length_m              optional
diagnostics                 optional
```

Environmental arrays use:

```text
static   (Y, X)
dynamic  (T, Y, X)
```

No hidden datetime interpolation, masking, or unit conversion was introduced.

---

## 3. Rothermel public input contract established

Implemented:

```text
FuelClass
RothermelFuelModel
RothermelFuelMoisture
RothermelInputs
```

Fixed six-class ordering:

```text
DEAD_1H
DEAD_10H
DEAD_100H
DEAD_HERBACEOUS
LIVE_HERBACEOUS
LIVE_WOODY
```

Public Rothermel inputs use SI units. Wind supplied to the model is explicitly midflame wind; 10-m / 20-ft wind adjustment is a separate preprocessing concern.

---

## 4. Rothermel R1 implemented and validated

Added explicit conversion helpers for:

```text
m ↔ ft
kg/m² ↔ lb/ft²
kg/m³ ↔ lb/ft³
1/m ↔ 1/ft
J/kg ↔ Btu/lb
m/s ↔ ft/min
```

Implemented R1 pure functions:

```text
compute_surface_area_weights
compute_characteristic_sav_m_inv
compute_packing_ratio
compute_bulk_density_kg_m3
compute_optimum_packing_ratio
```

The heterogeneous-fuel weighting tests use hand-computable synthetic inputs rather than taking another package as truth.

The R1 baseline was confirmed green across:

```text
Ruff lint
Ruff format
quality pytest
Python 3.11
Python 3.12
Python 3.13
```

---

## 5. R2 scientific variant audited before implementation

Primary-source review separated the original Rothermel 1972 formulation from later operational corrections.

PyFireCA now explicitly targets:

> **Albini-adjusted Rothermel surface fire**

Documented Albini 1976 adjustments include:

1. combustible-loading correction;
2. revised reaction-velocity exponent;
3. revised live moisture-of-extinction calculation;
4. revised combination of dead/live reaction intensities.

Andrews 2018 is used as the modern consolidated consistency reference.

No R2 equation chain was implemented before this variant decision was made.

---

## 6. Validation evidence hierarchy introduced

`docs/VALIDATION.md` now distinguishes:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent implementation comparison
Grade D  internal analytical/synthetic fixture
```

External values now require provenance instead of appearing as unexplained constants.

### Grade A snapshot

Added Albini 1976 worked examples:

```text
tests/validation/data/albini1976_worked_examples.csv
```

These provide future wind/slope whole-model checks but are not zero-wind/zero-slope R2 fixtures.

### Grade B snapshot

Pinned official USFS Fire Lab Behave 7 surface regression data:

```text
repository: firelab/behave-app
commit: a3cfcd5903188d73445948af16644868225bb9d5
source: behave-lib/test/csv/surface.csv
```

The snapshot is stored under:

```text
tests/validation/data/behave7_surface_reference.csv
```

Both external snapshots have SHA-based integrity tests.

### Remaining R2 validation gap

No precise external worked value with **both zero wind and zero slope** matching the selected Albini-adjusted R2 line has yet been locked.

Do not fabricate a Grade A value from PyFireCA's own equations.

Acceptable fallback if no primary worked value is found:

```text
pinned official Behave 7 build
        ↓
generate zero-wind/zero-slope case
        ↓
record as Grade B, not Grade A
```

---

## 7. GIS raster contract implemented

Added:

```text
src/pyfireca/gis.py
tests/test_gis.py
docs/GIS_DATA_CONTRACT.md
```

Core GIS objects/functions:

```text
RasterMetadata
RasterAlignmentError
validate_raster_alignment
validate_named_raster_alignment
```

Current geometric alignment contract:

```text
same shape
+
same canonical CRS
+
same full affine transform within explicit tolerance
```

The alignment layer never silently reprojects, resamples, shifts, or crops data.

NoData equality is optional because NoData representation and simulation semantics are separate questions.

`docs/DESIGN.md` was updated with design decisions D009/D010 covering GIS alignment and validation provenance.

---

## 8. Optional Rasterio adapter implemented

`gis.py` now also exposes optional adapter functions:

```text
read_raster(path, band=1)
write_raster(path, values, metadata)
```

Rasterio is imported lazily. Base `import pyfireca` therefore does not require the GIS extra.

Current adapter behavior:

- one raster band per call;
- raw stored values are read;
- CRS is required;
- shape/CRS/affine/NoData metadata are returned explicitly;
- writing uses one GeoTIFF band;
- dtype, CRS, affine transform, and NoData are preserved;
- no automatic parent-directory creation;
- no reprojection/resampling/masking/imputation.

Added:

```text
tests/test_rasterio_io.py
```

The dedicated GIS CI job installs:

```text
.[dev,gis]
```

and runs GIS contract + Rasterio round-trip tests.

The GIS job successfully passed its adapter tests during this session.

---

## 9. CI observations and fixes

CI was used continuously instead of treating engineering checks as final cleanup.

Issues caught during development were engineering-format issues rather than scientific-test failures, including:

- long line in `grid.py`;
- Ruff formatting of a regression array;
- modern `collections.abc.Mapping` import;
- formatter layout in `gis.py`;
- formatting of selected tests.

These were corrected without changing scientific semantics.

At the end of this log, the Rasterio-specific GIS job has passed. A final full workflow was re-triggered after the latest Ruff-format correction in `gis.py`; the first action in the next session should be to inspect the newest CI run and record its final conclusion in `STATUS.md` / `HANDOFF.md`.

---

## 10. Exact next work

### First action

Inspect the newest GitHub Actions run.

If a failure remains, determine whether it is:

```text
format/style
software test
scientific/reference test
GIS optional-dependency test
```

Do not change scientific equations to address an engineering-only failure.

### Scientific line

Continue R2 only after the fixture gate:

```text
external zero-wind + zero-slope reference
        ↓
Albini-adjusted formula-level functions
        ↓
validated no-wind/no-slope ROS
```

Do not jump directly to wind/slope or Cell2Fire distance accumulation.

### GIS line

After CI is green, synchronize the long-lived docs with the newly implemented adapter:

```text
docs/GIS_DATA_CONTRACT.md
  - mark Rasterio adapter implemented

docs/DEVELOPMENT.md
  - mark core GIS alignment + optional adapter complete

docs/STATUS.md
  - add GIS contract / adapter truth

docs/HANDOFF.md
  - add GIS API + CI state
CHANGELOG.md
  - record GIS metadata/alignment/Rasterio adapter
```

Then decide the next GIS semantic issue separately:

```text
NoData → UNBURNABLE / masked / error / weather missing policy
```

Do not silently choose one global NoData meaning for every input layer.

---

## 11. Files that should be read first next session

In order:

```text
1. docs/SESSION_LOG.md
2. docs/STATUS.md
3. docs/HANDOFF.md
4. docs/ROTHERMEL_REFERENCE.md
5. docs/VALIDATION.md
6. docs/GIS_DATA_CONTRACT.md
7. src/pyfireca/behavior/rothermel.py
8. src/pyfireca/gis.py
```

This should be enough to continue without reconstructing development decisions from chat history.
