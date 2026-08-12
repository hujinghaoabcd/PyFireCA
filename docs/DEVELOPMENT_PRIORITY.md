# Development Priority

> Effective: 2026-08-13
>
> This file overrides older "immediate next research" wording in historical notes when those documents have not yet been refreshed.

## Current priority

**Freeze the simple static baseline wildfire simulator before implementing a new PyFireCA-specific CA method.**

The ordinary simulator workflow is now implemented end to end. The current development order is therefore:

```text
1. preserve validated behavior/propagation foundations
2. keep all functional/GIS/package CI green
3. finish package metadata and release documentation
4. complete the release-readiness audit
5. choose/freeze the first baseline tag
6. only then reopen the paper-innovation branch
```

## Innovation ideas

Current innovation ideas remain recorded in:

```text
docs/FUTURE_RESEARCH.md
```

They include lattice-bias theory, neighborhood/directional refinement, and heterogeneous interface-coupling questions.

Until the baseline is frozen:

- record new ideas rather than implementing them;
- do not add extended/adaptive neighborhoods as default simulator features;
- do not change source-cell edge coupling invisibly;
- do not expose research variants in version-1 YAML/CLI;
- keep research benchmarks separate from the release-readiness path.

## Implemented simulator path

The current baseline already provides:

```text
YAML + 10 aligned GeoTIFFs + ignition events
→ strict validation
→ audited fuel catalogue
→ Albini-adjusted Rothermel
→ Behave/Catchpole directional spread
→ physical earliest arrival
→ GeoTIFF / WGS84 GeoJSON outputs
→ resolved config / hashes / metadata / metrics / log
```

CLI:

```bash
pyfireca validate config.yml
pyfireca run config.yml
```

Current audited catalogue is sufficient for the first baseline:

```text
Anderson FM1–FM13
Scott–Burgan GR1 (101)
```

## Current implementation work

Follow:

```text
docs/RELEASE_CHECKLIST.md
docs/SIMULATOR_ROADMAP.md
```

Remaining work is release-readiness rather than new simulation science:

```text
clean built-package end-to-end test
→ package metadata audit
→ license decision
→ stale-doc/repository audit
→ all-green release-candidate commit
→ baseline tag/freeze
```

Static north-up square metric rasters are sufficient for this first release. Do not let full Scott–Burgan coverage, rotated grids, dynamic WRF coupling, crown fire, spotting, suppression, Monte Carlo, FBP, or performance optimization delay the baseline freeze.
