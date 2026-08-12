# Development Priority

> Effective: 2026-08-12
>
> This file overrides older "immediate next research" wording in status/handoff notes when those documents have not yet been refreshed.

## Current priority

**Finish the simple baseline wildfire simulator first.**

Do not implement a new PyFireCA-specific CA method yet.

The development order is:

```text
1. preserve validated behavior/propagation foundations
2. complete ordinary simulator features and user workflow
3. complete GIS/config/CLI/output/reproducibility
4. freeze and validate the simple simulator baseline
5. only then reopen the paper-innovation branch
```

## Innovation ideas

All current innovation ideas are recorded in:

```text
docs/FUTURE_RESEARCH.md
```

They include lattice-bias theory, neighborhood/directional refinement, and heterogeneous interface-coupling questions.

Until the baseline simulator is complete:

- record new ideas;
- add evidence or literature notes if useful;
- do not turn them into default code paths;
- do not add extended/adaptive neighborhoods as a PyFireCA method;
- do not optimize an experimental interface rule;
- keep experimental benchmarks separate from the simulator roadmap.

## Simulator completion plan

Follow:

```text
docs/SIMULATOR_ROADMAP.md
```

The baseline completion target is an end-to-end deterministic workflow:

```text
config + raster landscape + ignition
→ validation
→ Rothermel
→ directional spread
→ physical arrival
→ GIS outputs
→ reproducible run directory
```

## Next implementation work

Prefer simulator-completion tasks in this approximate order:

```text
fuel catalogue coverage
→ user-facing simulation request/API
→ ignition workflow
→ stable result object
→ raster/vector outputs
→ config + CLI
→ reproducible run directory
→ end-to-end examples
→ baseline validation/release
```

Static north-up square metric rasters are sufficient for the first complete simulator. Do not let rotated-grid support, dynamic WRF coupling, crown fire, spotting, suppression, Monte Carlo, or performance optimization delay the first clean baseline.
