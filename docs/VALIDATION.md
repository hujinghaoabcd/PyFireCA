# PyFireCA Validation Plan

## 1. Validation philosophy

PyFireCA is scientific simulation software. Passing unit tests is necessary but not sufficient: implementation correctness, numerical stability, model interpretation, and comparison with independent references must be distinguished.

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

No benchmark superiority claim should be made without a documented protocol and reproducible evidence.

## 2. Unit-level invariants

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

## 3. Integration tests

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

## 4. Regression tests

For selected small configurations, store expected arrays/metrics so unintended behavior changes are visible.

Every regression fixture records:

- grid size;
- initial state;
- environmental arrays;
- rule parameters;
- seed;
- number of steps;
- expected final state and/or arrival time.

Regression changes require an explicit scientific or API rationale, not a blind snapshot update.

## 5. Fire-behavior validation

Each fire-behavior implementation must be validated independently from the CA engine.

### Rothermel

Planned checks:

- reference fuel cases with known/independently computed ROS;
- zero-wind / zero-slope case;
- wind-only case;
- slope-only case;
- moisture limits and non-burnable conditions;
- units and conversion checks.

Reference sources must be recorded alongside tests/docs when implementation begins.

### FBP

Planned checks:

- selected canonical fuel-type cases;
- wind/slope/direction transformations;
- ROS and supported secondary outputs;
- comparison with authoritative/reference implementation where licensing and reproducibility allow.

## 6. CA-specific scientific diagnostics

Because CA behavior can be sensitive to lattice and update choices, PyFireCA should explicitly characterize:

### Grid sensitivity

Run equivalent scenarios at multiple cell sizes and compare:

- burned area;
- arrival time;
- perimeter shape;
- spread-axis lengths.

### Time-step sensitivity

Run equivalent scenarios under multiple update intervals where the rule permits it.

### Directional / lattice bias

Use homogeneous fuel and controlled wind to measure spread anisotropy introduced by the lattice/neighborhood.

Suggested diagnostics:

- radial spread error by angle;
- major/minor axis error;
- perimeter distance to an analytical/ellipse target when appropriate.

This is particularly important because neighborhood design is a planned CA research direction.

## 7. Reference-model comparisons

### Cell2Fire

Use controlled scenarios to compare the PyFireCA Cell2Fire-like rule against Cell2Fire behavior.

The goal is initially **characterized correspondence**, not an unsupported claim of exact reproduction.

Document differences in:

- fuel/fire-behavior implementation;
- neighborhood geometry;
- update timing;
- distance accumulation;
- random processes;
- edge/boundary treatment.

### SimFire / Pyretechnics

Use selected fire-behavior calculations or simplified spread scenarios as independent cross-checks where the underlying scientific formulation overlaps.

### ELMFIRE / ForeFire

May be used later as non-CA spread comparisons to understand perimeter/arrival-time differences. They are not unit-test or API references.

## 8. GIS validation

GIS adapter tests should verify:

- round-trip shape and dtype;
- CRS preservation;
- affine transform preservation;
- NoData behavior;
- intentional failure on incompatible aligned-input requirements.

Use tiny generated rasters in tests rather than committing large real datasets.

## 9. Performance validation

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

## 10. Reproducibility metadata

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

## 11. Validation gates

A scientific component is not considered complete until:

1. assumptions and units are documented;
2. unit tests pass;
3. at least one reference/independent validation case exists when applicable;
4. integration with the CA engine has a small reproducible example;
5. limitations are documented.

Optimization and large experiments come after these gates.
