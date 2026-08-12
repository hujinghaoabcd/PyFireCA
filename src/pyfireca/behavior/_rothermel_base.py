"""Typed assembly of the no-wind/no-slope Rothermel reference chain."""

from __future__ import annotations

from dataclasses import dataclass

from pyfireca.behavior._rothermel_dynamic import apply_dynamic_herbaceous_transfer
from pyfireca.behavior._rothermel_equations import (
    compute_heat_sink_j_m3,
    compute_live_moisture_of_extinction,
    compute_mineral_damping,
    compute_moisture_damping,
    compute_no_wind_no_slope_spread_rate_m_s,
    compute_preignition_heat_term_j_kg,
    compute_propagating_flux,
    compute_reaction_intensity_w_m2,
    compute_reaction_velocity_per_min,
    compute_size_sorted_weighted_combustible_load,
)
from pyfireca.behavior.rothermel import (
    RothermelFuelModel,
    RothermelFuelMoisture,
    compute_bulk_density_kg_m3,
    compute_characteristic_sav_m_inv,
    compute_optimum_packing_ratio,
    compute_packing_ratio,
    compute_surface_area_weights,
)


@dataclass(frozen=True, slots=True)
class BaseSpreadResult:
    """Validated base quantities needed by later Rothermel wind/slope stages."""

    spread_rate_m_s: float
    reaction_intensity_w_m2: float
    characteristic_sav_m_inv: float
    packing_ratio: float
    optimum_packing_ratio: float
    relative_packing_ratio: float
    propagating_flux: float
    heat_sink_j_m3: float
    dynamic_herbaceous_transfer_fraction: float = 0.0
    dynamic_herbaceous_transferred_load_kg_m2: float = 0.0


def _weighted(values: tuple[float, ...], weights: tuple[float, ...]) -> float:
    return sum(value * weight for value, weight in zip(values, weights, strict=True))


def compute_base_spread_result(
    fuel: RothermelFuelModel,
    moisture: RothermelFuelMoisture,
) -> BaseSpreadResult:
    """Return prepared no-wind/no-slope Rothermel quantities.

    Dynamic herbaceous fuel models are first resolved into the same six-class
    static representation used by the validated R1/R2 chain. Wind, slope,
    crown fire, and spotting remain outside this assembler.
    """

    if not isinstance(fuel, RothermelFuelModel):
        raise TypeError("fuel must be RothermelFuelModel")
    if not isinstance(moisture, RothermelFuelMoisture):
        raise TypeError("moisture must be RothermelFuelMoisture")
    if not fuel.burnable:
        return BaseSpreadResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    dynamic_transfer = apply_dynamic_herbaceous_transfer(fuel, moisture)
    fuel = dynamic_transfer.fuel

    within, categories = compute_surface_area_weights(fuel)
    characteristic_sav = compute_characteristic_sav_m_inv(fuel)
    packing_ratio = compute_packing_ratio(fuel)
    optimum_packing_ratio = compute_optimum_packing_ratio(characteristic_sav)
    if optimum_packing_ratio <= 0.0:
        return BaseSpreadResult(
            0.0,
            0.0,
            characteristic_sav,
            packing_ratio,
            optimum_packing_ratio,
            0.0,
            0.0,
            0.0,
            dynamic_herbaceous_transfer_fraction=dynamic_transfer.transfer_fraction,
            dynamic_herbaceous_transferred_load_kg_m2=dynamic_transfer.transferred_load_kg_m2,
        )

    relative_packing_ratio = packing_ratio / optimum_packing_ratio
    reaction_velocity = compute_reaction_velocity_per_min(
        characteristic_sav,
        relative_packing_ratio,
    )
    moisture_values = moisture.as_six_class_values()

    dead_slice = slice(0, 4)
    live_slice = slice(4, 6)

    dead_loads = fuel.loads_kg_m2[dead_slice]
    live_loads = fuel.loads_kg_m2[live_slice]
    dead_sav = fuel.sav_ratio_m_inv[dead_slice]
    live_sav = fuel.sav_ratio_m_inv[live_slice]
    dead_weights = within[dead_slice]
    live_weights = within[live_slice]
    dead_moistures = moisture_values[dead_slice]
    live_moistures = moisture_values[live_slice]

    live_mx = compute_live_moisture_of_extinction(
        dead_loads,
        dead_sav,
        dead_moistures,
        live_loads,
        live_sav,
        fuel.dead_moisture_of_extinction_fraction,
    )

    dead_weighted_load = compute_size_sorted_weighted_combustible_load(
        dead_loads,
        dead_sav,
        dead_weights,
        fuel.total_mineral_fraction[dead_slice],
    )
    live_weighted_load = compute_size_sorted_weighted_combustible_load(
        live_loads,
        live_sav,
        live_weights,
        fuel.total_mineral_fraction[live_slice],
    )

    dead_heat = _weighted(fuel.heat_content_j_kg[dead_slice], dead_weights)
    live_heat = _weighted(fuel.heat_content_j_kg[live_slice], live_weights)
    dead_effective_mineral = _weighted(
        fuel.effective_mineral_fraction[dead_slice],
        dead_weights,
    )
    live_effective_mineral = _weighted(
        fuel.effective_mineral_fraction[live_slice],
        live_weights,
    )
    dead_moisture = _weighted(dead_moistures, dead_weights)
    live_moisture = _weighted(live_moistures, live_weights)

    dead_reaction = 0.0
    if categories[0] > 0.0 and dead_weighted_load > 0.0:
        dead_reaction = compute_reaction_intensity_w_m2(
            reaction_velocity,
            dead_weighted_load,
            dead_heat,
            compute_moisture_damping(
                dead_moisture,
                fuel.dead_moisture_of_extinction_fraction,
            ),
            compute_mineral_damping(dead_effective_mineral),
        )

    live_reaction = 0.0
    if categories[1] > 0.0 and live_weighted_load > 0.0:
        live_reaction = compute_reaction_intensity_w_m2(
            reaction_velocity,
            live_weighted_load,
            live_heat,
            compute_moisture_damping(live_moisture, live_mx),
            compute_mineral_damping(live_effective_mineral),
        )

    reaction_intensity = dead_reaction + live_reaction
    weighted_preignition_heat = 0.0
    for index in range(4):
        weighted_preignition_heat += (
            categories[0]
            * within[index]
            * compute_preignition_heat_term_j_kg(
                moisture_values[index],
                fuel.sav_ratio_m_inv[index],
            )
        )
    for index in range(4, 6):
        weighted_preignition_heat += (
            categories[1]
            * within[index]
            * compute_preignition_heat_term_j_kg(
                moisture_values[index],
                fuel.sav_ratio_m_inv[index],
            )
        )

    heat_sink = compute_heat_sink_j_m3(
        compute_bulk_density_kg_m3(fuel),
        weighted_preignition_heat,
    )
    propagating_flux = compute_propagating_flux(characteristic_sav, packing_ratio)
    spread_rate = compute_no_wind_no_slope_spread_rate_m_s(
        reaction_intensity,
        propagating_flux,
        heat_sink,
    )

    return BaseSpreadResult(
        spread_rate_m_s=spread_rate,
        reaction_intensity_w_m2=reaction_intensity,
        characteristic_sav_m_inv=characteristic_sav,
        packing_ratio=packing_ratio,
        optimum_packing_ratio=optimum_packing_ratio,
        relative_packing_ratio=relative_packing_ratio,
        propagating_flux=propagating_flux,
        heat_sink_j_m3=heat_sink,
        dynamic_herbaceous_transfer_fraction=dynamic_transfer.transfer_fraction,
        dynamic_herbaceous_transferred_load_kg_m2=dynamic_transfer.transferred_load_kg_m2,
    )


def compute_base_spread_rate_m_s(
    fuel: RothermelFuelModel,
    moisture: RothermelFuelMoisture,
) -> float:
    """Return Albini-adjusted no-wind/no-slope surface ROS in m/s."""

    return compute_base_spread_result(fuel, moisture).spread_rate_m_s
