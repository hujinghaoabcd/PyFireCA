# PyFireCA Static Baseline Release Checklist

> Target: first simple static simulator baseline
>
> Status: pre-release readiness gate

This checklist exists to prevent a source-tree-only success from being mistaken
for a reproducible software release.

## 1. Scope freeze

- [x] Default simulator is static weather only.
- [x] Default physical raster geometry is north-up, square-cell, metric.
- [x] Default physical propagation uses the validated immediate Moore-8 baseline.
- [x] Source-cell-controlled outgoing ROS is the documented heterogeneous baseline.
- [x] Research-only lattice/interface/neighborhood innovations are not exposed in YAML/CLI.
- [x] Dynamic weather, WRF, FBP, crown fire, spotting, suppression, Monte Carlo, GPU work are explicitly deferred.

## 2. Scientific validation

- [x] Albini-adjusted Rothermel base spread protected by pinned Behave regressions.
- [x] Wind/slope/vector-composition regressions protected.
- [x] Dynamic GR1 curing regression protected.
- [x] Behave/Catchpole off-axis `FromIgnitionPoint` directional spread protected.
- [x] Anderson FM1–FM13 records audited from pinned Behave source.
- [x] Existing FM1/FM2/GR1 reference values unchanged after catalogue expansion.
- [x] Physical arrival uses distance / direction-specific ROS.
- [x] Synchronous reference CA still has no hidden physical time step.

## 3. Input/data contract

- [x] Exactly ten baseline raster inputs documented.
- [x] Required units documented explicitly.
- [x] Shape/CRS/full-affine alignment checked.
- [x] North-up square-cell geometry checked.
- [x] Explicit `cell_size_m` checked against raster pixel size.
- [x] Domain/NoData semantics documented and tested.
- [x] Unknown/unaudited fuel codes fail explicitly.
- [x] Ignitions outside the burnable domain fail explicitly.

## 4. User workflow

- [x] Version-1 YAML configuration implemented.
- [x] Relative paths resolve relative to the YAML file.
- [x] `pyfireca validate config.yml` implemented.
- [x] `pyfireca run config.yml` implemented.
- [x] CLI is a thin wrapper around the same Python workflow/scientific implementation.
- [x] Single, multiple, and delayed ignition events supported.
- [x] Non-empty existing output directories are not silently overwritten.

## 5. Result contract

- [x] `config.resolved.yml`.
- [x] `metadata.json`.
- [x] `environment.json`.
- [x] single canonical root `metrics.json`.
- [x] `log.txt`.
- [x] `outputs/arrival_time.tif`.
- [x] `outputs/state.tif`.
- [x] `outputs/burned_mask.tif`.
- [x] `outputs/perimeter.geojson`.
- [x] input SHA-256 recorded.
- [x] fuel catalogue provenance recorded.
- [x] GeoJSON footprint transformed to WGS84 before serialization.

## 6. Automated tests

- [x] Unit/regression tests.
- [x] Python 3.11 test job.
- [x] Python 3.12 test job.
- [x] Python 3.13 test job.
- [x] Rasterio read/write integration tests.
- [x] spatial-output round-trip tests.
- [x] file-based YAML → GeoTIFF → simulator integration test.
- [x] real CLI validate/run integration test with temporary GeoTIFF inputs.
- [ ] Latest release-candidate commit has every CI job green simultaneously.

## 7. Packaging

- [ ] Wheel builds from repository source.
- [ ] Source distribution builds from repository source.
- [ ] Built wheel installs into a clean virtual environment.
- [ ] `pyfireca --help` works from the clean wheel install.
- [ ] `import pyfireca` works from the clean wheel install.
- [ ] `[gis]` extra installs from the built wheel.
- [ ] `import rasterio` works after clean `[gis]` installation.
- [ ] Package metadata has been reviewed for name/version/license/project URLs/classifiers.

These checks are now represented by the CI `package` job where practical.

## 8. Documentation

- [x] English README reflects current simulator, not the old architecture-only state.
- [x] Chinese README reflects current simulator.
- [x] `docs/RUNNING_SIMULATOR.md` documents exact input/output semantics.
- [x] `examples/static_run.yml` exists.
- [x] `docs/STATUS.md` reflects current repository truth.
- [x] `docs/HANDOFF.md` reflects current continuation point.
- [x] `docs/SIMULATOR_ROADMAP.md` reflects completed S1–S7 work.
- [x] `docs/DEVELOPMENT.md` reflects the release-readiness priority.
- [ ] `docs/SESSION_LOG.md` records the simulator-completion session.
- [ ] `CHANGELOG.md` includes all user-visible baseline workflow additions.
- [ ] Documented installation and CLI commands are confirmed against a clean built package.

## 9. Final repository audit

Before tagging:

- [ ] Search docs for stale claims such as “Rothermel not implemented”, “FM1/FM2/GR1 only”, or “CLI planned”.
- [ ] Search code/docs for duplicate or contradictory output semantics.
- [ ] Confirm `__version__` and `pyproject.toml` version agree.
- [ ] Confirm no generated run outputs, caches, or build artifacts are committed accidentally.
- [ ] Confirm no optional research variant became a default accidentally.
- [ ] Confirm latest main CI is all green.

## 10. Tag/release gate

Only after every required item above is satisfied:

- [ ] choose the first baseline release version/tag;
- [ ] freeze release notes from `CHANGELOG.md`;
- [ ] create the tag/release;
- [ ] record the released commit in `STATUS.md` and `HANDOFF.md`.

Do not tag the baseline merely because local/editable-install tests pass.
