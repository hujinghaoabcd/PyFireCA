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
- [ ] state model;
- [ ] raster grid model;
- [ ] neighborhood interface;
- [ ] minimal tests;
- [ ] CI;
- [ ] pre-commit;
- [ ] status/handoff/validation documents;
- [ ] RepoForge configuration;

### Milestone B — minimal CA reference core

Goal: run a small CA without wildfire-specific fire-behavior equations.

- [ ] `FireState` enum and state validation;
- [ ] `RasterGrid` shape/state contract;
- [ ] Moore neighborhood;
- [ ] Von Neumann neighborhood;
- [ ] boundary-safe neighbor indexing;
- [ ] abstract/minimal transition-rule contract;
- [ ] synchronous simulation step;
- [ ] explicit `numpy.random.Generator`;
- [ ] deterministic regression fixture;
- [ ] minimal example.

Exit criterion: a small raster CA can execute reproducibly and all behavior is covered by tests.

### Milestone C — wildfire data and behavior boundary

Goal: establish data contracts before complete fire spread.

- [ ] static landscape layers;
- [ ] dynamic environmental layers;
- [ ] common fire-behavior result type;
- [ ] behavior base protocol/ABC;
- [ ] initial fuel representation;
- [ ] GIS alignment validation;
- [ ] optional Rasterio I/O;
- [ ] reference calculations for behavior modules.

### Milestone D — first wildfire CA rule

Goal: implement one transparent spread rule that exercises the architecture.

- [ ] ignition representation;
- [ ] active burning cells / propagation state;
- [ ] CA rule consuming behavior output;
- [ ] arrival-time output;
- [ ] short integration example;
- [ ] regression case;
- [ ] scientific validation case.

The first rule should be simple enough to validate. Do not begin by reproducing every Cell2Fire feature.

### Milestone E — Cell2Fire-like distance rule

Goal: reproduce the important CA propagation concept in a modular form.

- [ ] formalize distance accumulation semantics;
- [ ] decide neighborhood geometry and directional distances;
- [ ] connect FBP-style behavior interface;
- [ ] compare with controlled Cell2Fire scenarios;
- [ ] characterize time-step / grid effects;
- [ ] document differences rather than claiming exact equivalence prematurely.

### Milestone F — Rothermel and richer wildfire processes

- [ ] Rothermel surface behavior;
- [ ] moisture inputs;
- [ ] optional crown-fire extension after surface validation;
- [ ] spotting design after core spread is stable;
- [ ] suppression/firebreak design after propagation invariants are stable.

### Milestone G — performance

Only after profiling:

- [ ] benchmark representative grid sizes;
- [ ] identify Python/NumPy hotspots;
- [ ] introduce Numba selectively;
- [ ] verify optimized/reference equivalence;
- [ ] record performance methodology.

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

## 7. Scientific implementation workflow

For each scientific component:

```text
1. identify source/reference equations
2. document assumptions and units
3. implement a readable reference version
4. add unit/reference tests
5. add integration test
6. compare with independent/reference implementation where possible
7. only then optimize
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

## 9. Documentation policy

README is a landing page. Detailed derivations, design rationale, experiments, validation tables, and developer instructions belong in `docs/`.

Every public feature should eventually have:

- one-line README discoverability when important;
- conceptual documentation;
- API docstring;
- runnable example when user-facing;
- tests;
- validation evidence when scientifically meaningful.

## 10. Release policy

Pre-1.0 releases may change APIs, but changes should still be recorded in `CHANGELOG.md` and architecture decisions documented.

Suggested progression:

```text
0.1.x  reference CA core + first wildfire rule
0.2.x  validated fire behavior + GIS workflow
0.3.x  Cell2Fire-like reproduction/comparison
0.4.x  richer processes + Monte Carlo
0.5.x  profiling-led performance work
```

The roadmap is descriptive, not a promise; scientific validation gates are more important than version numbering.
