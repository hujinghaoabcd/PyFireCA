# Future Research Directions

> Status: **recorded and intentionally deferred**
>
> These ideas are research notes, not the current implementation roadmap. Do not implement a new PyFireCA-specific CA method until the baseline simulator is complete and validated.

## 1. Research line: lattice discretization and directional bias

The current static arrival baseline exposes a clean research question: how does a finite raster-neighborhood topology distort a continuous wildfire spread field?

For a homogeneous Behave/Catchpole ignition-point ellipse,

```text
R(beta) = R_head * (1 - e) / (1 - e*cos(beta))
```

and the continuous travel time from the ignition point can be compared against graph-based CA arrival under a fixed neighborhood.

Current observations:

- Moore8 produces lower arrival MAE/RMSE than VN4 against the continuous ellipse reference;
- with the same physical problem, the homogeneous lattice-arrival error is invariant to head-fire rotation relative to the square grid;
- reducing cell size alone does not force error rapidly to zero when the allowed propagation direction set remains fixed;
- fixed 4/8-direction graph metrics retain Manhattan/octile-like anisotropy even as the raster is refined.

The key analytical relation currently under test is

```text
t_CA - t_continuous
    = (D_lattice - D_euclidean) / (R_head * (1 - e))
```

for the homogeneous ignition-point ellipse under the current directional edge construction.

Potential future paper questions:

1. Can lattice error be characterized analytically for different neighborhood stencils?
2. How does the number and angular distribution of admissible propagation directions control error?
3. Does an extended or adaptive directional stencil converge toward the continuous ellipse more efficiently than simply refining cell size?
4. Can a neighborhood be designed to minimize lattice bias while preserving strict obstacle/domain semantics?

Potential future method families, **not for current implementation**:

```text
VN4
Moore8
extended 16/24-direction stencil
directional/adaptive stencil
multi-scale neighborhood
geometry-aware neighborhood
```

## 2. Research line: heterogeneous cell-interface coupling

The current physical baseline is explicit:

```text
R_ij = R_source
```

so the source cell controls outgoing edge ROS.

A separately implemented comparison baseline is the two-half-cell interface travel time:

```text
t_ij = (d/2)/R_source + (d/2)/R_target
```

which is equivalent to a harmonic-mean edge rate when both rates are positive.

Current observations:

- source-only coupling introduces a directional interface bias when a front crosses a sharp fuel boundary;
- fast-to-slow and slow-to-fast crossings shift arrival time in opposite directions;
- the half-cell interface formulation places the material boundary at the midpoint between cell centers and removes that specific one-sided assumption.

Potential future paper questions:

1. Which interface rule best approximates a continuous heterogeneous medium?
2. How do source-only, target-only, harmonic, resistance-based, or subcell interface models affect arrival error?
3. How do interface semantics interact with resolution and neighborhood topology?
4. Can an interface formulation remain interpretable while reducing discretization bias across sharp fuel transitions?

## 3. Research line: resolution does not equal directional convergence

A key hypothesis to preserve for future study is:

> Spatial refinement and directional refinement are different operations.

A smaller raster cell can reduce geometric discretization error, but if the graph still permits only the same four or eight edge directions, the limiting path metric may remain anisotropic.

Future experiments should therefore separate:

```text
cell size
number of allowed directions
angular spacing of directions
edge-coupling semantics
landscape heterogeneity
```

rather than treating resolution as a single proxy for CA accuracy.

## 4. What must happen before this research line resumes

Do not turn these ideas into a new PyFireCA-specific method until the simple simulator baseline is complete.

The baseline simulator must first provide:

- stable deterministic wildfire simulation from input to GIS output;
- audited standard fuel-model support sufficient for ordinary examples;
- clear configuration/CLI workflow;
- ignition input;
- validated Rothermel behavior and directional spread;
- raster landscape loading and validation;
- arrival/state/perimeter outputs;
- reproducible run metadata;
- end-to-end examples and documentation;
- green CI and validation suite.

Only after that baseline is frozen should a new research branch introduce extended/adaptive neighborhoods or new interface rules.

## 5. Research discipline

When this line resumes:

- keep the validated baseline unchanged;
- introduce every new CA mechanism as a named variant;
- compare against the continuous analytical/reference solution where possible;
- report arrival-time and shape/perimeter error, not only visual fire footprints;
- separate behavioral-model error from propagation/discretization error;
- do not claim novelty before a dedicated literature review confirms the gap.
