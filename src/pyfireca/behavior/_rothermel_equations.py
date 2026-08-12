"""Pure equation helpers for the Albini-adjusted Rothermel reference path.

This private module isolates formula-level calculations from typed public
inputs and from CA propagation. Public PyFireCA behavior APIs use SI units;
legacy-unit empirical correlations explicitly convert their inputs at the
formula boundary.
"""

from __future__ import annotations

from math import exp, isfinite

from pyfireca.behavior._units import m_inv_to_ft_inv


def _require_finite_nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")


def compute_combustible_load(
    oven_dry_load: float,
    total_mineral_fraction: float,
) -> float:
    """Return Albini-adjusted combustible/net load in the input load unit.

    Albini's operational adjustment treats the reported oven-dry fuel loading
    as including total mineral content and uses ``w_n = w_0 * (1 - S_T)``.
    The calculation is unit-preserving: kg/m² in gives kg/m² out, while a
    native-unit validation fixture may use lb/ft².
    """

    _require_finite_nonnegative("oven_dry_load", oven_dry_load)
    _require_finite_nonnegative("total_mineral_fraction", total_mineral_fraction)
    if total_mineral_fraction > 1.0:
        raise ValueError("total_mineral_fraction must be in [0, 1]")
    return oven_dry_load * (1.0 - total_mineral_fraction)


def compute_mineral_damping(effective_mineral_fraction: float) -> float:
    """Return the dimensionless mineral damping coefficient ``eta_S``.

    The operational relation is ``0.174 / S_e**0.19``, capped at 1. The
    singular near-zero denominator is guarded explicitly to match the pinned
    Behave operational path.
    """

    _require_finite_nonnegative("effective_mineral_fraction", effective_mineral_fraction)
    if effective_mineral_fraction > 1.0:
        raise ValueError("effective_mineral_fraction must be in [0, 1]")

    denominator = effective_mineral_fraction**0.19
    if denominator < 1e-6:
        return 0.0
    return min(1.0, 0.174 / denominator)


def compute_moisture_damping(
    moisture_fraction: float,
    moisture_of_extinction_fraction: float,
) -> float:
    """Return the dimensionless moisture damping coefficient ``eta_M``.

    Moisture at or above the applicable extinction moisture produces zero
    contribution. Below extinction, evaluate the Rothermel cubic polynomial
    with ``r = M / M_x``.
    """

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


def compute_reaction_velocity_exponent(characteristic_sav_m_inv: float) -> float:
    """Return Albini's dimensionless reaction-velocity exponent ``A``.

    The empirical correlation uses characteristic SAV in inverse feet:
    ``A = 133 * sigma**-0.7913``. PyFireCA accepts inverse metres and performs
    the conversion explicitly here.
    """

    _require_finite_nonnegative("characteristic_sav_m_inv", characteristic_sav_m_inv)
    if characteristic_sav_m_inv == 0.0:
        return 0.0
    sigma_ft_inv = m_inv_to_ft_inv(characteristic_sav_m_inv)
    return 133.0 * sigma_ft_inv**-0.7913


def compute_maximum_reaction_velocity_per_min(characteristic_sav_m_inv: float) -> float:
    """Return maximum reaction velocity ``Gamma_max`` in 1/min.

    The published correlation uses characteristic SAV in inverse feet.
    """

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
