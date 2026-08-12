# PyFireCA Validation Plan

> Updated: 2026-08-13

## 1. Validation philosophy

PyFireCA is scientific simulation software. Passing unit tests is necessary but not sufficient: software correctness, numerical consistency, scientific equation fidelity, GIS workflow correctness, package reproducibility, and whole-model behavior are different questions and must be checked separately.

Validation is organized into these layers:

```text
software correctness
    ↓
numerical consistency
    ↓
scientific reference checks
    ↓
GIS / file-workflow integration
    ↓
package / clean-install reproducibility
    ↓
future model-behavior comparison
```

No benchmark superiority or model-equivalence claim should be made without a documented protocol and reproducible evidence.

## 2. Evidence grades for scientific reference values

Every externally sourced numerical reference used by PyFireCA receives a provenance grade.

### Grade A — primary/authoritative worked value

Examples:

- USDA/USFS technical report or research paper;
- official worked example with enough inputs to reproduce the output;
- authoritative source explicitly documenting the same equation variant and units.

Grade A is preferred for deciding what an equation or correction means.

### Grade B — official operational software regression

A maintained implementation from the responsible scientific institution, with pinned revision and explicit expected output.

For the current surface-fire line, pinned USFS Fire Lab Behave regressions provide key Grade B checks.

Grade B is strong operational evidence but does not erase the need to document which Rothermel/Albini/Behave conventions are active.

### Grade C — independent implementation comparison

Independent implementations such as SimFire or Pyretechnics may be used where scientific assumptions overlap.

Grade C is useful for triangulation and discrepancy diagnosis, but does not alone define PyFireCA's scientific truth.

### Grade D — internal synthetic/analytical fixture

Hand-computable or deliberately simplified cases created by PyFireCA.

Examples:

- exact surface-area weighting fixtures;
- square-grid distance/bearing invariants;
- analytical homogeneous arrival/lattice-error relations.

Grade D isolates code/model logic but is not an external scientific validation by itself.

### Conflict rule

When sources disagree:

```text
identify equation variant + units + conventions
→ return to primary/authoritative source where possible
→ document selected interpretation
→ add pinned regression/reference test
```

Do not resolve disagreement by loosening tolerances or by majority vote among packages.

## 3. Unit-level invariants

### State

- state codes are unique;
- arrays reject unsupported codes when validation is requested;
- `UNBURNABLE` is a real model state, not file NoData.

### Neighborhood

For an interior cell:

- Moore radius 1 → 8 offsets;
- Von Neumann radius 1 → 4 offsets;
- center `(0, 0)` is never returned;
- offsets are unique;
- invalid radius fails explicitly.

Physical arrival additionally restricts accepted propagation edges to immediate-neighbor offsets so a long edge cannot silently jump an intermediate barrier.

### Grid / geometry

- state shape equals grid shape;
- invalid dimensionality fails;
- boundary indexing never returns invalid coordinates;
- north-up square-grid distance/bearing conventions are explicitly tested for the physical baseline.

## 4. Synchronous CA reference validation

The synchronous architecture path is protected independently from the physical arrival baseline.

Key invariant:

```text
State(t)
→ rule reads old state
→ compute full State(t+1)
→ replace once
```

A newly ignited cell cannot propagate again in the same step.

No physical `dt` is inferred from a synchronous step.

## 5. Rothermel fire-behavior validation

The selected operational reference line is:

> **Albini-adjusted Rothermel surface fire behavior.**

### 5.1 R1 — fuel-bed quantities

Protected by exact/hand-computable tests for:

```text
unit conversions
surface-area weights
characteristic SAV
bulk density
packing ratio
optimum packing ratio
```

### 5.2 R2 — base no-wind/no-slope spread

R2 is no longer an open implementation gate.

Pinned Grade B Behave regressions currently include:

```text
FM1
4.4262698923571939 chains/h
0.024733996158492002 m/s

FM2
2.3810521029916596 chains/h
0.013305319151517395 m/s
```

Tests protect both the formula-level chain and full public model assembly.

### 5.3 R3 — wind / slope / vector composition

Protected cases include:

```text
FM1, 30% slope, zero wind
20.817222076028628 chains/h

FM1, zero slope, 100 ft/min DirectMidflame wind
8.834274755440232 chains/h

FM1, 30% slope + perpendicular 100 ft/min wind
21.399596624626479 chains/h maximum ROS
```

Validated semantics include:

```text
meteorological wind-from
conversion to downwind push
aspect as downslope bearing
upslope conversion
non-collinear wind/slope vector composition
optional wind-speed limiting
```

### 5.4 R4 — public model assembly

`RothermelModel.compute(RothermelInputs)` is covered end to end.

Stable validated outputs emphasize:

```text
spread_rate_m_s
spread_direction_deg
```

Zero wind + zero slope returns `spread_direction_deg=None`.

Fireline intensity/flame length remain outside the validated baseline public simulator output.

### 5.5 R5 — dynamic herbaceous curing

Pinned GR1 case:

```text
model 101 / GR1
live herb moisture 60%
zero wind / zero slope
0.71419316836403091 chains/h
0.003990911424818205 m/s
```

Dynamic curing/load transfer is validated as part of the same Rothermel equation path.

## 6. Standard fuel catalogue validation

Current audited catalogue:

```text
Anderson FM1–FM13
Scott–Burgan GR1 (101)
```

Anderson values are pinned to:

```text
firelab/behave
commit 29888c7ad364aa18cfb340f4c25a8e395f24260f
src/behave/fuelModels.cpp
```

Tests verify:

- native record fields for FM1–FM13;
- pinned source commit;
- conversion to the SI `RothermelFuelModel` contract;
- positive zero-wind/zero-slope computation for every Anderson model under a valid test moisture set;
- unchanged FM1/FM2/GR1 Grade B regressions;
- explicit failure for unaudited fuel codes.

The remaining Scott–Burgan catalogue is future expansion, not a first-baseline validation blocker.

## 7. Directional surface spread validation

The current ignition-point radial spread path uses the Behave/Catchpole surface ellipse:

```text
L/W = 0.936 exp(0.1147 U) + 0.461 exp(-0.0692 U) - 0.397
e = sqrt((L/W)^2 - 1) / (L/W)
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

Pinned Grade B FM1 case:

```text
100 ft/min DirectMidflame wind
zero slope
90° from head
FromIgnitionPoint
5.2277130003983068 chains/h
0.02921246024622574 m/s
```

Tests also protect head/flank/back/diagonal directional rates.

No `head_ROS*cos(theta)` shortcut is accepted.

`FromPerimeter` rates are not substituted for ignition-point radial arrival propagation.

## 8. Physical arrival validation

Contract:

```text
travel_time = physical_edge_distance / direction_specific_ROS
```

`StaticArrivalTimeSolver` is tested for:

- finite explicit ignition seeds;
- Dijkstra-style earliest-arrival behavior;
- barriers/domain exclusion;
- immediate-neighbor physical edge restrictions;
- directional homogeneous spread;
- heterogeneous per-source-cell spread;
- multiple/delayed ignition events;
- arrival → physical-time `FireState` conversion.

The current heterogeneous baseline uses:

> **source-cell-controlled outgoing edge ROS.**

Alternative interface coupling is not silently accepted as equivalent; it belongs to future controlled research comparison.

## 9. Lattice/discretization diagnostics

PyFireCA has already developed internal analytical tools for studying raster-direction bias while keeping the validated behavior model fixed.

Current analytical relations include exact immediate square-lattice path lengths for:

```text
VN4    Manhattan distance
Moore8 octile distance
```

For the homogeneous ignition-point ellipse, a corresponding exact CA-minus-continuous arrival-error relation is available for controlled lattice studies.

These diagnostics are research infrastructure only. They do not currently alter the default simulator.

Future paper experiments may compare:

```text
VN4 vs Moore8
cell-size sensitivity
extended neighborhoods
directional error by angle
arrival-time error
perimeter/shape error
interface-coupling variants
```

Implementation of new CA methods remains deferred until baseline release freeze.

## 10. GIS validation

GIS tests use tiny generated rasters rather than committed large datasets.

Protected checks include:

```text
shape/dtype round trip
CRS preservation
full affine-transform preservation
NoData preservation/semantics
alignment failure on incompatible rasters
state-raster canonical dtype/NoData behavior
```

The physical landscape baseline also validates:

```text
north-up geometry
square pixels
explicit metric cell_size_m consistency
```

Rotated/sheared/non-square or mismatched grids fail closed.

## 11. File-workflow integration validation

A real temporary-raster integration path tests:

```text
10 generated GeoTIFFs
→ StaticRunConfig
→ validate_static_run
→ run_static_config
→ complete run directory
→ read result rasters back
```

The test verifies:

```text
resolved configuration
input SHA-256
fuel provenance
metrics
log
arrival output
state output
burned-mask output
perimeter GeoJSON
```

## 12. CLI integration validation

The GIS CI job creates a real YAML + GeoTIFF fixture and runs:

```text
pyfireca validate semantics through cli.main
pyfireca run semantics through cli.main
```

It verifies the complete output directory exists and the CLI reports the expected run summary.

The console-script packaging entry point is separately exercised after clean wheel installation.

## 13. Output validation

### Arrival raster

```text
float64
seconds
-1 file NoData for no finite arrival
```

### Terminal state raster

```text
uint8
0 UNBURNABLE
1 in-domain unreachable UNBURNED
3 BURNED
file NoData None
```

### Burned mask

```text
uint8 0/1
```

### Perimeter

The final raster footprint is polygonized and transformed from the input CRS to EPSG:4326 before GeoJSON serialization.

Tests verify the resulting coordinates are geographic for a projected test raster.

## 14. Reproducibility metadata validation

File-based runs now record, rather than merely planning to record:

```text
resolved configuration
PyFireCA version
Python version
platform
Git commit when available from execution environment
raster geometry
ignition events
input SHA-256
fuel catalogue source revision
runtime metrics
```

The run workflow reuses the already loaded landscape for metadata rather than re-reading all ten inputs solely for reporting.

## 15. Package/release validation

CI now includes a dedicated `package` job.

It requires:

```text
wheel build
sdist build
clean wheel installation
pyfireca --help from built wheel
import pyfireca from built wheel
clean built-wheel [gis] installation
import rasterio after [gis] installation
```

This protects against packaging errors that editable source-tree tests cannot see.

The first baseline tag additionally requires `docs/RELEASE_CHECKLIST.md` to be satisfied.

## 16. Performance validation

Performance remains separate from scientific correctness.

When acceleration is introduced, it must be benchmarked and numerically compared with the NumPy reference path.

Record at least:

```text
grid size
active-cell fraction/scenario
hardware
Python/NumPy/accelerator versions
runtime methodology
memory methodology if reported
```

No Numba/GPU optimization is required for the first static baseline.

## 17. Future reference-model comparisons

### Cell2Fire

Future Cell2Fire-like comparisons should document differences in:

```text
fuel behavior
neighborhood geometry
time/update semantics
distance accumulation
random processes
barrier/boundary treatment
```

The target is characterized correspondence, not unsupported exact equivalence.

### SimFire / Pyretechnics

Useful as Grade C behavior/spread cross-checks when assumptions match.

### ELMFIRE / ForeFire

May later be used as non-CA perimeter/arrival comparisons, not as unit/API truth.

## 18. Validation gates

A scientific component is complete only when:

1. assumptions and units are documented;
2. formula/unit tests pass;
3. reference provenance/evidence grade is recorded;
4. external or independently checkable evidence exists where applicable;
5. integration has a reproducible small scenario;
6. limitations/discrepancies are documented;
7. CI protects the accepted behavior.

A release is complete only when scientific validation **and** GIS/package/reproducibility gates pass.
