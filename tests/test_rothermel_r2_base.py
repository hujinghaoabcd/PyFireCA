import pytest

from pyfireca.behavior._rothermel_base import compute_base_spread_rate_m_s
from pyfireca.behavior._units import (
    btu_lb_to_j_kg,
    feet_to_metres,
    ft_inv_to_m_inv,
    lb_ft2_to_kg_m2,
    lb_ft3_to_kg_m3,
)
from pyfireca.behavior.rothermel import RothermelFuelModel, RothermelFuelMoisture

STANDARD_HEAT = tuple(btu_lb_to_j_kg(8000.0) for _ in range(6))
STANDARD_DENSITY = tuple(lb_ft3_to_kg_m3(32.0) for _ in range(6))
STANDARD_TOTAL_MINERAL = (0.0555,) * 6
STANDARD_EFFECTIVE_MINERAL = (0.01,) * 6


def _fm1() -> RothermelFuelModel:
    return RothermelFuelModel(
        code=1,
        depth_m=feet_to_metres(1.0),
        dead_moisture_of_extinction_fraction=0.12,
        loads_kg_m2=(lb_ft2_to_kg_m2(0.034), 0.0, 0.0, 0.0, 0.0, 0.0),
        sav_ratio_m_inv=(
            ft_inv_to_m_inv(3500.0),
            ft_inv_to_m_inv(109.0),
            ft_inv_to_m_inv(30.0),
            0.0,
            0.0,
            0.0,
        ),
        heat_content_j_kg=STANDARD_HEAT,
        particle_density_kg_m3=STANDARD_DENSITY,
        total_mineral_fraction=STANDARD_TOTAL_MINERAL,
        effective_mineral_fraction=STANDARD_EFFECTIVE_MINERAL,
    )


def _fm2(*, dynamic: bool = False) -> RothermelFuelModel:
    return RothermelFuelModel(
        code=2,
        depth_m=feet_to_metres(1.0),
        dead_moisture_of_extinction_fraction=0.15,
        loads_kg_m2=tuple(
            lb_ft2_to_kg_m2(value) for value in (0.092, 0.046, 0.023, 0.0, 0.023, 0.0)
        ),
        sav_ratio_m_inv=tuple(
            ft_inv_to_m_inv(value) for value in (3000.0, 109.0, 30.0, 1500.0, 1500.0, 1500.0)
        ),
        heat_content_j_kg=STANDARD_HEAT,
        particle_density_kg_m3=STANDARD_DENSITY,
        total_mineral_fraction=STANDARD_TOTAL_MINERAL,
        effective_mineral_fraction=STANDARD_EFFECTIVE_MINERAL,
        dynamic=dynamic,
    )


def _moisture() -> RothermelFuelMoisture:
    return RothermelFuelMoisture(
        dead_1h_fraction=0.05,
        dead_10h_fraction=0.05,
        dead_100h_fraction=0.05,
        live_herbaceous_fraction=1.0,
        live_woody_fraction=1.0,
    )


def test_typed_fm1_base_ros_matches_pinned_behave7_reference() -> None:
    observed = compute_base_spread_rate_m_s(_fm1(), _moisture())

    assert observed == pytest.approx(0.024733996158492002, rel=1e-13)


def test_typed_fm2_live_fuel_base_ros_matches_pinned_behave7_reference() -> None:
    observed = compute_base_spread_rate_m_s(_fm2(), _moisture())

    assert observed == pytest.approx(0.013305319151517395, rel=1e-13)


def test_dynamic_fuel_requires_explicit_load_transfer_before_base_ros() -> None:
    with pytest.raises(NotImplementedError, match="dynamic herbaceous"):
        compute_base_spread_rate_m_s(_fm2(dynamic=True), _moisture())
