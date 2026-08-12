# CA Discretization and Edge-Coupling Experiment Design

> Status: design baseline for the next PyFireCA research stage
>
> Principle: keep the validated fire-behavior model fixed while changing only CA/discretization assumptions.

## 1. Scientific objective

PyFireCA now has a validated local surface-fire behavior path and a static GIS-to-arrival pipeline. The next research question is therefore not another Rothermel formula:

> **How do raster CA neighborhood topology, grid resolution, orientation, and interface/edge semantics alter the propagation produced from the same continuous directional fire behavior?**

This separates:

```text
fire-behavior error
from
CA spatial-discretization error
```

and directly targets the CA component of the framework.

## 2. Why start with a homogeneous analytical benchmark

For one homogeneous static Rothermel behavior state, PyFireCA already has a Behave-aligned ignition-point ellipse.

For direction `beta` relative to heading:

```text
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

For a cell center at polar distance `r` and direction `beta`, the continuous-reference arrival time is therefore:

```text
t_reference = r / R(beta)
```

This provides an analytical reference independent of the raster shortest-path solver.

It is preferable to comparing one CA implementation only against another CA implementation because the benchmark can isolate lattice/discretization error directly.

## 3. Experiment A — neighborhood topology

### Fixed science

Use one validated homogeneous FM1 Rothermel state, initially:

```text
fuel                   FM1
moisture               5/5/5% dead
midflame wind          100 ft/min equivalent SI
slope                  0
```

Keep:

```text
Rothermel equations
wind input
surface ellipse
directional ROS
ignition location
domain extent
```

identical.

### CA variants

First compare only immediate-neighbor topologies with unambiguous physical edges:

```text
VN4      Von Neumann radius 1
Moore8   Moore radius 1
```

Do **not** include radius>1 neighborhoods yet.

`StaticArrivalTimeSolver` now rejects long-range offsets because a direct `(0, 2)` edge could otherwise jump over an intervening `UNBURNABLE` cell. Extended neighborhoods require explicit intermediate-cell/path-intersection semantics before they become valid physical variants.

### Hypothesis

VN4 should show stronger Manhattan/lattice anisotropy. Moore8 should reduce but not eliminate orientation-dependent propagation error.

The experiment should quantify this rather than assume it.

## 4. Experiment B — heading orientation relative to the lattice

A square raster has preferred axes. Rotate the maximum-spread direction while keeping the physical fire behavior magnitude/shape otherwise equivalent.

Suggested headings:

```text
0°
15°
30°
45°
60°
75°
90°
```

Because of square-grid symmetry, 0–90° is sufficient for the first controlled benchmark.

Key question:

> Does error depend systematically on the angle between the physical heading direction and raster axes/diagonals?

This is a direct measure of lattice directional bias.

## 5. Experiment C — cell-size sensitivity

Repeat the same physical problem at several square-grid resolutions.

Suggested initial set:

```text
5 m
10 m
20 m
30 m
60 m
```

The physical domain, ignition coordinate, weather, and reference ellipse remain unchanged.

Metrics should be evaluated in physical units and normalized where useful, so finer grids are not automatically favored merely because they contain more cells.

Questions:

1. Does arrival-time error converge as cell size decreases?
2. Does perimeter/shape error converge?
3. Does orientation bias decrease monotonically?
4. What computational cost is paid for each reduction in error?

## 6. Analytical arrival reference

For a north-up grid with ignition at physical coordinate `(x0, y0)`, each cell center has:

```text
dx = x - x0
dy = y - y0
r  = hypot(dx, dy)
bearing = geographic bearing from ignition to cell center
beta = angular separation from physical head direction
```

Then:

```text
R_beta = surface_ellipse_directional_ros(beta)
t_ref  = r / R_beta
```

The ignition center has `t_ref = 0`.

This analytical field becomes the primary Grade-D mathematical reference for discretization experiments. It is not a new Grade-B Behave fixture; Behave validation has already established the underlying directional ellipse equation.

## 7. Arrival-time metrics

Evaluate only cells within a physically meaningful analysis window to avoid edge effects from the finite test domain.

Core metrics:

```text
MAE_t   = mean(|t_CA - t_ref|)
RMSE_t  = sqrt(mean((t_CA - t_ref)^2))
Bias_t  = mean(t_CA - t_ref)
```

Recommended normalized forms:

```text
nMAE_t  = MAE_t / T_ref
nRMSE_t = RMSE_t / T_ref
```

where `T_ref` is a selected physical evaluation time or another explicitly documented scale.

Also record quantiles of absolute error rather than only the mean.

## 8. Directional bias metrics

Partition cell centers by bearing bins relative to the ignition point, for example 5° or 10° bins.

For each bin compute:

```text
mean arrival error
median arrival error
front-distance error at selected time
```

A useful scalar anisotropy index can be defined only after inspecting the angular error curve; do not invent one prematurely. The full angular error profile should remain available even if a summary statistic is introduced later.

## 9. Fire-shape / perimeter metrics

At selected physical times `T`:

```text
reference burned set = cells with t_ref <= T
CA burned set        = cells with t_CA <= T
```

First raster-set metrics:

```text
IoU / Jaccard
precision
recall
area bias
```

Geometric metrics after converting fronts/perimeters to physical coordinates may include:

```text
Hausdorff distance
mean symmetric boundary distance
head-position error
backing-position error
flank-position error
```

Do not make perimeter polygonization a dependency of the core solver. Keep evaluation in a metrics/experiment layer.

## 10. Runtime metrics

For every configuration record:

```text
number of cells
number of reachable cells
neighborhood edge count
wall-clock solve time
peak memory if available
```

Performance is secondary to correctness in the reference phase, but it is useful for later profiling/Numba decisions.

## 11. Experiment D — heterogeneous interface/edge semantics

After the homogeneous lattice benchmark is stable, introduce a simple two-region landscape with a sharp fuel or wind boundary.

### D0 — current baseline

```text
SourceCellEdge
R_ij = R_source(direction i→j)
```

This is the current `StaticSpatialRothermelDirectionalSpreadRate` semantics.

### D1 — half-cell interface travel

A physically interpretable alternative is to treat the center-to-center edge as two half-cell segments:

```text
t_ij = (d/2) / R_source(direction i→j)
     + (d/2) / R_target(direction i→j)
```

For positive rates, the equivalent edge ROS is the harmonic mean:

```text
R_equiv = 2 / (1/R_source + 1/R_target)
```

If either half has zero ROS, the edge is unreachable under this interface model.

This should be implemented as a **separate named provider/edge-coupling strategy**, not by modifying the source-cell baseline.

### Why not start with arithmetic averaging

An arithmetic mean:

```text
(R_source + R_target) / 2
```

is easy to compute but does not correspond to adding the travel times through two equal half-segments. It can later be included as a numerical sensitivity variant, but the half-cell travel/harmonic construction has a clearer physical interpretation for the first interface comparison.

## 12. Heterogeneous benchmark layouts

Start with deterministic synthetic landscapes before real GIS complexity.

Recommended cases:

### H1 — vertical fuel boundary

```text
left region  FM1
right region FM2 or GR1
```

Test fire moving:

```text
fast → slow
slow → fast
parallel to boundary
oblique to boundary
```

### H2 — wind-direction boundary

Same fuel/moisture, different wind directions on each side.

### H3 — narrow barrier / nonburnable strip

Use only immediate-neighbor semantics initially. This is especially useful for testing whether future extended-neighborhood implementations respect intermediate barriers.

## 13. Neighborhood extension gate

Extended neighborhoods may help reduce square-lattice bias, but they introduce a new path semantics problem.

For an offset such as `(1, 2)` or `(0, 2)`, future code must decide what the physical edge crosses.

Possible explicit designs include:

```text
A. straight center-to-center segment with raster line traversal
B. segment split by every crossed cell/interface
C. graph edge allowed only when all intersected cells are burnable
D. weighted path integral through crossed cells
```

These are different models.

Until one is selected and tested, `StaticArrivalTimeSolver` intentionally rejects long-range offsets.

## 14. Experimental reproducibility

Every experiment run should record:

```text
PyFireCA version
Git commit
behavior configuration
fuel model
moistures
wind/slope/aspect
wind-limit setting
cell size
neighborhood
edge-coupling strategy
domain extent
ignition coordinate
analysis times
metrics
runtime
```

The benchmark should be deterministic; no stochastic CA component is needed for this first discretization study.

## 15. Suggested implementation order

```text
E1  analytical homogeneous ellipse arrival field
E2  arrival-error metrics
E3  VN4 vs Moore8 benchmark
E4  heading-angle sweep
E5  cell-size sweep
E6  fire-shape metrics
E7  source-cell vs half-cell-interface coupling
E8  simple heterogeneous boundaries
E9  only then design extended neighborhoods
```

Do not jump from E1 directly to learned/dynamic CA. The point is to establish exactly what error the raster CA discretization itself creates.

## 16. Research value

This benchmark layer serves two purposes:

1. **software validation** — detect regressions in propagation geometry;
2. **scientific CA research** — quantify lattice bias and interface assumptions independently of local fire-behavior equations.

It also creates a controlled foundation for later CA modifications such as adaptive neighborhoods, multiscale grids, or alternative event rules: a new CA method can be judged against the same continuous-reference benchmark rather than only against another implementation.
