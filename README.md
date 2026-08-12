# PyFireCA

**A modular, validated, and GIS-ready cellular-automata framework for wildfire spread simulation in Python.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](#installation)
[![CI](https://github.com/hujinghaoabcd/PyFireCA/actions/workflows/ci.yml/badge.svg)](https://github.com/hujinghaoabcd/PyFireCA/actions/workflows/ci.yml)
[![Status](https://img.shields.io/badge/status-alpha-orange)](#project-status)

[简体中文](README.zh-CN.md) · [Run the simulator](docs/RUNNING_SIMULATOR.md) · [Architecture](docs/DESIGN.md) · [Validation](docs/VALIDATION.md) · [Status](docs/STATUS.md) · [Handoff](docs/HANDOFF.md)

## Why PyFireCA?

Wildfire cellular-automata implementations often mix fire-behavior equations, raster geometry, transition logic, GIS I/O, and experiment code. PyFireCA separates those concerns so the scientific behavior model, propagation semantics, spatial data contract, and user workflow can be validated independently.

The current baseline is deliberately practical: **first build a small, complete, reproducible wildfire simulator; keep new PyFireCA-specific CA innovations outside the default implementation until that baseline is frozen.**

## Current baseline

PyFireCA currently provides an end-to-end static raster workflow:

```text
YAML configuration + aligned GeoTIFFs + ignition events
                         ↓
                   input validation
                         ↓
             audited standard fuel models
                         ↓
         Albini-adjusted Rothermel behavior
                         ↓
     Behave/Catchpole directional surface spread
                         ↓
           physical earliest-arrival propagation
                         ↓
       arrival / state / burned footprint outputs
                         ↓
          reproducible run metadata and hashes
```

Implemented baseline capabilities include:

- validated Albini-adjusted Rothermel behavior;
- wind, slope, dynamic herbaceous curing, and optional wind-speed limiting;
- Behave-compatible surface-fire ellipse and off-axis `FromIgnitionPoint` spread;
- audited Anderson fuel models **FM1–FM13** plus Scott–Burgan **GR1 (101)**;
- static heterogeneous raster landscapes;
- one or more ignition cells, including delayed ignition times;
- physical earliest-arrival propagation on the immediate Moore-8 baseline;
- GeoTIFF arrival/state/burned-mask outputs;
- WGS84 burned-footprint GeoJSON;
- reproducible configuration, environment, input hashes, metrics, and run log;
- Python API and `pyfireca validate/run` CLI;
- Python 3.11–3.13, GIS, regression, and pinned Behave validation tests.

## Installation

Clone the repository and install the GIS-enabled baseline simulator:

```bash
git clone https://github.com/hujinghaoabcd/PyFireCA.git
cd PyFireCA
python -m pip install -e ".[gis]"
```

For development:

```bash
python -m pip install -e ".[dev,gis]"
```

## Quick start

Start from [`examples/static_run.yml`](examples/static_run.yml), point it at ten aligned GeoTIFF layers, and validate the complete input contract:

```bash
pyfireca validate examples/static_run.yml
```

Then run:

```bash
pyfireca run examples/static_run.yml
```

A completed run produces:

```text
runs/static-example/
├── config.resolved.yml
├── metadata.json
├── environment.json
├── metrics.json
├── log.txt
└── outputs/
    ├── arrival_time.tif
    ├── state.tif
    ├── burned_mask.tif
    └── perimeter.geojson
```

See [`docs/RUNNING_SIMULATOR.md`](docs/RUNNING_SIMULATOR.md) for exact raster units, NoData semantics, ignition syntax, validation rules, outputs, and Python API usage.

## Scientific architecture

```text
GIS / EnvironmentalData
          ↓
      LandscapeInput
          ↓
   Rothermel inputs per cell
          ↓
   FireBehaviorModel
          ↓
 directional surface spread
          ↓
 edge travel time = distance / directional ROS
          ↓
 earliest arrival
          ↓
 FireState / GIS outputs
```

The original synchronous CA reference path remains available separately for architecture testing. It is not assigned a hidden physical `dt` and is not silently substituted for the physical-arrival baseline.

Detailed responsibilities and extension boundaries are documented in [`docs/DESIGN.md`](docs/DESIGN.md).

## Input contract

The baseline file workflow requires aligned, north-up, square, metric raster grids containing:

```text
fuel model                   integer code
1-h dead moisture            fraction
10-h dead moisture           fraction
100-h dead moisture          fraction
live herbaceous moisture     fraction
live woody moisture          fraction
midflame wind speed          m/s
meteorological wind-from     degrees
slope                        degrees
aspect                       degrees
```

PyFireCA does not silently convert percentage moisture, percent slope, 10-m wind, radians, or mismatched raster geometry.

## Validation

Scientific validation is a first-class repository capability. Current reference checks include pinned USFS Fire Lab Behave results for base Rothermel spread, wind/slope effects, dynamic GR1 curing, and off-axis directional spread. External fixtures retain source revisions and evidence grades.

See [`docs/VALIDATION.md`](docs/VALIDATION.md) and [`docs/ROTHERMEL_REFERENCE.md`](docs/ROTHERMEL_REFERENCE.md).

## Research extensions

Promising CA research directions—such as lattice bias, extended/adaptive neighborhoods, and heterogeneous interface coupling—are intentionally recorded in [`docs/FUTURE_RESEARCH.md`](docs/FUTURE_RESEARCH.md) rather than being mixed into the current baseline simulator.

The development priority is documented in [`docs/SIMULATOR_ROADMAP.md`](docs/SIMULATOR_ROADMAP.md).

## Development documents

Development-stage documentation is maintained continuously:

- [`docs/DESIGN.md`](docs/DESIGN.md) — architecture and design decisions;
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) — implementation history and roadmap;
- [`docs/STATUS.md`](docs/STATUS.md) — repository truth and current milestone;
- [`docs/HANDOFF.md`](docs/HANDOFF.md) — detailed continuation guide;
- [`docs/SESSION_LOG.md`](docs/SESSION_LOG.md) — session-level implementation record;
- [`docs/VALIDATION.md`](docs/VALIDATION.md) — numerical/scientific validation;
- [`docs/FUTURE_RESEARCH.md`](docs/FUTURE_RESEARCH.md) — deferred paper ideas.

## Citation

Software citation metadata is available in [`CITATION.cff`](CITATION.cff).

## Project status

PyFireCA is an **alpha research-software project**. The static baseline simulator is now functional end to end; current work is focused on finishing documentation, release-quality integration checks, and the remaining baseline polish before freezing the first simple simulator release.

Dynamic weather/WRF coupling, crown fire, spotting, suppression, Monte Carlo, FBP, GPU backends, and new PyFireCA-specific CA methods are not part of the current baseline release target.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Scientific or architectural changes should preserve validation provenance and keep `docs/STATUS.md` / `docs/HANDOFF.md` synchronized with repository truth.
