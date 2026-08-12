import pytest

from pyfireca.behavior._rothermel_equations import (
    compute_combustible_load,
    compute_maximum_reaction_velocity_per_min,
    compute_mineral_damping,
    compute_moisture_damping,
    compute_reaction_velocity_exponent,
    compute_reaction_velocity_per_min,
)
from pyfireca.behavior._units import ft_inv_to_m_inv, lb_ft2_to_kg_m2

FM1_SIGMA_M_INV = ft_inv_to_m_inv(3500.0)
FM1_PACKING_RATIO = 0.034 / (1.0 * 32.0)
FM1_OPTIMUM_PACKING_RATIO = 3.348 / 3500.0**0.8189
FM1_RELATIVE_PACKING_RATIO = FM1_PACKING_RATIO / FM1_OPTIMUM_PACKING_RATIO


def test_fm1_combustible_load_matches_albini_adjustment() -> None:
    oven_dry_load_kg_m2 = lb_ft2_to_kg_m2(0.034)

    observed = compute_combustible_load(oven_dry_load_kg_m2, 0.0555)

    assert observed == pytest.approx(lb_ft2_to_kg_m2(0.032113), rel=1e-14)
    assert observed == pytest.approx(0.1567893986871689, rel=1e-14)


def test_fm1_mineral_damping_matches_operational_equation() -> None:
    assert compute_mineral_damping(0.01) == pytest.approx(
        0.4173969279093913,
        rel=1e-14,
    )


def test_fm1_dead_moisture_damping_matches_operational_equation() -> None:
    assert compute_moisture_damping(0.05, 0.12) == pytest.approx(
        0.5533564814814815,
        rel=1e-14,
    )


def test_moisture_damping_is_zero_at_or_above_extinction() -> None:
    assert compute_moisture_damping(0.12, 0.12) == 0.0
    assert compute_moisture_damping(0.20, 0.12) == 0.0
    assert compute_moisture_damping(0.0, 0.0) == 0.0


def test_fm1_albini_reaction_velocity_exponent_uses_inverse_feet() -> None:
    assert compute_reaction_velocity_exponent(FM1_SIGMA_M_INV) == pytest.approx(
        0.2086558654295252,
        rel=1e-14,
    )


def test_fm1_maximum_and_actual_reaction_velocity() -> None:
    assert compute_maximum_reaction_velocity_per_min(FM1_SIGMA_M_INV) == pytest.approx(
        16.18369682415168,
        rel=1e-14,
    )
    assert compute_reaction_velocity_per_min(
        FM1_SIGMA_M_INV,
        FM1_RELATIVE_PACKING_RATIO,
    ) == pytest.approx(14.201359906473266, rel=1e-14)


def test_r2_equations_define_zero_and_invalid_boundaries() -> None:
    assert compute_combustible_load(0.0, 0.0555) == 0.0
    assert compute_mineral_damping(0.0) == 0.0
    assert compute_reaction_velocity_exponent(0.0) == 0.0
    assert compute_maximum_reaction_velocity_per_min(0.0) == 0.0
    assert compute_reaction_velocity_per_min(FM1_SIGMA_M_INV, 0.0) == 0.0

    with pytest.raises(ValueError):
        compute_combustible_load(-1.0, 0.0555)
    with pytest.raises(ValueError):
        compute_combustible_load(1.0, 1.01)
    with pytest.raises(ValueError):
        compute_mineral_damping(-0.01)
    with pytest.raises(ValueError):
        compute_moisture_damping(-0.01, 0.12)
    with pytest.raises(ValueError):
        compute_reaction_velocity_exponent(-1.0)
    with pytest.raises(ValueError):
        compute_reaction_velocity_per_min(FM1_SIGMA_M_INV, -0.1)
