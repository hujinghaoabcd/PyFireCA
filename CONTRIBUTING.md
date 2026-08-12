# Contributing to PyFireCA

PyFireCA is early-stage scientific software. Contributions should preserve both scientific transparency and software maintainability.

## Development setup

```bash
git clone https://github.com/hujinghaoabcd/PyFireCA.git
cd PyFireCA
python -m pip install -e ".[dev]"
pre-commit install
```

Run the local quality suite with:

```bash
ruff check .
ruff format --check .
pytest
```

## Contribution rules

### Keep CA changes isolated

When proposing a new cellular-automata method, state clearly which model dimension changes:

- state definition;
- neighborhood;
- transition rule;
- scheduler/time stepping;
- environmental coupling.

Avoid changing unrelated GIS, packaging, or documentation infrastructure in the same scientific change unless necessary.

### Document scientific assumptions

New fire-behavior or propagation implementations should document:

- source equations/reference;
- units;
- assumptions;
- supported input range;
- known limitations;
- validation evidence.

### Add tests with behavior changes

A change is incomplete when it modifies model behavior without corresponding tests.

Use the appropriate level:

- `tests/unit/` or focused top-level tests for isolated contracts;
- integration tests for component interaction;
- regression tests for stable reference simulations;
- validation tests/documents for scientific reference cases.

### Update living development documents

If a change affects architecture, roadmap, current implementation status, or continuation context, update the relevant files:

```text
docs/DESIGN.md
docs/DEVELOPMENT.md
docs/STATUS.md
docs/HANDOFF.md
docs/VALIDATION.md
```

The handoff document must describe repository truth after the change.

## Pull requests

Prefer focused pull requests with:

1. a clear scientific/software motivation;
2. implementation summary;
3. tests performed;
4. validation impact;
5. documentation impact;
6. known limitations or follow-up work.

Do not use performance claims without a reproducible benchmark protocol.

## Style

PyFireCA uses Ruff for linting and formatting. Public APIs should use type hints and scientific array shapes/units should be documented in docstrings where relevant.

## Performance changes

Performance optimization follows this sequence:

```text
reference implementation
→ profiling
→ targeted optimization
→ equivalence tests
→ benchmark
```

Do not replace readable reference code with a faster path unless numerical/scientific equivalence can be checked.
