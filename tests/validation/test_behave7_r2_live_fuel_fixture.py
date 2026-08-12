import csv
import hashlib
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "data" / "behave7_r2_live_fuel_zero_wind_zero_slope.csv"
EXPECTED_SHA256 = "68614947de592aebbce4d970aa64410c5712725a593d67f29d74af4761fc4240"


def _row() -> dict[str, str]:
    with FIXTURE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    return rows[0]


def test_behave7_live_fuel_reference_snapshot_is_unchanged() -> None:
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_behave7_live_fuel_reference_has_pinned_provenance_and_conditions() -> None:
    row = _row()

    assert row["case_id"] == "fm2_m5_live100_zero_wind_zero_slope"
    assert row["evidence_grade"] == "B"
    assert row["behave_app_commit"] == "a3cfcd5903188d73445948af16644868225bb9d5"
    assert row["behave_core_commit"] == "29888c7ad364aa18cfb340f4c25a8e395f24260f"
    assert row["fuel_model_number"] == "2"
    assert float(row["fuel_load_live_herb_lb_ft2"]) == 0.023
    assert float(row["midflame_wind_ft_min"]) == 0.0
    assert float(row["slope_percent"]) == 0.0


def test_behave7_live_fuel_reference_spread_rate_conversion_is_consistent() -> None:
    row = _row()
    spread_rate_chains_h = float(row["spread_rate_chains_h"])
    spread_rate_m_s = float(row["spread_rate_m_s"])

    assert spread_rate_chains_h == pytest.approx(2.3810521029916596, abs=1e-15)
    assert spread_rate_m_s == pytest.approx(spread_rate_chains_h * 20.1168 / 3600.0, abs=1e-15)


def test_behave7_live_fuel_reference_contains_operational_fm2_parameters() -> None:
    row = _row()

    assert float(row["fuel_bed_depth_ft"]) == 1.0
    assert float(row["dead_moisture_of_extinction_fraction"]) == 0.15
    assert float(row["fuel_load_1h_lb_ft2"]) == 0.092
    assert float(row["fuel_load_10h_lb_ft2"]) == 0.046
    assert float(row["fuel_load_100h_lb_ft2"]) == 0.023
    assert float(row["fuel_load_live_herb_lb_ft2"]) == 0.023
    assert float(row["savr_1h_ft_inv"]) == 3000.0
    assert float(row["savr_10h_ft_inv"]) == 109.0
    assert float(row["savr_100h_ft_inv"]) == 30.0
    assert float(row["savr_live_herb_ft_inv"]) == 1500.0
