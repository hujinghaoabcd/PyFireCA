# PyFireCA Development Guide

## 1. Development objective

PyFireCA must preserve two priorities at the same time:

1. keep CA algorithms small and inspectable enough for methodological research;
2. meet modern research-software expectations for reproducibility, validation, documentation, testing, and release discipline.

Infrastructure must not grow faster than scientific requirements justify it.

## 2. Living development documents

- `docs/DESIGN.md` — architecture and cross-cutting design decisions;
- `docs/DEVELOPMENT.md` — workflow and milestone roadmap;
- `docs/STATUS.md` — repository truth at the current commit;
- `docs/HANDOFF.md` — exact continuation context for the next session;
- `docs/VALIDATION.md` — scientific/numerical validation plan;
- `docs/BEHAVIOR_DATA_CONTRACT.md` — shared behavior/data conventions;
- `docs/ROTHERMEL_REFERENCE.md` — Rothermel implementation and validation plan.

Rules:

- architecture/scientific interpretation changes update design documentation before or with code;
- completed work updates `STATUS.md`;
- every substantial development session leaves `HANDOFF.md` current;
- scientific claims require a validation item or explicit limitation.

## 3. Change workflow

Preferred normal workflow:

```text
main
 └── focused feature/fix branch
      └── implementation + tests + affected docs
```

Current bootstrap work has been committed directly while establishing the repository. Once normal feature development begins, prefer focused branches/PRs for changes with meaningful scientific impact.

Required local checks:

```bash
ruff check .
ruff format --check .
pytest
pre-commit run --all-files
```

CI currently repeats quality checks and pytest on Python 3.11, 3.12, and 3.13.

## 4. Milestones

### Milestone A — repository foundation

**Status: complete except reviewed RepoForge migration.**

- [x] repository / `src/` package layout;
- [x] English and Chinese README;
- [x] `pyproject.toml` / Hatchling;
- [x] Ruff / pre-commit / pytest / coverage;
- [x] GitHub Actions CI;
- [x] citation / changelog / contribution files;
- [x] design / development / validation / status / handoff documents;
- [ ] RepoForge managed-header migration.

RepoForge remains deferred intentionally. The existing README contains project-specific scientific prose. When migrated, use `scientific-python / standard`, inspect the diff, and prefer managed header sections rather than whole-file ownership.

### Milestone B — minimal CA reference core

**Status: complete.**

- [x] `FireState` and state validation;
- [x] `RasterGrid`;
- [x] Moore neighborhood;
- [x] Von Neumann neighborhood;
- [x] clipped boundary-safe neighbor indexing;
- [x] synchronous `TransitionRule`;
- [x] `Simulation.step()` / `run()`;
- [x] explicit `numpy.random.Generator`;
- [x] deterministic `NeighborIgnitionRule` baseline;
- [x] regression test for synchronous no-cascade semantics;
- [x] runnable minimal example.

Exit criterion is met for the architectural reference core. This milestone does not claim physically realistic wildfire behavior.

### Milestone C — behavior and environmental data contracts

**Status: current; core contract largely complete.**

Common boundary:

- [x] SI-derived CA-facing behavior output policy;
- [x] `FireBehaviorResult`;
- [x] generic `FireBehaviorModel[InputT]`;
- [x] direction convention;
- [x] static `(Y, X)` `SpatialLayer`;
- [x] dynamic `(T, Y, X)` `SpatialLayer`;
- [x] `EnvironmentalData` spatial/time alignment;
- [x] explicit units/NoData metadata policy;
- [x] tests for behavior/data contracts.

First behavior-family contract:

- [x] select Rothermel as first reference implementation;
- [x] fixed six-class fuel ordering;
- [x] SI `RothermelFuelModel`;
- [x] `RothermelFuelMoisture`;
- [x] `RothermelInputs`;
- [x] midflame-wind and direction conventions;
- [x] contract tests;
- [x] detailed `ROTHERMEL_REFERENCE.md` plan.

Remaining contract/GIS work:

- [ ] CRS / affine-transform / extent alignment contract;
- [ ] optional Rasterio read/write adapter;
- [ ] explicit GIS NoData → unburnable/masked policy;
- [ ] physical timestamp / interpolation policy when a real weather integration begins.

The generic behavior result contract should not be redesigned merely to make one equation implementation convenient.

### Milestone D — validated Rothermel reference implementation

**Next scientific milestone.**

Implement in small independently testable stages:

#### R1 — units and base fuel quantities

- [ ] exact/native unit-conversion helpers needed by the published equation path;
- [ ] conversion tests;
- [ ] surface-area weighting / characteristic fuel quantities;
- [ ] bulk density / packing ratio / optimum packing ratio;
- [ ] formula-level tests.

#### R2 — no-wind / no-slope surface ROS

- [ ] moisture damping;
- [ ] mineral damping;
- [ ] reaction velocity/intensity;
- [ ] propagating flux ratio;
- [ ] effective heating / heat of preignition;
- [ ] base ROS;
- [ ] authoritative numeric fixture.

#### R3 — wind and slope

- [ ] wind factor;
- [ ] slope factor;
- [ ] explicit geographic/vector convention tests;
- [ ] documented wind-limit policy if/when applied.

#### R4 — PyFireCA output

- [ ] `RothermelModel.compute(RothermelInputs)`;
- [ ] SI `FireBehaviorResult`;
- [ ] independent comparison with authoritative values;
- [ ] comparison with SimFire/Pyretechnics where scientifically equivalent.

#### R5 — fuel catalogues

- [ ] independently verified Anderson 13 data;
- [ ] Scott--Burgan 40 only after conversion/provenance tests;
- [ ] dynamic herbaceous curing when scientifically validated.

Do not copy equations/source code from reference software. Implement from published scientific sources and use software implementations only for comparison.

### Milestone E — first behavior-informed CA rule

- [ ] define the minimal CA propagation state beyond the architectural baseline;
- [ ] consume `FireBehaviorResult` without behavior-model name branches;
- [ ] arrival-time representation;
- [ ] transparent short integration example;
- [ ] deterministic/reference regression case;
- [ ] scientific validation case.

This rule should be intentionally simple enough to diagnose CA effects separately from fire-behavior effects.

### Milestone F — FBP and Cell2Fire-like CA

- [ ] define typed FBP input/result adapter to the common behavior contract;
- [ ] validate FBP reference calculations;
- [ ] formalize Cell2Fire-like distance accumulation;
- [ ] define directional neighbor distances/geometry;
- [ ] connect FBP output to the distance rule;
- [ ] controlled comparison with Cell2Fire scenarios;
- [ ] grid/time-step sensitivity;
- [ ] lattice/directional-bias diagnostics;
- [ ] document differences instead of claiming exact equivalence prematurely.

### Milestone G — richer wildfire processes and experiments

- [ ] Monte Carlo RNG stream strategy;
- [ ] scenario/run configuration;
- [ ] batch/ensemble execution outside the CA kernel;
- [ ] reproducibility metadata;
- [ ] metrics aggregation;
- [ ] moisture extensions;
- [ ] crown fire only after surface behavior validation;
- [ ] spotting only after core spread invariants are stable;
- [ ] suppression/firebreaks only after propagation semantics are stable.

### Milestone H — performance

Only after representative profiling:

- [ ] benchmark grid sizes / active-cell fractions;
- [ ] identify measured hotspots;
- [ ] add Numba selectively;
- [ ] retain NumPy reference path;
- [ ] verify optimized/reference equivalence;
- [ ] record hardware/software benchmark metadata.

## 5. Code rules

### Keep numerical kernels explicit

Prefer small pure functions over deep mutable object graphs. Array shape and units belong in typed interfaces/docstrings.

### Avoid magic values

Use enums/dataclasses/constants for state codes and scientific parameters.

### Avoid global state

No global RNG, mutable singleton configuration, or hidden simulation state.

### Keep file I/O outside algorithms

Numerical kernels receive arrays/domain objects. GIS paths are resolved by adapters/preprocessing code.

### Fail explicitly

Invalid states, shapes, physical domains, units/conventions, and unsupported configurations should raise informative exceptions rather than silently clamp/repair unless the scientific model explicitly specifies a limit.

## 6. Dependency policy

Core dependency remains deliberately small:

```text
numpy
```

Optional groups may provide:

```text
gis: rasterio
dev: pytest, pytest-cov, ruff, pre-commit
```

Do not add xarray, Zarr, Pydantic, Numba, or another package until a concrete requirement exists.

## 7. Scientific implementation workflow

For every scientific component:

```text
1. identify primary source equations
2. document assumptions / units / conventions
3. define input and output contracts
4. prepare reference fixtures where possible
5. implement readable reference functions
6. add formula-level tests
7. add complete reference calculation
8. compare with an independent implementation
9. diagnose disagreements
10. only then optimize/integrate
```

A fast implementation without an independently checkable reference path is incomplete.

## 8. CA research workflow

When adding a CA innovation, state exactly what changes:

```text
State?
Neighborhood?
Transition rule?
Scheduler/time stepping?
Environmental coupling?
```

Comparisons should reuse the same grid/data/fire-behavior/metrics/experiment setup wherever possible and replace only the CA component being studied. This makes ablation and methodological attribution much cleaner.

## 9. Documentation policy

README is the landing page, not the manual. Derivations, scientific assumptions, validation tables, architecture rationale, and continuation notes live under `docs/`.

`STATUS.md` = current truth.

`HANDOFF.md` = how to continue.

`CHANGELOG.md` = externally meaningful changes.

`VALIDATION.md` = what evidence is required before scientific claims are accepted.

## 10. Release direction

Suggested pre-1.0 progression:

```text
0.1.x  CA core + behavior/data contracts + Rothermel reference
0.2.x  GIS workflow + first behavior-informed CA
0.3.x  FBP + Cell2Fire-like comparison
0.4.x  richer processes + Monte Carlo
0.5.x  profiling-led performance work
```

The sequence is descriptive, not a delivery promise. Scientific validation gates take priority over version numbering.
