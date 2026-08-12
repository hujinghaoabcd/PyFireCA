# Validation fixtures

This directory contains small, pinned external-reference snapshots used for scientific validation.

Evidence grades are defined in `docs/VALIDATION.md`:

```text
Grade A  primary/authoritative worked value
Grade B  official operational software regression
Grade C  independent software comparison
Grade D  internal synthetic/analytical fixture
```

## 1. Albini 1976 worked examples

File:

```text
data/albini1976_worked_examples.csv
```

Evidence grade: **A**.

Source: Frank A. Albini (1976), *Estimating Wildfire Behavior and Effects*, USDA Forest Service GTR INT-30, worked examples on printed pages 10 and 16.

The two pinned examples cover:

1. level ground with nonzero wind;
2. calm wind with nonzero slope.

They are valuable later R3/R4 whole-model checks but are not the dedicated base-ROS case.

## 2. Behave 7 upstream surface regression snapshot

File:

```text
data/behave7_surface_reference.csv
```

Evidence grade: **B**.

Pinned provenance:

```text
repository: firelab/behave-app
app commit: a3cfcd5903188d73445948af16644868225bb9d5
source path: behave-lib/test/csv/surface.csv
source blob SHA: 975000d8dc3def0f25a22df0777e4ab70016c996
validator: behave-lib/test/cpp/testSurface.cpp
```

This is copied from the official Behave 7 regression data. The official validator runs the Surface module, retrieves spread rate in chains/hour, and compares with tolerance `1e-6`.

These rows primarily exercise nonzero wind/slope and are reserved for later full-surface validation.

## 3. Behave 7 R2 zero-wind / zero-slope reference

File:

```text
data/behave7_r2_zero_wind_zero_slope.csv
```

Evidence grade: **B — official operational software regression generated from a pinned build**.

Pinned code provenance:

```text
Behave app:  firelab/behave-app
app commit:  a3cfcd5903188d73445948af16644868225bb9d5
Behave core: firelab/behave
core commit: 29888c7ad364aa18cfb340f4c25a8e395f24260f
```

The repository workflow `.github/workflows/behave7-r2-probe.yml` checks out exactly those revisions, builds the official `testSurface` executable, and verifies the reference case.

Reference conditions:

```text
fuel model                 FM1 / model 1
1-h dead moisture          5%
10-h dead moisture         5%
100-h dead moisture        5%
live herb moisture         100%  (no live load in FM1)
live woody moisture        100%  (no live load in FM1)
midflame wind              0 ft/min, DirectMidflame
slope                      0%
aspect                     0°
canopy cover/height         0
```

Pinned official result:

```text
spread rate = 4.4262698923571939 chains/hour
            = 0.024733996158492002 m/s
```

The SI conversion uses exactly `1 chain = 20.1168 m` and `1 hour = 3600 s`.

The fixture also records the native FM1 parameters needed to reconstruct the dead-only base-ROS case:

```text
fuel-bed depth             1.0 ft
dead moisture extinction   0.12
heat content               8000 Btu/lb
1-h dead load              0.034 lb/ft²
1-h SAV                     3500 1/ft
total mineral fraction     0.0555
effective mineral fraction 0.01
particle density            32 lb/ft³
```

### What this resolves

This fixture resolves the previous R2 numeric-gate gap: PyFireCA now has an independently generated official zero-wind/zero-slope target for the selected operational Rothermel line.

### What it does **not** validate

FM1 contains only dead 1-h fuel load. Therefore this case validates the **dead-only no-wind/no-slope chain** but does not independently validate:

- live moisture of extinction;
- dead/live reaction-intensity combination under nonzero live load;
- dynamic herbaceous load transfer;
- wind/slope effects.

Those require additional external cases before their respective stages are considered validated.

## 4. Fixture update policy

External snapshots are immutable by default. Updating one requires:

1. intentionally selecting a new source document/software revision;
2. reviewing scientific/implementation differences;
3. updating exact provenance;
4. updating the fixture SHA/integrity test;
5. explaining changed expected values in project documentation/changelog.

Do not overwrite external reference values merely to make PyFireCA tests pass.
