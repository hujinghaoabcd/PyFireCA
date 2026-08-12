"""Pure equation helpers for the Albini-adjusted Rothermel reference path.

This private module isolates formula-level calculations from typed public
inputs and from CA propagation. Public PyFireCA behavior APIs use SI units;
legacy-unit empirical correlations explicitly convert their inputs at the
formula boundary.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import exp, isfinite, sqrt

from pyfireca.behavior._units import btu_lb_to_j_kg, m_inv_to_ft_inv


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")


def _require_unit_interval(name: str, value: float) -> None:
    _require_finite_nonnegative(name, value)
    if value > 1.0:
        raise ValueError(f"{name} must be in [0, 1]")


def _require_equal_lengths(name: str, *values: Sequence[float]) -> None:
    lengths = {len(value) for value in values}
    if len(lengths) > 1:
        raise ValueError(f"{name} sequences must have equal lengths")


def compute_combustible_load(
    oven_dry_load: float,
    total_mineral_fraction: float,
) -> float:
    """Return Albini-adjusted combustible/net load in the input load unit."""

    _require_finite_nonnegative("oven_dry_load", oven_dry_load)
    _require_unit_interval("total_mineral_fraction", total_mineral_fraction)
    return oven_dry_load * (1.0 - total_mineral_fraction)


def compute_size_sorted_weighted_combustible_load(
    loads: Sequence[float],
    sav_m_inv: Sequence[float],
    within_surface_area_weights: Sequence[float],
    total_mineral_fractions: Sequence[float],
) -> float:
    """Return operational size-bin-weighted combustible load.

    Rothermel/Behave groups fuel particles into five SAV classes before
    weighting net load. Bin boundaries are expressed in inverse feet:
    ``>=1200``, ``>=192``, ``>=96``, ``>=48``, and ``>=16``. Each particle's
    net load is multiplied by the summed within-life-state surface-area
    fraction of its SAV bin.

    The calculation is unit-preserving for fuel load.
    """

    _require_equal_lengths(
        "size-sorted fuel",
        loads,
        sav_m_inv,
        within_surface_area_weights,
        total_mineral_fractions,
    )

    bin_totals = [0.0] * 5
    particle_bins: list[int | None] = []
    for sav, weight in zip(sav_m_inv, within_surface_area_weights, strict=True):
        _require_finite_nonnegative("sav_m_inv", sav)
        _require_finite_nonnegative("within_surface_area_weight", weight)
        if weight > 1.0:
            raise ValueError("within_surface_area_weight must be in [0, 1]")

        sav_ft_inv = m_inv_to_ft_inv(sav) if sav > 0.0 else 0.0
        if sav_ft_inv >= 1200.0:
            bin_index = 0
        elif sav_ft_inv >= 192.0:
            bin_index = 1
        elif sav_ft_inv >= 96.0:
            bin_index = 2
        elif sav_ft_inv >= 48.0:
            bin_index = 3
        elif sav_ft_inv >= 16.0:
            bin_index = 4
        else:
            bin_index = None
        particle_bins.append(bin_index)
        if bin_index is not None:
            bin_totals[bin_index] += weight

    weighted_load = 0.0
    for load, mineral, bin_index in zip(
        loads,
        total_mineral_fractions,
        particle_bins,
        strict=True,
    ):
        _require_finite_nonnegative("load", load)
        _require_unit_interval("total_mineral_fraction", mineral)
        if bin_index is None:
            continue
        weighted_load += bin_totals[bin_index] * compute_combustible_load(load, mineral)
    return weighted_load


def compute_mineral_damping(effective_mineral_fraction: float) -> float:
    """Return the dimensionless mineral damping coefficient ``eta_S``."""

    _require_unit_interval("effective_mineral_fraction", effective_mineral_fraction)
    denominator = effective_mineral_fraction**0.19
    if denominator < 1e-6:
        return 0.0
    return min(1.0, 0.174 / denominator)


def compute_moisture_damping(
    moisture_fraction: float,
    moisture_of_extinction_fraction: float,
) -> float:
    """Return the dimensionless moisture damping coefficient ``eta_M``."""

    _require_finite_nonnegative("moisture_fraction", moisture_fraction)
    _require_finite_nonnegative(
        "moisture_of_extinction_fraction",
        moisture_of_extinction_fraction,
    )
    if moisture_of_extinction_fraction == 0.0:
        return 0.0
    if moisture_fraction >= moisture_of_extinction_fraction:
        return 0.0

    relative_moisture = moisture_fraction / moisture_of_extinction_fraction
    return (
        1.0 - 2.59 * relative_moisture + 5.11 * relative_moisture**2 - 3.52 * relative_moisture**3
    )


def compute_live_moisture_of_extinction(
    dead_loads: Sequence[float],
    dead_sav_m_inv: Sequence[float],
    dead_moisture_fractions: Sequence[float],
    live_loads: Sequence[float],
    live_sav_m_inv: Sequence[float],
    dead_moisture_of_extinction_fraction: float,
) -> float:
    """Return Albini-adjusted live-fuel moisture of extinction.

    Fine dead loading uses ``w * exp(-138 / sigma)`` while fine live loading
    uses ``w * exp(-500 / sigma)``, with SAV expressed in inverse feet. Load
    units cancel in the dead/live ratio.
    """

    _require_equal_lengths("dead fuel", dead_loads, dead_sav_m_inv, dead_moisture_fractions)
    _require_equal_lengths("live fuel", live_loads, live_sav_m_inv)
    _require_finite_nonnegative(
        "dead_moisture_of_extinction_fraction",
        dead_moisture_of_extinction_fraction,
    )
    if dead_moisture_of_extinction_fraction == 0.0:
        return 0.0

    fine_dead = 0.0
    weighted_dead_moisture = 0.0
    for load, sav, moisture in zip(
        dead_loads,
        dead_sav_m_inv,
        dead_moisture_fractions,
        strict=True,
    ):
        _require_finite_nonnegative("dead_load", load)
        _require_finite_nonnegative("dead_sav_m_inv", sav)
        _require_finite_nonnegative("dead_moisture_fraction", moisture)
        if sav == 0.0:
            continue
        weight = load * exp(-138.0 / m_inv_to_ft_inv(sav))
        fine_dead += weight
        weighted_dead_moisture += weight * moisture

    fine_dead_moisture = weighted_dead_moisture / fine_dead if fine_dead > 1e-7 else 0.0

    fine_live = 0.0
    for load, sav in zip(live_loads, live_sav_m_inv, strict=True):
        _require_finite_nonnegative("live_load", load)
        _require_finite_nonnegative("live_sav_m_inv", sav)
        if sav == 0.0:
            continue
        fine_live += load * exp(-500.0 / m_inv_to_ft_inv(sav))

    dead_over_live = fine_dead / fine_live if fine_live > 1e-7 else 0.0
    live_mx = (
        2.9 * dead_over_live * (1.0 - fine_dead_moisture / dead_moisture_of_extinction_fraction)
        - 0.226
    )
    return max(dead_moisture_of_extinction_fraction, live_mx)


def compute_reaction_velocity_exponent(characteristic_sav_m_inv: float) -> float:
    """Return Albini's dimensionless reaction-velocity exponent ``A``."""

    _require_finite_nonnegative("characteristic_sav_m_inv", characteristic_sav_m_inv)
    if characteristic_sav_m_inv == 0.0:
        return 0.0
    sigma_ft_inv = m_inv_to_ft_inv(characteristic_sav_m_inv)
    return 133.0 * sigma_ft_inv**-0.7913


def compute_maximum_reaction_velocity_per_min(characteristic_sav_m_inv: float) -> float:
    """Return maximum reaction velocity ``Gamma_max`` in 1/min."""

    _require_finite_nonnegative("characteristic_sav_m_inv", characteristic_sav_m_inv)
    if characteristic_sav_m_inv == 0.0:
        return 0.0
    sigma_ft_inv = m_inv_to_ft_inv(characteristic_sav_m_inv)
    sigma_power = sigma_ft_inv**1.5
    return sigma_power / (495.0 + 0.0594 * sigma_power)


def compute_reaction_velocity_per_min(
    characteristic_sav_m_inv: float,
    relative_packing_ratio: float,
) -> float:
    """Return actual reaction velocity ``Gamma`` in 1/min."""

    _require_finite_nonnegative("characteristic_sav_m_inv", characteristic_sav_m_inv)
    _require_finite_nonnegative("relative_packing_ratio", relative_packing_ratio)
    if characteristic_sav_m_inv == 0.0 or relative_packing_ratio == 0.0:
        return 0.0

    exponent = compute_reaction_velocity_exponent(characteristic_sav_m_inv)
    gamma_max = compute_maximum_reaction_velocity_per_min(characteristic_sav_m_inv)
    return (
        gamma_max
        * relative_packing_ratio**exponent
        * exp(exponent * (1.0 - relative_packing_ratio))
    )


def compute_reaction_intensity_w_m2(
    reaction_velocity_per_min: float,
    combustible_load_kg_m2: float,
    heat_content_j_kg: float,
    moisture_damping: float,
    mineral_damping: float,
) -> float:
    """Return one life-state reaction intensity contribution in W/m²."""

    _require_finite_nonnegative("reaction_velocity_per_min", reaction_velocity_per_min)
    _require_finite_nonnegative("combustible_load_kg_m2", combustible_load_kg_m2)
    _require_finite_nonnegative("heat_content_j_kg", heat_content_j_kg)
    _require_unit_interval("moisture_damping", moisture_damping)
    _require_unit_interval("mineral_damping", mineral_damping)
    return (
        reaction_velocity_per_min
        * combustible_load_kg_m2
        * heat_content_j_kg
        * moisture_damping
        * mineral_damping
        / 60.0
    )


def compute_propagating_flux(
    characteristic_sav_m_inv: float,
    packing_ratio: float,
) -> float:
    """Return the dimensionless propagating flux ratio ``xi``."""

    _require_finite_nonnegative("characteristic_sav_m_inv", characteristic_sav_m_inv)
    _require_finite_nonnegative("packing_ratio", packing_ratio)
    if characteristic_sav_m_inv == 0.0:
        return 0.0

    sigma_ft_inv = m_inv_to_ft_inv(characteristic_sav_m_inv)
    numerator = exp((0.792 + 0.681 * sqrt(sigma_ft_inv)) * (packing_ratio + 0.1))
    denominator = 192.0 + 0.2595 * sigma_ft_inv
    return numerator / denominator


def compute_heat_of_preignition_j_kg(moisture_fraction: float) -> float:
    """Return heat of preignition ``Q_ig`` in J/kg."""

    _require_finite_nonnegative("moisture_fraction", moisture_fraction)
    return btu_lb_to_j_kg(250.0 + 1116.0 * moisture_fraction)


def compute_effective_heating_number(sav_ratio_m_inv: float) -> float:
    """Return the dimensionless effective heating number for one fuel class."""

    _require_finite_nonnegative("sav_ratio_m_inv", sav_ratio_m_inv)
    if sav_ratio_m_inv == 0.0:
        return 0.0
    sav_ft_inv = m_inv_to_ft_inv(sav_ratio_m_inv)
    return exp(-138.0 / sav_ft_inv)


def compute_preignition_heat_term_j_kg(
    moisture_fraction: float,
    sav_ratio_m_inv: float,
) -> float:
    """Return ``Q_ig * epsilon`` for one fuel class in J/kg."""

    return compute_heat_of_preignition_j_kg(moisture_fraction) * compute_effective_heating_number(
        sav_ratio_m_inv
    )


def compute_heat_sink_j_m3(
    bulk_density_kg_m3: float,
    weighted_preignition_heat_j_kg: float,
) -> float:
    """Return fuel-bed heat sink in J/m³."""

    _require_finite_nonnegative("bulk_density_kg_m3", bulk_density_kg_m3)
    _require_finite_nonnegative(
        "weighted_preignition_heat_j_kg",
        weighted_preignition_heat_j_kg,
    )
    return bulk_density_kg_m3 * weighted_preignition_heat_j_kg


def compute_no_wind_no_slope_spread_rate_m_s(
    reaction_intensity_w_m2: float,
    propagating_flux: float,
    heat_sink_j_m3: float,
) -> float:
    """Return no-wind/no-slope surface spread rate in m/s."""

    _require_finite_nonnegative("reaction_intensity_w_m2", reaction_intensity_w_m2)
    _require_finite_nonnegative("propagating_flux", propagating_flux)
    _require_finite_nonnegative("heat_sink_j_m3", heat_sink_j_m3)
    if heat_sink_j_m3 == 0.0:
        return 0.0
    return reaction_intensity_w_m2 * propagating_flux / heat_sink_j_m3
