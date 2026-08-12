# PyFireCA Development Guide

> Updated: 2026-08-13

## 1. Development objective

PyFireCA must preserve two priorities at the same time:

1. keep CA algorithms small and inspectable enough for methodological research;
2. meet modern research-software expectations for reproducibility, validation, GIS interoperability, testing, and release discipline.

Infrastructure must not grow faster than scientific requirements justify it.

The current short-term priority is fixed:

> **Finish and freeze the first simple static simulator baseline before implementing new PyFireCA-specific CA innovations.**

See `docs/SIMULATOR_ROADMAP.md` and `docs/FUTURE_RESEARCH.md`.

## 2. Living development documents

```text
docs/DESIGN.md                architecture and design decisions
docs/DEVELOPMENT.md           development/release workflow
docs/DEVELOPMENT_PRIORITY.md  current priority rule
docs/SIMULATOR_ROADMAP.md     simple-simulator completion plan
docs/STATUS.md                repository truth
docs/HANDOFF.md               exact continuation context
docs/SESSION_LOG.md           session-level implementation record
docs/VALIDATION.md            scientific/numerical evidence policy
docs/ROTHERMEL_REFERENCE.md   behavior implementation/validation truth
docs/RUNNING_SIMULATOR.md     user-facing simulator manual
docs/FUTURE_RESEARCH.md       deferred paper/method ideas
```

Rules:

- architecture/scientific interpretation changes update design docs before or with code;
- completed work updates `STATUS.md`;
- every substantial development session leaves `HANDOFF.md` current;
- externally meaningful behavior changes update `CHANGELOG.md`;
- scientific claims require validation evidence or an explicit limitation.

## 3. Change workflow

Preferred normal workflow:

```text
main
 └── focused feature/fix branch
      └── implementation + tests + affected docs
```

The repository bootstrap has included direct main commits while the project was being established. After the first baseline freeze, meaningful scientific changes should normally use focused branches/PRs.

Required checks:

```bash
ruff check .
ruff format --check .
pytest
pre-commit run --all-files
```

CI additionally tests Python 3.11/3.12/3.13 and the optional Rasterio/GIS workflow.

## 4. Current milestone map

### A — repository foundation

**Status: complete for baseline development.**

Implemented:

- `src/` layout + Hatchling;
- English/Chinese README;
- Ruff / pytest / coverage / pre-commit;
- GitHub Actions;
- citation/changelog/contributing/community files;
- continuous design/status/handoff/session documentation.

RepoForge managed-header migration remains optional and must not overwrite scientific README prose.

### B — minimal synchronous CA reference

**Status: complete.**

Implemented:

```text
FireState
RasterGrid
MooreNeighborhood
VonNeumannNeighborhood
TransitionRule
Simulation
NeighborIgnitionRule
explicit NumPy RNG
synchronous no-cascade regression
```

This remains an architecture/reference path, not the physically timed wildfire baseline.

### C — behavior, environmental data and GIS contracts

**Status: complete for the static baseline.**

Implemented:

```text
FireBehaviorModel / FireBehaviorResult
SpatialLayer / EnvironmentalData
LandscapeInput
RasterMetadata
strict raster alignment
explicit NoData/domain semantics
optional Rasterio read/write
canonical state raster output
```

Physical timestamp interpolation remains deferred until dynamic weather is designed.

### D — validated Rothermel reference

**Status: complete for the first static simulator baseline.**

Implemented and protected by pinned Behave/reference tests:

```text
R1 fuel-bed quantities
R2 Albini-adjusted no-wind/no-slope base spread
R3 wind / slope / vector composition
R4 public RothermelModel
R5 dynamic herbaceous curing
surface-fire ellipse / arbitrary-angle FromIgnitionPoint ROS
```

Public baseline behavior emphasizes validated spread rate/direction. Fireline intensity/flame length remain deferred until separately validated.

### E — standard fuel catalogue

**Status: sufficient for first baseline.**

Audited:

```text
Anderson FM1–FM13
Scott–Burgan GR1 (101)
```

Remaining Scott–Burgan models are future catalogue expansion and do not block the first static simulator release.

### F — physical static propagation

**Status: complete baseline.**

Implemented:

```text
physical edge distance/bearing
edge time = distance / direction-specific ROS
StaticArrivalTimeSolver
arrival_times_to_state
homogeneous directional provider
heterogeneous per-source-cell directional provider
```

Current baseline edge semantic is source-cell-controlled outgoing ROS.

Alternative interface coupling remains a research hypothesis, not a hidden default change.

### G — complete static simulator workflow

**Status: implemented end to end.**

User-facing path:

```text
version-1 YAML
→ ten aligned GeoTIFFs
→ strict validation
→ ignition events
→ static Rothermel arrival simulation
→ reproducible result directory
```

CLI:

```bash
pyfireca validate run.yml
pyfireca run run.yml
```

Run outputs:

```text
config.resolved.yml
metadata.json
environment.json
metrics.json
log.txt
outputs/arrival_time.tif
outputs/state.tif
outputs/burned_mask.tif
outputs/perimeter.geojson
```

### H — baseline freeze / release readiness

**Status: active.**

Remaining work:

- keep final commit fully green including Ruff format;
- build wheel + sdist in CI;
- clean-install built wheel and test console script;
- verify clean GIS-extra installation path;
- add release-readiness checklist;
- perform final package/docs audit;
- freeze/tag only after the checklist is satisfied.

### I — post-baseline science

**Status: intentionally deferred.**

After baseline freeze, resume controlled CA research such as:

```text
lattice/grid directional bias
extended/adaptive neighborhoods
named source/target interface coupling variants
cell-size sensitivity
arrival/perimeter error experiments
```

These ideas are recorded in `docs/FUTURE_RESEARCH.md`.

Do not mix them into the baseline CLI/config before freeze.

## 5. Code rules

### Keep numerical kernels explicit

Prefer small pure functions over deep mutable object graphs. Array shape, units, directional conventions, and physical assumptions belong in typed interfaces/docstrings.

### Avoid magic values

Use enums/dataclasses/constants for state codes and scientific parameters.

### Avoid global state

No global RNG, mutable singleton configuration, or hidden simulation state.

### Keep file I/O outside scientific kernels

Numerical behavior/propagation code receives arrays/domain objects. File paths are resolved by configuration/GIS/workflow adapters.

### Fail explicitly

Invalid states, shapes, units, domains, unsupported fuel codes, and unsupported grid geometry should raise informative exceptions rather than silently repair inputs.

### One implementation of the science

CLI/config/workflow layers must assemble the same validated simulator objects. Do not create a second scientific implementation inside the command-line path.

## 6. Dependency policy

Current base runtime dependencies:

```text
numpy
PyYAML
```

Optional:

```text
gis: rasterio
dev: pytest, pytest-cov, ruff, pre-commit
```

CLI uses standard-library `argparse`.

Do not add Pydantic, Typer, Click, xarray, Zarr, Numba, PyTorch, or JAX without a concrete requirement.

## 7. Scientific implementation workflow

For every scientific component:

```text
1. identify source equation/model
2. document assumptions / units / conventions
3. define input/output contract
4. prepare external/analytical fixtures
5. implement readable reference functions
6. add formula-level tests
7. add complete reference calculation
8. compare against pinned independent/official implementation where appropriate
9. diagnose disagreements
10. only then optimize/integrate
```

A fast implementation without independently checkable evidence is incomplete.

## 8. CA research workflow after baseline freeze

When adding a CA innovation, state exactly what changes:

```text
State?
Neighborhood?
Transition rule?
Scheduler/time stepping?
Environmental coupling?
Edge/interface coupling?
```

Controlled comparisons should reuse the same fuel/weather/grid/behavior/metrics setup and replace only the CA component under study.

This is important for interpretable ablation and publishable methodological attribution.

## 9. Release workflow

Before a baseline tag:

```text
quality tests green
Python matrix green
GIS integration green
wheel + sdist build green
built wheel clean-install green
console script smoke test green
docs/example commands verified
CHANGELOG current
STATUS/HANDOFF current
release-readiness checklist signed off
```

Do not tag a release merely because individual source-tree tests pass.

## 10. Post-baseline deferred work

Not blockers for the first static release:

```text
full Scott–Burgan 40 catalogue
affine-aware rotated/non-square geometry
time-varying weather scheduler
WRF / NetCDF / xarray
FBP
crown fire
spotting
suppression
Monte Carlo
fireline intensity/flame length public output
Numba optimization
GPU / Torch / JAX
new PyFireCA-specific CA methods
```
