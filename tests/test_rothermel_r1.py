import pytest

from pyfireca.behavior._units import ft_inv_to_m_inv
from pyfireca.behavior.rothermel import (
    FuelClass,
    RothermelFuelModel,
    compute_bulk_density_kg_m3,
    compute_characteristic_sav_m_inv,
    compute_optimum_packing_ratio,
    compute_packing_ratio,
    compute_surface_area_weights,
)


def _weighted_test_fuel() -> RothermelFuelModel:
    return RothermelFuelModel(
        code=9001,
        depth_m=1.0,
        dead_moisture_of_extinction_fraction=0.20,
        loads_kg_m2=(1.0, 1.0, 0.0, 0.0, 1.0, 0.0),
        sav_ratio_m_inv=(100.0, 200.0, 0.0, 0.0, 400.0, 0.0),
        heat_content_j_kg=(18_000_000.0, 18_000_000.0, 0.0, 0.0, 18_000_000.0, 0.0),
        particle_density_kg_m3=(1000.0, 1000.0, 0.0, 0.0, 1000.0, 0.0),
        total_mineral_fraction=(0.05, 0.05, 0.0, 0.0, 0.05, 0.0),
        effective_mineral_fraction=(0.01, 0.01, 0.0, 0.0, 0.01, 0.0),
    )


def _nonburnable_test_fuel() -> RothermelFuelModel:
    zeros = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return RothermelFuelModel(
        code=99,
        depth_m=0.0,
        dead_moisture_of_extinction_fraction=0.0,
        loads_kg_m2=zeros,
        sav_ratio_m_inv=zeros,
        heat_content_j_kg=zeros,
        particle_density_kg_m3=zeros,
        total_mineral_fraction=zeros,
        effective_mineral_fraction=zeros,
        burnable=False,
    )


def test_surface_area_weights_separate_dead_and_live_categories() -> None:
    fuel = _weighted_test_fuel()

    within, categories = compute_surface_area_weights(fuel)

    assert within[FuelClass.DEAD_1H] == pytest.approx(1.0 / 3.0)
    assert within[FuelClass.DEAD_10H] == pytest.approx(2.0 / 3.0)
    assert within[FuelClass.DEAD_100H] == 0.0
    assert within[FuelClass.DEAD_HERBACEOUS] == 0.0
    assert within[FuelClass.LIVE_HERBACEOUS] == pytest.approx(1.0)
    assert within[FuelClass.LIVE_WOODY] == 0.0
    assert categories == pytest.approx((3.0 / 7.0, 4.0 / 7.0))


def test_characteristic_sav_uses_surface_area_weights() -> None:
    fuel = _weighted_test_fuel()

    assert compute_characteristic_sav_m_inv(fuel) == pytest.approx(300.0)


def test_packing_ratio_uses_particle_volume_and_fuel_depth() -> None:
    fuel = _weighted_test_fuel()

    assert compute_packing_ratio(fuel) == pytest.approx(0.003)


def test_bulk_density_uses_total_load_and_fuel_depth() -> None:
    fuel = _weighted_test_fuel()

    assert compute_bulk_density_kg_m3(fuel) == pytest.approx(3.0)


def test_optimum_packing_ratio_converts_characteristic_sav_to_inverse_feet() -> None:
    characteristic_sav_m_inv = ft_inv_to_m_inv(3500.0)

    assert compute_optimum_packing_ratio(characteristic_sav_m_inv) == pytest.approx(
        0.004193224627380653
    )


def test_nonburnable_fuel_returns_zero_derived_quantities() -> None:
    fuel = _nonburnable_test_fuel()

    within, categories = compute_surface_area_weights(fuel)

    assert within == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert categories == (0.0, 0.0)
    assert compute_characteristic_sav_m_inv(fuel) == 0.0
    assert compute_packing_ratio(fuel) == 0.0
    assert compute_bulk_density_kg_m3(fuel) == 0.0
    assert compute_optimum_packing_ratio(0.0) == 0.0


def test_optimum_packing_ratio_rejects_negative_characteristic_sav() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        compute_optimum_packing_ratio(-1.0)
