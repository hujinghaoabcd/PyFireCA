# PyFireCA Development Handoff

> Updated: 2026-08-12
>
> Purpose: allow the next development session or contributor to continue immediately without reconstructing design context from chat history.

## 1. Project identity

Repository: `hujinghaoabcd/PyFireCA`

PyFireCA is a **wildfire cellular-automata research framework**. It is not intended to become a generic urban CA platform. Urban CA projects are engineering references only: they inform GIS data organization, raster contracts, experiment structure, and software engineering.

Primary research interest: **modify and study the CA itself**.

Protected CA extension points:

```text
State
Neighborhood
Transition Rule
Time stepping / scheduler
```

Fire behavior and GIS are supporting layers, not the definition of the CA engine.

## 2. Scope decisions already made

Do not casually reverse these decisions without updating `docs/DESIGN.md` and explaining the scientific reason.

1. PyFireCA is wildfire-specific.
2. UrbanVCA / PLUS / intPLUS / Mesa-Geo do not become supported urban-model modules.
3. PyTorchFire-style differentiable CA is deferred.
4. Level Set and front tracking remain comparison methods, not core propagation engines.
5. NumPy is the readable scientific reference implementation.
6. Numba is introduced only after profiling.
7. Fire behavior and CA propagation remain separate.
8. GIS file I/O remains outside numerical kernels.
9. The package tree stays compact until code size/extension pressure justifies splitting files into subpackages.
10. Development design/status/handoff/validation documents are maintained continuously.

## 3. Reference-project lessons already accepted

### Cell2Fire

Main wildfire-CA reference for:

- cell-based landscape propagation;
- ROS-driven cell-to-cell spread;
- distance/ellipse concepts;
- Monte Carlo landscape experiments.

Do not copy its implementation architecture wholesale.

### SimFire

Use for:

- Python simulation-manager ideas;
- Rothermel-oriented wildfire workflow;
- mitigation/suppression concepts;
- environment/simulation separation.

Avoid coupling rendering/game concerns to the numerical kernel.

### GridFire

Use for:

- raster fire-model organization;
- Monte Carlo/scenario ideas;
- richer wildfire system concerns;
- later performance comparisons.

### Pyretechnics

Use mainly for:

- modular fire-behavior equations;
- surface/crown/spot separation;
- static + dynamic environmental data organization;
- reference-calculation ideas.

Do **not** adopt its Level Set propagation as PyFireCA's core.

### ELMFIRE / ForeFire

Keep as non-CA comparison baselines only.

### UrbanVCA / PLUS / intPLUS

Engineering references only:

- preprocessing pipeline separation;
- GIS raster compatibility requirements;
- driving/environmental layer organization;
- simulation vs assessment separation.

UrbanVCA's flat research-script layout should not be copied.

### Mesa-Geo

Use as a modern Python/GIS engineering reference for:

- package hygiene;
- CI / pre-commit / coverage;
- documentation and contribution standards;
- GIS-aware design.

Do not force agent-based abstractions into a raster CA where arrays are more appropriate.

## 4. Current implemented source tree

```text
src/pyfireca/
├── __init__.py
├── state.py
├── grid.py
├── neighborhood.py
├── rules.py
└── simulation.py
```

Current examples/tests:

```text
examples/
└── minimal.py

tests/
├── test_grid.py
├── test_neighborhood.py
├── test_rules.py
├── test_simulation.py
└── test_state.py
```

Planned files such as `data.py`, `gis.py`, `config.py`, `metrics.py`, and `behavior/` should be added only when their milestone starts. Do not create empty placeholder modules merely to match a diagram.

## 5. Current CA behavior

### `FireState`

Implemented state set:

```text
UNBURNABLE = 0
UNBURNED   = 1
BURNING    = 2
BURNED     = 3
```

`validate_state_array()` requires a two-dimensional integer array and rejects unsupported state codes.

### `RasterGrid`

Implemented:

- state validation;
- `shape` property;
- optional positive `cell_size`;
- safe state replacement with shape checking;
- independent copy.

No CRS/transform metadata yet. Those belong to the upcoming GIS/data contract.

### Neighborhoods

Implemented:

- `Neighborhood` structural protocol;
- `MooreNeighborhood(radius=...)`;
- `VonNeumannNeighborhood(radius=...)`;
- `valid_neighbor_indices(...)`.

Current boundary semantics are **clipping**: off-grid neighbors are omitted.

### `TransitionRule`

Implemented as a synchronous protocol:

```python
next_state(grid, *, rng) -> array
```

The rule reads the current grid and returns a complete next-state array. `Simulation` applies it only after computation finishes.

This means newly updated cells do not influence other cells within the same step unless a future scheduler explicitly changes that policy.

### `NeighborIgnitionRule`

Implemented as the first transparent wildfire CA reference rule:

```text
BURNING cell
    ↓
becomes BURNED next step
    +
currently UNBURNED neighbors become BURNING
```

It contains **no Rothermel/FBP physics**. This is intentional. It is a baseline for validating CA semantics and neighborhood substitution.

### `Simulation`

Implemented:

- `Simulation.from_seed(...)`;
- explicit `numpy.random.Generator`;
- `step()`;
- `run(steps)`;
- shape/state validation of rule output;
- explicit synchronous replacement semantics.

## 6. Test / CI state

The GitHub Actions workflow contains:

- Ruff lint;
- Ruff format check;
- pytest + coverage in the quality job;
- pytest matrix for Python 3.11, 3.12, 3.13.

During bootstrap CI correctly found two style problems:

1. one 101-character line in `grid.py`;
2. one Ruff-format mismatch in `tests/test_rules.py`.

Both were corrected.

The Python 3.11/3.12/3.13 test jobs have been passing. An English-README-era run completed fully green after the style fixes; later documentation-only commits continue to trigger the same CI.

If the next session begins with a red CI badge, inspect the newest run before changing scientific code.

## 7. Engineering files already present

```text
.github/workflows/ci.yml
.pre-commit-config.yaml
.gitignore
pyproject.toml
CITATION.cff
CHANGELOG.md
CONTRIBUTING.md
README.md
README.zh-CN.md
```

`pyproject.toml` currently uses:

- Python `>=3.11`;
- Hatchling;
- NumPy core dependency;
- optional `gis` extra for Rasterio;
- optional `dev` extra for pytest/coverage/Ruff/pre-commit.

## 8. Documentation contract

Living documents:

```text
docs/DESIGN.md
docs/DEVELOPMENT.md
docs/STATUS.md
docs/HANDOFF.md
docs/VALIDATION.md
```

README is the landing page. Detailed scientific assumptions, derivations, validation protocols, and developer continuation details belong under `docs/`.

RepoForge philosophy to preserve:

- scientific-python / standard style;
- README remains representative and runnable;
- validation and limitations are explicit;
- hand-edited scientific body prose must not be casually overwritten by a template tool;
- if RepoForge managed sections are applied later, prefer managed header regions rather than whole-file ownership.

## 9. Performance contract

Do not begin with C++, Cython, CUDA, Torch, or JAX.

Development order:

```text
readable NumPy reference
      ↓
scientific/regression tests
      ↓
profiling
      ↓
Numba only for measured hotspots
```

Keep the NumPy reference after optimization so equivalence can be tested.

## 10. Data-model direction

Prefer structure-of-arrays:

```text
state       [Y, X]
fuel        [Y, X]
slope       [Y, X]
aspect      [Y, X]
wind_speed  [T, Y, X]
wind_dir    [T, Y, X]
moisture    [T, Y, X]
```

Do not create one heavyweight Python object per raster cell.

Future GIS compatibility checks should cover:

```text
CRS
shape
resolution
transform
extent
NoData
units where scientifically important
```

## 11. Immediate next implementation target

Do **not** jump directly into the full Rothermel or FBP equations.

First establish the common fire-behavior boundary:

```text
FireBehaviorResult
      ↓
FireBehaviorModel protocol
      ↓
minimal environmental input contract
      ↓
reference tests
```

The purpose is to ensure Rothermel and FBP can both feed CA rules through one stable interface.

Recommended next files:

```text
src/pyfireca/behavior/__init__.py
src/pyfireca/behavior/base.py
src/pyfireca/data.py

tests/test_behavior_base.py
tests/test_data.py
```

Only create `rothermel.py` after the result/input contracts and units are documented.

## 12. Open design questions

These remain intentionally unresolved:

1. Exact common output fields/units for Rothermel and FBP.
2. How dynamic weather time coordinates map to simulation time.
3. Full-array vs sparse transition representation for later performance work.
4. Whether future asynchronous/event-driven updating is a scheduler abstraction or a separate simulation class.
5. Exact additional propagation state needed by a Cell2Fire-like distance-accumulation rule.
6. GeoTIFF metadata/NoData convention for arrival time and state outputs.
7. Monte Carlo RNG stream-generation policy.

When one of these is resolved, add a design decision to `docs/DESIGN.md` rather than hiding the choice inside code.

## 13. Definition of a good next handoff

At the end of every development session, this file should answer:

- What changed?
- What tests/CI pass?
- What remains incomplete?
- What scientific assumptions were introduced?
- What design decisions were made?
- What exact module/function should be implemented next?
- What must not be changed accidentally?

The handoff must describe repository truth, not aspirational work that was never implemented.
