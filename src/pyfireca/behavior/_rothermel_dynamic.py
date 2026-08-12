"""Dynamic herbaceous load transfer for Scott--Burgan style fuel models."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite

from pyfireca.behavior.rothermel import FuelClass, RothermelFuelModel, RothermelFuelMoisture


@dataclass(frozen=True, slots=True)
class DynamicFuelTransferResult:
    """Prepared static fuel plus diagnostics from dynamic herbaceous curing."""

    fuel: RothermelFuelModel
    transfer_fraction: float
    transferred_load_kg_m2: float


def compute_dynamic_herbaceous_transfer_fraction(
    live_herbaceous_moisture_fraction: float,
) -> float:
    """Return the Behave/Scott--Burgan live-to-dead herbaceous load fraction.

    The pinned Behave operational path uses 100% transfer below 30% live-herb
    moisture, ``1.333 - 1.11*M`` from 30% through 120%, and no transfer above
    120%. Moisture is expressed on a dry-mass fractional basis.
    """

    if not isfinite(live_herbaceous_moisture_fraction):
        raise ValueError("live_herbaceous_moisture_fraction must be finite")
    if live_herbaceous_moisture_fraction < 0.0:
        raise ValueError("live_herbaceous_moisture_fraction must be non-negative")

    if live_herbaceous_moisture_fraction < 0.30:
        return 1.0
    if live_herbaceous_moisture_fraction <= 1.20:
        return 1.333 - 1.11 * live_herbaceous_moisture_fraction
    return 0.0


def apply_dynamic_herbaceous_transfer(
    fuel: RothermelFuelModel,
    moisture: RothermelFuelMoisture,
) -> DynamicFuelTransferResult:
    """Resolve one dynamic fuel model into a static six-class fuel model.

    Dynamic standard models store herbaceous load initially in the live-herb
    class. Curing transfers part of that load into ``DEAD_HERBACEOUS`` before
    the Rothermel fuel-bed weighting stage.

    Operational semantics preserved here:

    - transferred dead herb uses live-herb SAV because the physical particle
      size does not change;
    - transferred dead herb uses dead-fuel heat/density/mineral properties;
    - its moisture is supplied later by ``RothermelFuelMoisture`` using the
      dead 1-h moisture convention;
    - the returned fuel is marked ``dynamic=False`` because redistribution has
      already been resolved for this moisture snapshot.
    """

    if not isinstance(fuel, RothermelFuelModel):
        raise TypeError("fuel must be RothermelFuelModel")
    if not isinstance(moisture, RothermelFuelMoisture):
        raise TypeError("moisture must be RothermelFuelMoisture")

    if not fuel.dynamic:
        return DynamicFuelTransferResult(
            fuel=fuel,
            transfer_fraction=0.0,
            transferred_load_kg_m2=0.0,
        )

    dead_herb = int(FuelClass.DEAD_HERBACEOUS)
    live_herb = int(FuelClass.LIVE_HERBACEOUS)
    dead_reference = int(FuelClass.DEAD_1H)

    if fuel.loads_kg_m2[dead_herb] != 0.0:
        raise ValueError(
            "a dynamic fuel model must start with zero DEAD_HERBACEOUS load; "
            "that class is derived from live-herb curing"
        )

    transfer_fraction = compute_dynamic_herbaceous_transfer_fraction(
        moisture.live_herbaceous_fraction
    )
    live_load = fuel.loads_kg_m2[live_herb]
    transferred_load = live_load * transfer_fraction

    loads = list(fuel.loads_kg_m2)
    loads[dead_herb] = transferred_load
    loads[live_herb] = live_load - transferred_load

    sav = list(fuel.sav_ratio_m_inv)
    heat = list(fuel.heat_content_j_kg)
    density = list(fuel.particle_density_kg_m3)
    total_mineral = list(fuel.total_mineral_fraction)
    effective_mineral = list(fuel.effective_mineral_fraction)

    sav[dead_herb] = sav[live_herb]
    heat[dead_herb] = heat[dead_reference]
    density[dead_herb] = density[dead_reference]
    total_mineral[dead_herb] = total_mineral[dead_reference]
    effective_mineral[dead_herb] = effective_mineral[dead_reference]

    prepared = replace(
        fuel,
        loads_kg_m2=tuple(loads),
        sav_ratio_m_inv=tuple(sav),
        heat_content_j_kg=tuple(heat),
        particle_density_kg_m3=tuple(density),
        total_mineral_fraction=tuple(total_mineral),
        effective_mineral_fraction=tuple(effective_mineral),
        dynamic=False,
    )
    return DynamicFuelTransferResult(
        fuel=prepared,
        transfer_fraction=transfer_fraction,
        transferred_load_kg_m2=transferred_load,
    )
