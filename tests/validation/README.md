# Validation fixtures

This directory contains small, pinned external-reference snapshots used for scientific validation.

External numbers are not treated equally. See `docs/VALIDATION.md` for the evidence-grade policy:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent software comparison
Grade D  internal synthetic/analytical fixture
```

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

PyFireCA must continue searching for a suitable Grade A worked value, or explicitly document the absence of one, before treating R2 no-wind/no-slope ROS as fully validated.
