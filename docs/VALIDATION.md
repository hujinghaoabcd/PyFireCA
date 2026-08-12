# PyFireCA Validation Plan

## 1. Validation philosophy

PyFireCA is scientific simulation software. Passing unit tests is necessary but not sufficient: software correctness, numerical consistency, scientific equation fidelity, and whole-model comparison are different questions and must be reported separately.

Validation is organized into four layers:

```text
software correctness
    ↓
numerical consistency
    ↓
scientific reference checks
    ↓
model-behavior comparison
```

No benchmark superiority or model-equivalence claim should be made without a documented protocol and reproducible evidence.

## 2. Evidence grades for scientific reference values

Every externally sourced numerical reference used by PyFireCA should be assigned an evidence grade. The grade describes **provenance**, not whether the number is large/small or whether PyFireCA agrees with it.

### Grade A — primary/authoritative worked value

Preferred scientific truth source:

- USDA/USFS primary technical report, research paper, handbook, or official worked example;
- published equations plus an official numerical example with enough inputs to reproduce the value;
- another authoritative source explicitly documenting the same equation variant and units.

Grade A is preferred for equation-level acceptance and for deciding between competing interpretations of the model.

### Grade B — official operational software regression

A maintained implementation from the responsible scientific institution, with pinned source revision and explicit expected output.

For Rothermel surface fire, the current Grade B reference is the USFS Fire Lab `firelab/behave-app` Behave 7 regression suite. PyFireCA pins the upstream commit/path used by any copied fixture so later upstream edits cannot silently change our expected values.

Grade B is strong operational evidence, but it does not replace Grade A when PyFireCA is deciding what an equation *means*. A software package may include implementation choices, corrections, limits, or ancillary models beyond one original paper.

### Grade C — independent implementation comparison

Independent/open implementations such as SimFire or Pyretechnics may be used to triangulate results when the scientific assumptions overlap.

Grade C is useful for detecting mistakes and implementation divergence. It is **not** used alone to define PyFireCA's scientific truth.

### Grade D — internal synthetic/analytical fixture

Hand-computable or deliberately simplified cases created by PyFireCA.

Examples include the current R1 synthetic fuel bed whose expected surface-area weights are exact fractions. Grade D is excellent for software/formula isolation but does not validate the full scientific model against an external authority.

### Conflict rule

When sources disagree:

```text
identify equation variant + units + conventions
        ↓
return to Grade A source where possible
        ↓
document the selected interpretation
        ↓
add a regression/reference test
```

Do not resolve disagreements by loosening tolerances or by majority vote among software packages.

## 3. Unit-level invariants

### State

- every state code is unique;
- state arrays reject unsupported codes when validation is requested;
- model-defined irreversible transitions are tested once rules exist.

### Neighborhood

For an interior cell:

- Moore radius 1 → 8 offsets;
- Von Neumann radius 1 → 4 offsets;
- center `(0, 0)` is never returned;
- offsets are unique;
- radius must be a positive integer;
- directional/radius variants later receive equivalent invariant checks.

### Grid

- state shape equals grid shape;
- invalid dimensionality fails explicitly;
- boundary indexing never returns invalid coordinates;
- geospatial metadata is preserved when supplied.

## 4. Integration tests

Short simulations should verify that components work together without relying on large real-world datasets.

Initial fixtures should include:

```text
3×3
5×5
10×10
```

Examples:

- one burning center cell with deterministic neighbor ignition;
- blocked/unburnable cells prevent propagation;
- fixed seed reproduces stochastic spread;
- stopping conditions terminate correctly.

## 5. Regression tests

For selected small configurations, store expected arrays/metrics so unintended behavior changes are visible.

Every regression fixture records:

- grid size;
- initial state;
- environmental arrays;
- rule parameters;
- seed;
- number of steps;
- expected final state and/or arrival time;
- fixture provenance when values come from an external reference.

Regression changes require an explicit scientific or API rationale, not a blind snapshot update.

## 6. Fire-behavior validation

Each fire-behavior implementation is validated independently from the CA engine.

### 6.1 Rothermel R1

Current R1 evidence includes:

- Grade D hand-computable heterogeneous-fuel surface-area weights;
- Grade D characteristic SAV, packing-ratio, and bulk-density checks;
- explicit SI ↔ legacy-unit round trips;
- formula-domain validation for nonburnable/invalid inputs.

R1 is a component-level baseline, not a complete spread-model validation.

### 6.2 Rothermel R2 — current gate

PyFireCA's selected reference variant is **Albini-adjusted Rothermel**.

Before accepting no-wind/no-slope ROS, require:

1. Grade A equation provenance for every selected correction/convention;
2. at least one Grade A worked/numeric fixture if an adequate one can be located;
3. otherwise clearly record the absence of a suitable Grade A worked value rather than manufacturing one;
4. Grade B comparison against pinned USFS Fire Lab Behave 7 where equivalent inputs can be constructed;
5. Grade C comparisons against SimFire/Pyretechnics only under matching assumptions.

Planned no-wind/no-slope checks:

- combustible/net fuel loading;
- mineral damping;
- moisture damping;
- live moisture of extinction;
- reaction velocity/intensity;
- propagating flux ratio;
- effective heating number;
- heat of preignition;
- heat sink;
- final base ROS.

### 6.3 Official Behave 7 regression snapshot

PyFireCA preserves a small upstream snapshot under:

```text
tests/validation/data/behave7_surface_reference.csv
```

Upstream provenance currently pinned in `tests/validation/README.md`:

```text
repository: firelab/behave-app
commit: a3cfcd5903188d73445948af16644868225bb9d5
source: behave-lib/test/csv/surface.csv
validator: behave-lib/test/cpp/testSurface.cpp
```

The upstream C++ test loads the CSV, runs the Surface module in the direction of maximum spread, retrieves spread rate in chains/hour, and checks it with `1e-6` tolerance. Therefore these rows are **Grade B operational regression values**.

The current upstream CSV contains wind/slope cases plus a nonburnable model-91 case; it is mainly useful for later R3/R4 whole-surface regression. It does **not** currently provide the dedicated zero-wind/zero-slope R2 fixture PyFireCA wants. That absence is recorded explicitly rather than treating a non-equivalent case as R2 evidence.

### 6.4 FBP

Planned checks:

- selected canonical fuel-type cases;
- wind/slope/direction transformations;
- ROS and supported secondary outputs;
- Grade A/B reference values where available;
- controlled comparison with Cell2Fire-compatible behavior assumptions.

## 7. CA-specific scientific diagnostics

Because CA behavior can be sensitive to lattice and update choices, PyFireCA explicitly characterizes these effects rather than attributing all error to fire behavior.

### Grid sensitivity

Run equivalent scenarios at multiple cell sizes and compare:

- burned area;
- arrival time;
- perimeter shape;
- spread-axis lengths.

### Time-step sensitivity

Run equivalent scenarios under multiple update intervals where the rule permits it.

### Directional / lattice bias

Use homogeneous fuel and controlled forcing to measure anisotropy introduced by the lattice/neighborhood.

Suggested diagnostics:

- radial spread error by angle;
- major/minor axis error;
- perimeter distance to an analytical/ellipse target when appropriate.

This is particularly important because neighborhood design is a planned CA research direction.

## 8. Reference-model comparisons

### Cell2Fire

Use controlled scenarios to compare the future PyFireCA Cell2Fire-like rule against Cell2Fire behavior.

The initial goal is **characterized correspondence**, not an unsupported claim of exact reproduction.

Document differences in:

- fuel/fire-behavior implementation;
- neighborhood geometry;
- update timing;
- distance accumulation;
- random processes;
- edge/boundary treatment.

### SimFire / Pyretechnics

Use selected fire-behavior calculations or simplified spread scenarios as Grade C cross-checks where the underlying scientific formulation overlaps.

### ELMFIRE / ForeFire

May be used later as non-CA spread comparisons to understand perimeter/arrival-time differences. They are not unit-test or API references.

## 9. GIS validation

GIS adapter tests should verify:

- round-trip shape and dtype;
- CRS preservation;
- affine transform preservation;
- NoData behavior;
- intentional failure on incompatible aligned-input requirements.

Use tiny generated rasters in tests rather than committing large real datasets.

## 10. Performance validation

Performance is measured separately under `benchmarks/`.

When Numba or another acceleration technique is introduced, it must pass numerical-equivalence tests against the NumPy reference path before performance results are considered meaningful.

Record:

- grid size;
- steps;
- active-cell fraction where relevant;
- hardware;
- Python/NumPy/Numba versions;
- runtime statistic methodology;
- memory measurement method if reported.

## 11. Reproducibility metadata

Future run outputs should record at least:

```text
PyFireCA version
Git commit
Python version
seed
configuration
input identity/hash where practical
runtime/backend information
```

Monte Carlo experiments must record the seed-generation strategy, not only a single top-level seed.

External validation fixtures additionally record upstream repository/document identifier, revision/version, source path/page/table when available, units, and evidence grade.

## 12. Validation gates

A scientific component is not considered complete until:

1. assumptions and units are documented;
2. unit/formula tests pass;
3. reference provenance and evidence grade are recorded;
4. at least one external reference/independent validation case exists when applicable;
5. integration with the CA engine has a small reproducible example when that layer is reached;
6. limitations and unresolved discrepancies are documented.

Optimization and large experiments come after these gates.
