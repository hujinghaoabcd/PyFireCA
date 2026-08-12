# PyFireCA Project Status

> Updated: 2026-08-12
>
> Current milestone: **A — Repository foundation**

## Current position

PyFireCA has just entered implementation. The repository is being established as a modern research-software project before wildfire equations are ported or rewritten.

The architectural direction is fixed for the current milestone:

```text
wildfire-specific product
+ explicit CA components
+ compact Python package
+ NumPy reference implementation
+ GIS adapters separated from algorithms
+ development/validation/handoff documents maintained continuously
```

## Completed

- Repository `hujinghaoabcd/PyFireCA` created.
- English and Chinese README initialized.
- Project scope explicitly limited to wildfire CA; urban CA projects are engineering references only.
- Differentiable CA / PyTorch / JAX explicitly excluded from the current development line.
- Modern `pyproject.toml` initialized with Python 3.11+, Hatchling, NumPy, optional GIS/dev dependencies, Ruff and pytest configuration.
- `docs/DESIGN.md` initialized with component ownership and design decisions.
- `docs/DEVELOPMENT.md` initialized with milestone-driven implementation workflow.

## In progress in this bootstrap pass

- minimal CA state model;
- neighborhood model;
- initial tests;
- CI / repository hygiene;
- validation plan;
- handoff document.

## Not implemented yet

### CA core

- raster grid object;
- transition-rule protocol;
- simulation loop;
- synchronous update semantics;
- RNG propagation;
- boundary policy.

### Wildfire science

- Rothermel model;
- FBP model;
- fuel model representation;
- fire-behavior result contract;
- ignition/spread rule;
- arrival time;
- spotting;
- suppression.

### GIS/data

- raster read/write;
- alignment checks;
- static/dynamic layer containers;
- YAML run configuration.

### Validation

- scientific reference cases;
- regression fixtures;
- comparison against Cell2Fire / other reference implementations.

## Key decisions that should not be casually reversed

1. PyFireCA is not a generic urban/geospatial CA product.
2. UrbanVCA/PLUS/intPLUS/Mesa-Geo inform engineering only.
3. Fire behavior and CA propagation stay separate.
4. NumPy remains the readable reference implementation.
5. Numba is introduced after profiling, not as an architectural requirement.
6. GIS file I/O does not enter numerical kernels.
7. The initial module tree stays compact; split modules only when real complexity appears.
8. Development documentation is part of the implementation, not cleanup work.

## Immediate next target

Complete Milestone A and begin Milestone B with a minimal, fully tested CA core:

```text
FireState
RasterGrid
MooreNeighborhood
VonNeumannNeighborhood
TransitionRule
Simulation.step()
```

The first simulation should be tiny and deterministic. Wildfire equations should not be added until these contracts are stable enough to test independently.
