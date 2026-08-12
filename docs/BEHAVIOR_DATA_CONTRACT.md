# Fire Behavior and Environmental Data Contract

> Status: active design contract for Milestone C
>
> Updated: 2026-08-12

## 1. Purpose

This document defines the boundary between wildfire fire-behavior calculations, environmental data, and cellular-automata transition rules.

The goal is not to force Rothermel, FBP, and future models into one artificial input schema. The goal is to make their **outputs predictable for CA rules** while keeping model-specific scientific inputs explicit and independently testable.

The intended flow is:

```text
Environmental / fuel data
        ↓
model-specific input adapter
        ↓
FireBehaviorModel
        ↓
FireBehaviorResult
        ↓
CA TransitionRule
```

`Simulation` does not select behavior models and does not interpret model-specific diagnostics.

## 2. Common behavior output

All fire-behavior implementations return `FireBehaviorResult`.

Current common fields:

| Field | Unit / convention | Required | Meaning |
| --- | --- | --- | --- |
| `spread_rate_m_s` | m/s | yes | local or forward rate of spread supplied to CA propagation |
| `spread_direction_deg` | degrees clockwise from geographic north, `[0, 360)` | no | local/maximum spread direction when defined |
| `fireline_intensity_w_m` | W/m | no | fireline intensity when supported |
| `flame_length_m` | m | no | flame length when supported |
| `diagnostics` | model-specific scalar values | no | scientific diagnostics not part of the portable CA contract |

Invalid or non-finite common quantities fail explicitly. PyFireCA does not silently clamp negative spread rate, wrap invalid directions, or replace invalid diagnostics.

## 3. Unit policy

Quantities crossing the common behavior-to-CA boundary use explicit SI-derived units in field names.

A source model may use its documented native units internally. Conversion to the PyFireCA common output occurs at the behavior-model boundary and must be covered by reference tests.

Do not infer units from array values or filenames.

Generic environmental layers may carry a `units` metadata string. That metadata is descriptive in the current milestone; automatic unit conversion is intentionally deferred.

## 4. Direction convention

When a common spread direction is provided, PyFireCA uses:

```text
0°   = geographic north
90°  = east
180° = south
270° = west
```

Angles increase clockwise and must satisfy `0 <= direction < 360`.

A behavior implementation whose source equations use another convention must convert explicitly at its output boundary. The conversion belongs in the model implementation and its tests, not in `Simulation`.

## 5. Model-specific input policy

`FireBehaviorModel` is generic in its input type:

```python
FireBehaviorModel[InputT]
```

This is intentional.

Examples of future model-specific contracts may include:

```text
RothermelInputs
FBPInputs
```

They may differ in fuel representation, moisture fields, wind conventions, or other scientific parameters.

Do not create a giant `FireBehaviorInputs` object containing every field used by every model. Such an object would make optional/undefined values common, weaken typing, and hide scientific differences.

Interchangeability is achieved by a stable **result** contract plus explicit adapters from environmental data to each model's native input type.

## 6. Environmental layer representation

The initial in-memory data contract contains two small types:

```text
SpatialLayer
EnvironmentalData
```

A `SpatialLayer` is either:

```text
static:   (Y, X)
dynamic:  (T, Y, X)
```

It may carry:

```text
units
nodata
```

No CRS, affine transform, reprojection, or file path is stored in this generic numerical layer yet. Those belong to the GIS adapter/grid metadata milestone.

## 7. Environmental alignment rules

`EnvironmentalData` requires:

1. at least one named layer;
2. non-empty layer names;
3. every value to be a `SpatialLayer`;
4. identical spatial `(Y, X)` shape for every layer;
5. identical `T` length across dynamic layers in the initial index-based contract.

The initial contract deliberately uses **time indices**, not physical timestamps.

Example:

```python
snapshot = data.snapshot(time_index=3)
```

returns one aligned `(Y, X)` array for each layer. Static layers are reused unchanged; dynamic layers return slice `3`.

## 8. Why physical time is deferred

WRF, ERA5, observations, and synthetic scenarios can use different time coordinates and cadences. Introducing datetime interpolation before one concrete integration exists would create unnecessary abstractions.

The current rule is:

```text
Milestone C: consistent integer time index
later GIS/weather milestone: explicit physical time coordinate + documented interpolation
```

When physical time is introduced, it must not silently interpolate or extrapolate without a declared policy.

## 9. NoData policy

`SpatialLayer.nodata` currently carries metadata only.

The numerical kernel does not yet mask or impute NoData automatically. Before behavior-informed CA is applied to real GIS data, the GIS/data-validation layer must define which cells are invalid/unburnable and ensure incompatible data are rejected or intentionally preprocessed.

This avoids hidden scientific behavior such as silently replacing missing moisture with zero.

## 10. Intended future adapters

A future behavior-informed workflow may look like:

```text
EnvironmentalData.snapshot(t)
        ↓
RothermelInputBuilder / FBPInputBuilder
        ↓
model.compute(inputs)
        ↓
FireBehaviorResult
        ↓
spread rule
```

The adapter layer should remain small and explicit. A CA rule should consume the common quantities it scientifically requires and avoid dependence on model-specific diagnostics unless the rule itself is explicitly model-specific.

## 11. Validation requirements

Before a behavior model is considered implemented:

1. document source equations and source units;
2. define its model-specific input dataclass;
3. test unit conversions into the common output;
4. compare representative calculations with an independent/reference implementation;
5. test invalid-domain handling;
6. add at least one integration case showing the result can feed a CA rule without `Simulation` model-name branches.

## 12. Explicitly deferred items

Not part of this contract yet:

- full Rothermel equations;
- FBP equations;
- fuel-model database design;
- CRS/affine metadata;
- automatic reprojection/resampling;
- physical datetime coordinates;
- temporal interpolation;
- xarray/Zarr storage abstraction;
- spatial masks/NoData execution semantics;
- Cell2Fire-like distance accumulation.

These are added only when their milestone begins and with corresponding design/tests.
