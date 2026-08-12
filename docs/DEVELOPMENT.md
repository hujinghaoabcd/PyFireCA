# PyFireCA Development Guide

## 1. Development objective

The development process must preserve two priorities at the same time:

1. PyFireCA should remain small enough that the CA algorithms are easy to inspect and modify.
2. PyFireCA should meet modern research-software expectations for reproducibility, validation, documentation, testing, and release discipline.

The project should not accumulate infrastructure faster than scientific requirements justify it.

## 2. Development documents

The following files are living development artifacts:

- `docs/DESIGN.md` — architecture and design decisions;
- `docs/DEVELOPMENT.md` — development workflow and roadmap;
- `docs/STATUS.md` — current implementation status;
- `docs/HANDOFF.md` — detailed continuation guide;
- `docs/VALIDATION.md` — scientific validation plan.

Rules:

- architecture changes update `DESIGN.md` before or with code;
- completed work updates `STATUS.md`;
- every development session leaves `HANDOFF.md` accurate enough for a new session to continue without reconstructing context;
- scientific claims require a corresponding validation item.

## 3. Branch and change policy

For normal development:

```text
main
 └── focused feature/fix branch
      └── tests + docs
```

Keep commits scoped. Avoid mixing a scientific-model change with unrelated formatting or repository cleanup when possible.

Before a feature is considered complete:

```bash
ruff check .
ruff format --check .
pytest
```

When pre-commit is installed:

```bash
pre-commit run --all-files
```

## 4. Initial milestones

### Milestone A — repository foundation

Goal: establish the scientific-software skeleton before implementing wildfire equations.

- [x] repository created;
- [x] English/Chinese landing README initialized;
- [x] `pyproject.toml` initialized;
- [x] detailed design document initialized;
- [x] state model;
- [x] raster grid model;
- [x] neighborhood interface;
- [x] minimal tests;
- [x] CI;
- [x] pre-commit;
- [x] status/handoff/validation documents;
- [ ] RepoForge managed-header migration.

The RepoForge item is intentionally deferred rather than approximated by hand. The current README already contains project-specific scientific prose. When RepoForge is applied, initialize it as `scientific-python / standard`, review the generated diff, and migrate only the stable managed header regions so the hand-written README body remains user-owned.

Recommended reviewed workflow:

```bash
repoforge init . \
  --type scientific-python \
  --profile standard \
  --name PyFireCA \
  --repository-url https://github.com/hujinghaoabcd/PyFireCA

repoforge diff . --config repoforge.yml
repoforge apply . --config repoforge.yml --dry-run
```

Because the repository already has an unmarked README, do not use `--force` until the migration diff has been reviewed carefully.

### Milestone B — minimal CA reference core

Goal: run a small CA without wildfire-specific fire-behavior equations.

- [x] `FireState` enum and state validation;
- [x] `RasterGrid` shape/state contract;
- [x] Moore neighborhood;
- [x] Von Neumann neighborhood;
- [x] boundary-safe neighbor indexing;
- [x] abstract/minimal transition-rule contract;
- [x] synchronous simulation step;
- [x] explicit `numpy.random.Generator`;
- [x] deterministic regression/reference fixtures;
- [x] minimal runnable example.

Exit criterion: **met for the architectural reference core.** A small raster CA executes reproducibly, neighborhood substitution is tested, and synchronous no-cascade semantics are explicit. This milestone does not claim physically realistic wildfire behavior.

### Milestone C — wildfire data and behavior boundary

**Current implementation target.** Establish common data and behavior contracts before adding complete spread equations.

- [ ] define SI-unit policy and document any source-model conversion boundaries;
- [ ] common `FireBehaviorResult` type;
- [ ] behavior base protocol;
- [ ] minimal environmental input contract;
- [ ] static landscape layers;
- [ ] dynamic environmental layers;
- [ ] initial fuel representation;
- [ ] reference tests for behavior contracts;
- [ ] GIS alignment validation;
- [ ] optional Rasterio I/O.

The common behavior interface must be designed before implementing Rothermel or FBP so both can feed CA transition rules without model-name branches in `Simulation`.

### Milestone D — first behavior-informed wildfire CA rule

Goal: implement one transparent spread rule that consumes the common fire-behavior output.

- [ ] ignition representation beyond the architectural baseline;
- [ ] active burning cells / propagation state;
- [ ] CA rule consuming behavior output;
- [ ] arrival-time output;
- [ ] short integration example;
- [ ] regression case;
- [ ] scientific validation case.

The existing `NeighborIgnitionRule` is an architectural baseline, not the scientific rule targeted by this milestone.

### Milestone E — Cell2Fire-like distance rule

Goal: reproduce the important CA propagation concept in a modular form.

- [ ] formalize distance accumulation semantics;
- [ ] decide neighborhood geometry and directional distances;
- [ ] connect FBP-style behavior interface;
- [ ] compare with controlled Cell2Fire scenarios;
- [ ] characterize time-step / grid effects;
- [ ] document differences rather than claiming exact equivalence prematurely.

### Milestone F — Rothermel / FBP and richer wildfire processes

The exact order of Rothermel and FBP implementation should follow the validation/reference material available when Milestone C is complete.

- [ ] validated surface-fire behavior implementation;
- [ ] second interchangeable fire-behavior implementation;
- [ ] moisture inputs;
- [ ] optional crown-fire extension after surface validation;
- [ ] spotting design after core spread is stable;
- [ ] suppression/firebreak design after propagation invariants are stable.

### Milestone G — Monte Carlo and experiment layer

- [ ] explicit independent RNG stream strategy;
- [ ] scenario/run configuration;
- [ ] batch/ensemble execution without coupling to the CA kernel;
- [ ] metrics aggregation;
- [ ] reproducibility metadata;
- [ ] controlled sensitivity experiments.

### Milestone H — performance

Only after profiling representative simulations:

- [ ] benchmark representative grid sizes and active-cell fractions;
- [ ] identify Python/NumPy hotspots;
- [ ] introduce Numba selectively;
- [ ] verify optimized/reference equivalence;
- [ ] record performance methodology and hardware metadata.

## 5. Code-style rules

### Keep numerical kernels simple

Prefer functions that operate on arrays and explicit parameters. Avoid hiding numerical behavior behind deep object graphs.

### Avoid magic values

Use enums/constants/dataclasses for state codes and structured parameters.

### Avoid global state

No global RNG, mutable singleton configuration, or hidden process-wide simulation state.

### Avoid file I/O inside algorithms

Numerical kernels receive arrays or domain objects. GIS paths are resolved before entering the kernel.

### Fail explicitly

Invalid grids, impossible states, incompatible shapes, and unsupported configurations should raise informative exceptions.

### Type public interfaces

Public functions/classes must use type hints. Array shape/unit expectations belong in docstrings.

## 6. Dependency policy

Core dependencies should remain minimal.

Initial core:

```text
numpy
```

Optional groups may include:

```text
gis: rasterio
dev: pytest, pytest-cov, ruff, pre-commit
```

Do not add a dependency because a reference project uses it. Every dependency must solve a concrete PyFireCA requirement.

Prefer optional dependencies for GIS/documentation/benchmark tooling when the CA core does not require them at import time.

## 7. Scientific implementation workflow

For each scientific component:

```text
1. identify source/reference equations
2. document assumptions and units
3. define input/output contract
4. implement a readable reference version
5. add unit/reference tests
6. add integration test
7. compare with independent/reference implementation where possible
8. only then optimize
```

A fast implementation without an independently checkable reference path is not considered complete.

## 8. CA research workflow

When adding a new CA idea, isolate which dimension changes:

```text
State?
Neighborhood?
Transition rule?
Scheduler/time stepping?
Environmental coupling?
```

Do not label a whole model as new when the actual methodological change can be represented as one component. This keeps ablation and comparison experiments clean.

A research comparison should preferably reuse the same grid, input data, behavior model, metrics, and experiment runner while replacing only the CA component under study.

## 9. Documentation policy

README is a landing page. Detailed derivations, design rationale, experiments, validation tables, and developer instructions belong in `docs/`.

Every public feature should eventually have:

- one-line README discoverability when important;
- conceptual documentation;
- API docstring;
- runnable example when user-facing;
- tests;
- validation evidence when scientifically meaningful.

Development-stage documents are not release-history dumps. `STATUS.md` describes current truth; `HANDOFF.md` explains how to continue; `CHANGELOG.md` records externally meaningful changes.

## 10. Release policy

Pre-1.0 releases may change APIs, but changes should still be recorded in `CHANGELOG.md` and architecture decisions documented.

Suggested progression:

```text
0.1.x  reference CA core + common behavior/data contracts
0.2.x  validated fire behavior + GIS workflow
0.3.x  Cell2Fire-like reproduction/comparison
0.4.x  richer processes + Monte Carlo
0.5.x  profiling-led performance work
```

The roadmap is descriptive, not a promise; scientific validation gates are more important than version numbering.
