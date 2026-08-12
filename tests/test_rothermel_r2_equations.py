import pytest

from pyfireca.behavior._rothermel_equations import (
    compute_combustible_load,
    compute_effective_heating_number,
    compute_heat_of_preignition_j_kg,
    compute_heat_sink_j_m3,
    compute_live_moisture_of_extinction,
    compute_maximum_reaction_velocity_per_min,
    compute_mineral_damping,
    compute_moisture_damping,
    compute_no_wind_no_slope_spread_rate_m_s,
    compute_preignition_heat_term_j_kg,
    compute_propagating_flux,
    compute_reaction_intensity_w_m2,
    compute_reaction_velocity_exponent,
    compute_reaction_velocity_per_min,
)
from pyfireca.behavior._units import (
    btu_lb_to_j_kg,
    ft_inv_to_m_inv,
    lb_ft2_to_kg_m2,
    lb_ft3_to_kg_m3,
)

FM1_SIGMA_M_INV = ft_inv_to_m_inv(3500.0)
FM1_PACKING_RATIO = 0.034 / (1.0 * 32.0)
FM1_OPTIMUM_PACKING_RATIO = 3.348 / 3500.0**0.8189
FM1_RELATIVE_PACKING_RATIO = FM1_PACKING_RATIO / FM1_OPTIMUM_PACKING_RATIO
FM1_BEHAVE7_BASE_ROS_M_S = 0.024733996158492002


def test_fm1_combustible_load_matches_albini_adjustment() -> None:
    oven_dry_load_kg_m2 = lb_ft2_to_kg_m2(0.034)
    observed = compute_combustible_load(oven_dry_load_kg_m2, 0.0555)

    assert observed == pytest.approx(lb_ft2_to_kg_m2(0.032113), rel=1e-14)
    assert observed == pytest.approx(0.1567893986871689, rel=1e-14)


def test_fm1_mineral_damping_matches_operational_equation() -> None:
    assert compute_mineral_damping(0.01) == pytest.approx(0.4173969279093913, rel=1e-14)


def test_fm1_dead_moisture_damping_matches_operational_equation() -> None:
    assert compute_moisture_damping(0.05, 0.12) == pytest.approx(0.5533564814814815, rel=1e-14)


def test_moisture_damping_is_zero_at_or_above_extinction() -> None:
    assert compute_moisture_damping(0.12, 0.12) == 0.0
    assert compute_moisture_damping(0.20, 0.12) == 0.0
    assert compute_moisture_damping(0.0, 0.0) == 0.0


def test_fm2_live_moisture_of_extinction_matches_albini_operational_path() -> None:
    observed = compute_live_moisture_of_extinction(
        dead_loads=[lb_ft2_to_kg_m2(value) for value in (0.092, 0.046, 0.023)],
        dead_sav_m_inv=[ft_inv_to_m_inv(value) for value in (3000.0, 109.0, 30.0)],
        dead_moisture_fractions=[0.05, 0.05, 0.05],
        live_loads=[lb_ft2_to_kg_m2(0.023)],
        live_sav_m_inv=[ft_inv_to_m_inv(1500.0)],
        dead_moisture_of_extinction_fraction=0.15,
    )

    assert observed == pytest.approx(11.63009861291455, rel=1e-14)
    assert compute_moisture_damping(1.0, observed) == pytest.approx(0.812843639975883, rel=1e-14)


def test_live_moisture_of_extinction_is_bounded_by_dead_extinction() -> None:
    observed = compute_live_moisture_of_extinction(
        dead_loads=[lb_ft2_to_kg_m2(0.01)],
        dead_sav_m_inv=[ft_inv_to_m_inv(100.0)],
        dead_moisture_fractions=[0.15],
        live_loads=[lb_ft2_to_kg_m2(1.0)],
        live_sav_m_inv=[ft_inv_to_m_inv(1500.0)],
        dead_moisture_of_extinction_fraction=0.15,
    )

    assert observed == 0.15


def test_live_moisture_of_extinction_validates_sequence_shapes() -> None:
    with pytest.raises(ValueError, match="equal lengths"):
        compute_live_moisture_of_extinction(
            dead_loads=[1.0, 2.0],
            dead_sav_m_inv=[1.0],
            dead_moisture_fractions=[0.1, 0.1],
            live_loads=[1.0],
            live_sav_m_inv=[1.0],
            dead_moisture_of_extinction_fraction=0.15,
        )


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


def test_fm1_reaction_intensity_and_heat_transfer_intermediates() -> None:
    gamma = compute_reaction_velocity_per_min(FM1_SIGMA_M_INV, FM1_RELATIVE_PACKING_RATIO)
    net_load = compute_combustible_load(lb_ft2_to_kg_m2(0.034), 0.0555)
    eta_m = compute_moisture_damping(0.05, 0.12)
    eta_s = compute_mineral_damping(0.01)

    reaction_intensity = compute_reaction_intensity_w_m2(
        gamma,
        net_load,
        btu_lb_to_j_kg(8000.0),
        eta_m,
        eta_s,
    )
    propagating_flux = compute_propagating_flux(FM1_SIGMA_M_INV, FM1_PACKING_RATIO)
    heat_of_preignition = compute_heat_of_preignition_j_kg(0.05)
    effective_heating = compute_effective_heating_number(FM1_SIGMA_M_INV)
    heat_sink = compute_heat_sink_j_m3(
        lb_ft3_to_kg_m3(0.034),
        compute_preignition_heat_term_j_kg(0.05, FM1_SIGMA_M_INV),
    )

    assert reaction_intensity == pytest.approx(159495.8270605292, rel=1e-13)
    assert propagating_flux == pytest.approx(0.0577521709187699, rel=1e-14)
    assert heat_of_preignition == pytest.approx(711290.8, rel=1e-14)
    assert effective_heating == pytest.approx(0.9613386185824466, rel=1e-14)
    assert heat_sink == pytest.approx(372411.72862670355, rel=1e-13)


def test_fm1_dead_only_base_ros_matches_pinned_behave7_reference() -> None:
    gamma = compute_reaction_velocity_per_min(FM1_SIGMA_M_INV, FM1_RELATIVE_PACKING_RATIO)
    reaction_intensity = compute_reaction_intensity_w_m2(
        gamma,
        compute_combustible_load(lb_ft2_to_kg_m2(0.034), 0.0555),
        btu_lb_to_j_kg(8000.0),
        compute_moisture_damping(0.05, 0.12),
        compute_mineral_damping(0.01),
    )
    heat_sink = compute_heat_sink_j_m3(
        lb_ft3_to_kg_m3(0.034),
        compute_preignition_heat_term_j_kg(0.05, FM1_SIGMA_M_INV),
    )

    observed = compute_no_wind_no_slope_spread_rate_m_s(
        reaction_intensity,
        compute_propagating_flux(FM1_SIGMA_M_INV, FM1_PACKING_RATIO),
        heat_sink,
    )

    assert observed == pytest.approx(FM1_BEHAVE7_BASE_ROS_M_S, rel=1e-13)


def test_r2_equations_define_zero_and_invalid_boundaries() -> None:
    assert compute_combustible_load(0.0, 0.0555) == 0.0
    assert compute_mineral_damping(0.0) == 0.0
    assert compute_reaction_velocity_exponent(0.0) == 0.0
    assert compute_maximum_reaction_velocity_per_min(0.0) == 0.0
    assert compute_reaction_velocity_per_min(FM1_SIGMA_M_INV, 0.0) == 0.0
    assert compute_propagating_flux(0.0, FM1_PACKING_RATIO) == 0.0
    assert compute_effective_heating_number(0.0) == 0.0
    assert compute_heat_sink_j_m3(0.0, 1.0) == 0.0
    assert compute_no_wind_no_slope_spread_rate_m_s(1.0, 1.0, 0.0) == 0.0

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
    with pytest.raises(ValueError):
        compute_propagating_flux(FM1_SIGMA_M_INV, -0.1)
    with pytest.raises(ValueError):
        compute_heat_of_preignition_j_kg(-0.1)
    with pytest.raises(ValueError):
        compute_heat_sink_j_m3(-1.0, 1.0)
