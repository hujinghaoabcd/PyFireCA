# PyFireCA Static Baseline Release Checklist

> Target: first simple static simulator baseline
>
> Status: **release candidate pending final all-green license-metadata commit**

This checklist prevents a source-tree-only success from being mistaken for a reproducible software release.

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
- [x] Spatial-output round-trip tests.
- [x] File-based YAML → GeoTIFF → simulator integration test.
- [x] Real CLI validate/run integration test with temporary GeoTIFF inputs.
- [x] Built-wheel GIS end-to-end smoke test exists and has passed.
- [ ] Latest **final MIT-metadata release-candidate commit** has every CI job green simultaneously.

## 7. Packaging

Verified by the CI `package` job before the final MIT-metadata commit:

- [x] Wheel builds from repository source.
- [x] Source distribution builds from repository source.
- [x] Built wheel installs into a clean virtual environment.
- [x] `pyfireca --help` works from the clean wheel install.
- [x] `import pyfireca` works from the clean wheel install.
- [x] `[gis]` extra installs from the built wheel.
- [x] `import rasterio` works after clean `[gis]` installation.
- [x] Clean built `[gis]` wheel can generate input GeoTIFFs and execute `pyfireca validate` + `pyfireca run` end to end.
- [x] Package name/version/author/keywords/project URLs/Python classifiers reviewed.
- [x] Runtime `pyfireca.__version__` is regression-tested against installed distribution metadata.
- [x] Project license selected: **MIT**.
- [x] Root `LICENSE` file added with copyright `2026 Jinghao Hu`.
- [x] `pyproject.toml` declares SPDX `license = "MIT"` and `license-files = ["LICENSE"]`.
- [x] Minimum Hatchling build requirement raised to `>=1.27` so the declared PEP 639 metadata is supported by the minimum backend.
- [ ] Confirm the final package job succeeds with the MIT metadata and includes the license file in built distributions.

## 8. Documentation

- [x] English README reflects the current simulator.
- [x] Chinese README reflects the current simulator.
- [x] `docs/RUNNING_SIMULATOR.md` documents exact input/output semantics.
- [x] `examples/static_run.yml` exists.
- [x] `docs/STATUS.md` reflects current repository truth.
- [x] `docs/HANDOFF.md` reflects current continuation point.
- [x] `docs/SIMULATOR_ROADMAP.md` reflects completed S1–S7 work and S9 release gate.
- [x] `docs/DEVELOPMENT.md` reflects the release-readiness priority.
- [x] `docs/DESIGN.md` reflects the implemented arrival/config/CLI/output architecture.
- [x] `docs/VALIDATION.md` reflects completed R2–R8 and GIS/package validation.
- [x] `docs/STATIC_RASTER_WORKFLOW.md` reflects Anderson FM1–FM13 + GR1.
- [x] `docs/ROTHERMEL_REFERENCE.md` reflects Anderson FM1–FM13 + GR1 and release-freeze priority.
- [x] `docs/SESSION_LOG.md` records the simulator-completion session.
- [x] `CHANGELOG.md` includes user-visible baseline workflow additions.
- [x] Documented installation and CLI commands are confirmed against a clean built package in CI.
- [ ] Add the short MIT license link/badge to README files during the final release-doc pass.

## 9. Final repository audit

Completed:

- [x] Authoritative docs were searched/reviewed for stale pre-Rothermel, FM1/FM2/GR1-only, and CLI-planned claims and updated where they affected current guidance.
- [x] Duplicate run/output metrics semantics were removed; root `metrics.json` is canonical.
- [x] `__version__` and distribution version are protected by an automated equality test.
- [x] Root repository listing contains no generated run/build artifacts; `.gitignore` covers `dist/`, `build/`, `runs/`, `.venv-*`, and `.package-smoke/`.
- [x] Research variants remain absent from the version-1 baseline YAML/CLI.
- [x] License policy is resolved as MIT and represented in repository/package metadata.

Remaining:

- [ ] Confirm the latest final MIT-metadata main commit is all green.
- [ ] Perform the final README license-link pass.

## 10. Tag/release gate

After the two remaining verification/documentation items above:

- [ ] Choose the first baseline release version/tag.
- [ ] Freeze release notes from `CHANGELOG.md`.
- [ ] Create the tag/release.
- [ ] Add the actual release date to `CITATION.cff`.
- [ ] Record the released commit/tag in `STATUS.md` and `HANDOFF.md`.

There is currently no GitHub tag or release, so `CITATION.cff` deliberately does not contain a premature `date-released` field.
