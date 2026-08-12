# PyFireCA

**A modular and extensible cellular automata framework for wildfire spread simulation in Python.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](#installation)
[![CI](https://github.com/hujinghaoabcd/PyFireCA/actions/workflows/ci.yml/badge.svg)](https://github.com/hujinghaoabcd/PyFireCA/actions/workflows/ci.yml)
[![Status](https://img.shields.io/badge/status-early%20development-orange)](#project-status)

[简体中文](README.zh-CN.md) · [Architecture](docs/DESIGN.md) · [Development](docs/DEVELOPMENT.md) · [Validation](docs/VALIDATION.md) · [Handoff](docs/HANDOFF.md)

## Why PyFireCA?

Wildfire cellular-automata implementations often mix fire-behavior equations, neighborhood traversal, grid state, GIS I/O, simulation control, and experiment code. That makes it difficult to change the CA formulation without rewriting unrelated parts of the model.

PyFireCA separates the CA mechanisms that are expected to evolve during research—**state, neighborhood, transition rule, and time stepping**—from wildfire behavior and GIS data handling. The first releases deliberately prioritize a clear NumPy reference implementation, reproducibility, validation, and extensibility over premature acceleration.

## Design goals

- **CA-first** — wildfire spread is modeled through explicit cellular-automata components.
- **Extensible** — neighborhoods and transition rules can be replaced without rewriting the simulation loop.
- **Fire-behavior modularity** — Rothermel/FBP-style behavior models are kept separate from CA propagation rules.
- **GIS-aware** — raster metadata and geospatial alignment are explicit parts of the data contract.
- **Reproducible** — simulations use explicit random generators, configuration, regression tests, and validation cases.
- **Research-software quality** — `src/` layout, typing, tests, Ruff, pre-commit, CI, design documentation, and handoff documentation are maintained from the beginning.

## Architecture

```text
GIS / environmental data
          ↓
         Grid
          ↓
         State
          ↓
     Neighborhood
          ↓
Fire behavior → Transition rule
          ↓
      Simulation
          ↓
        Metrics
```

The detailed architecture and extension boundaries are documented in [`docs/DESIGN.md`](docs/DESIGN.md).

## Installation

PyFireCA is currently an early-development source package.

```bash
git clone https://github.com/hujinghaoabcd/PyFireCA.git
cd PyFireCA
python -m pip install -e ".[dev]"
```

## Quick start

The first executable reference rule is deliberately simple: a burning cell becomes burned and ignites currently unburned cells in its selected neighborhood. It exists to validate CA architecture before Rothermel/FBP physics are added.

```python
import numpy as np

from pyfireca import (
    FireState,
    MooreNeighborhood,
    NeighborIgnitionRule,
    RasterGrid,
    Simulation,
)

state = np.full((7, 7), FireState.UNBURNED, dtype=np.uint8)
state[3, 3] = FireState.BURNING

grid = RasterGrid(state=state, cell_size=30.0)
rule = NeighborIgnitionRule(MooreNeighborhood(radius=1))
sim = Simulation.from_seed(grid=grid, rule=rule, seed=42)

sim.run(steps=3)
print(sim.grid.state)
```

A runnable version is available at [`examples/minimal.py`](examples/minimal.py).

## Planned scientific scope

The initial scope is intentionally narrow:

- raster cellular automata for wildfire spread;
- replaceable neighborhood definitions;
- replaceable transition rules;
- deterministic and stochastic CA formulations;
- Rothermel and FBP-style fire-behavior interfaces;
- static and time-varying environmental layers;
- GeoTIFF-oriented GIS workflows;
- NumPy reference implementation, followed by profiling-led Numba optimization;
- Monte Carlo experiments and scientific validation.

Out of scope for the initial releases: differentiable CA, PyTorch/JAX backends, Level Set propagation, front tracking, CFD, urban simulation, Web UI, and distributed services.

## Validation

Scientific validation is a first-class project requirement rather than a final release task. Planned validation includes neighborhood invariants, deterministic regression cases, fire-behavior reference calculations, grid/time-step sensitivity, directional-bias diagnostics, and reference-model comparisons. See [`docs/VALIDATION.md`](docs/VALIDATION.md).

## Development documents

Development-stage documents are maintained continuously:

- [`docs/DESIGN.md`](docs/DESIGN.md) — architecture, responsibilities, extension boundaries, and design decisions;
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) — implementation roadmap and development rules;
- [`docs/STATUS.md`](docs/STATUS.md) — current repository state and active work;
- [`docs/HANDOFF.md`](docs/HANDOFF.md) — detailed continuation guide for the next development session;
- [`docs/VALIDATION.md`](docs/VALIDATION.md) — scientific and numerical validation plan.

## Citation

Software citation metadata is available in [`CITATION.cff`](CITATION.cff).

## Project status

PyFireCA is in **early development**. The current milestone is `v0.1.0`: establish a small, tested CA reference core before implementing complete wildfire spread formulations.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Architecture changes should follow the contracts in `docs/DESIGN.md` and keep `docs/STATUS.md` / `docs/HANDOFF.md` synchronized with code changes.
