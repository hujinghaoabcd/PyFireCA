# Validation fixtures

This directory contains small, pinned external-reference snapshots used for scientific validation.

External numbers are not treated equally. See `docs/VALIDATION.md` for the evidence-grade policy:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent software comparison
Grade D  internal synthetic/analytical fixture
```

## Albini 1976 worked examples

File:

```text
data/albini1976_worked_examples.csv
```

Evidence grade: **A — primary/authoritative worked value**.

Source:

```text
Frank A. Albini (1976)
Estimating Wildfire Behavior and Effects
USDA Forest Service General Technical Report INT-30
Examples section, printed pages 10 and 16
```

The source gives two worked nomograph examples:

1. fuel model 3, fuel moisture 5%, 20-ft wind 8 mi/h, level ground → spread rate `97 chains/hour`, flame length `12.5 ft`;
2. fuel model 2, fine dead moisture 8%, live foliage moisture about 50%, calm wind, slope 70% → spread rate `34 chains/hour`, flame length `6.2 ft`.

These are valuable full-surface-fire validation cases, but neither is the dedicated R2 no-wind/no-slope fixture:

```text
Example 1: slope = 0, wind > 0
Example 2: wind = 0, slope > 0
```

They should therefore be used after wind/slope integration (R3/R4), not as a substitute for the R2 base-ROS reference.

## Behave 7 surface reference

File:

```text
data/behave7_surface_reference.csv
```

Evidence grade: **B — official operational software regression**.

Pinned upstream provenance:

```text
repository: firelab/behave-app
commit: a3cfcd5903188d73445948af16644868225bb9d5
source path: behave-lib/test/csv/surface.csv
source blob SHA: 975000d8dc3def0f25a22df0777e4ab70016c996
upstream validator: behave-lib/test/cpp/testSurface.cpp
```

The upstream `testSurface.cpp` reads the CSV rows, supplies the listed inputs to the Behave Surface module, runs the calculation in the direction of maximum spread, retrieves spread rate in `ChainsPerHour`, and checks the expected value with an error tolerance of `1e-6`.

The snapshot is copied verbatim from the pinned upstream CSV so future changes to Behave do not silently change PyFireCA's regression reference. Updating the snapshot requires:

1. selecting a new upstream commit intentionally;
2. reviewing the upstream diff;
3. recording the new commit/blob SHA here;
4. explaining any changed expected values in `CHANGELOG.md` / validation notes.

### Scope limitation

The current Behave upstream surface CSV contains nonzero wind/slope cases plus a nonburnable fuel-model case. It is useful for later whole-surface R3/R4 validation, but it is **not** the dedicated zero-wind/zero-slope R2 reference fixture.

## Current R2 reference gap

The source audit has found strong Grade A/B references for whole-model behavior, but not yet a precise tabulated zero-wind **and** zero-slope worked value that matches the selected Albini-adjusted R2 formulation.

Rothermel 1972 contains no-wind equations and graphical results, including curves spanning zero wind, but graph reading is not precise enough to serve as a high-accuracy regression constant. Albini's worked examples isolate either level ground or calm wind, not both simultaneously.

PyFireCA therefore records the R2 numerical fixture as an explicit validation gap rather than manufacturing a value. The next R2 work should either locate a suitable Grade A value or construct a pinned Grade B zero-wind/zero-slope case using the official Behave implementation while clearly retaining its Grade B status.
