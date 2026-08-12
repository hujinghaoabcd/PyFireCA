import pytest

from pyfireca.behavior import (
    RothermelFuelMoisture,
    RothermelInputs,
    RothermelModel,
    available_standard_fuel_model_numbers,
    get_standard_fuel_model,
    get_standard_fuel_model_record,
)
from pyfireca.behavior._units import ft_min_to_m_s

PINNED_BEHAVE_CORE = "29888c7ad364aa18cfb340f4c25a8e395f24260f"


def _static_moisture() -> RothermelFuelMoisture:
    return RothermelFuelMoisture(
        dead_1h_fraction=0.05,
        dead_10h_fraction=0.05,
        dead_100h_fraction=0.05,
        live_herbaceous_fraction=1.0,
        live_woody_fraction=1.0,
    )


def _compute_zero_wind_ros(number: int, moisture: RothermelFuelMoisture) -> float:
    result = RothermelModel().compute(
        RothermelInputs(
            fuel=get_standard_fuel_model(number),
            moisture=moisture,
            midflame_wind_speed_m_s=ft_min_to_m_s(0.0),
            wind_from_direction_deg=0.0,
            slope_deg=0.0,
            aspect_deg=0.0,
        )
    )
    return result.spread_rate_m_s


def test_catalogue_reports_only_currently_audited_models() -> None:
    assert available_standard_fuel_model_numbers() == (1, 2, 101)


def test_fm1_native_record_matches_pinned_behave_source() -> None:
    record = get_standard_fuel_model_record(1)

    assert record.code == "FM1"
    assert record.source_commit == PINNED_BEHAVE_CORE
    assert record.depth_ft == 1.0
    assert record.dead_moisture_of_extinction_fraction == 0.12
    assert record.dead_1h_load_lb_ft2 == 0.034
    assert record.dead_1h_sav_ft_inv == 3500.0
    assert record.dynamic is False


def test_fm2_native_record_matches_pinned_behave_source() -> None:
    record = get_standard_fuel_model_record(2)

    assert record.code == "FM2"
    assert record.dead_1h_load_lb_ft2 == 0.092
    assert record.dead_10h_load_lb_ft2 == 0.046
    assert record.dead_100h_load_lb_ft2 == 0.023
    assert record.live_herbaceous_load_lb_ft2 == 0.023
    assert record.dead_1h_sav_ft_inv == 3000.0
    assert record.dynamic is False


def test_gr1_native_record_preserves_dynamic_scott_burgan_values() -> None:
    record = get_standard_fuel_model_record(101)

    assert record.code == "GR1"
    assert record.depth_ft == 0.4
    assert record.dead_moisture_of_extinction_fraction == 0.15
    assert record.dead_1h_load_lb_ft2 == pytest.approx(0.10 * 2000.0 / 43560.0)
    assert record.live_herbaceous_load_lb_ft2 == pytest.approx(0.30 * 2000.0 / 43560.0)
    assert record.dead_1h_sav_ft_inv == 2200.0
    assert record.live_herbaceous_sav_ft_inv == 2000.0
    assert record.dynamic is True


def test_catalogue_fm1_and_fm2_preserve_existing_grade_b_base_ros() -> None:
    moisture = _static_moisture()

    assert _compute_zero_wind_ros(1, moisture) == pytest.approx(
        0.024733996158492002,
        rel=1e-13,
    )
    assert _compute_zero_wind_ros(2, moisture) == pytest.approx(
        0.013305319151517395,
        rel=1e-13,
    )


def test_catalogue_gr1_preserves_dynamic_grade_b_reference() -> None:
    moisture = RothermelFuelMoisture(
        dead_1h_fraction=0.05,
        dead_10h_fraction=0.05,
        dead_100h_fraction=0.05,
        live_herbaceous_fraction=0.60,
        live_woody_fraction=0.90,
    )

    assert _compute_zero_wind_ros(101, moisture) == pytest.approx(
        0.003990911424818205,
        rel=1e-12,
    )


def test_catalogue_rejects_unknown_or_invalid_model_numbers() -> None:
    with pytest.raises(KeyError, match="has not been audited"):
        get_standard_fuel_model(3)
    with pytest.raises(TypeError, match="integer"):
        get_standard_fuel_model_record(True)
