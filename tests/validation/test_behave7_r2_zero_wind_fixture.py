import csv
import hashlib
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "data" / "behave7_r2_zero_wind_zero_slope.csv"
EXPECTED_SHA256 = "3a9a264a4cf77b931cde36cdbabc9acab55a11aff495a97976e1d1476aba8983"


def _row() -> dict[str, str]:
    with FIXTURE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    return rows[0]


def test_behave7_r2_reference_snapshot_is_unchanged() -> None:
    """Protect the pinned external reference from accidental edits."""

    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_behave7_r2_reference_has_pinned_provenance_and_conditions() -> None:
    row = _row()

    assert row["case_id"] == "fm1_m5_zero_wind_zero_slope"
    assert row["evidence_grade"] == "B"
    assert row["behave_app_commit"] == "a3cfcd5903188d73445948af16644868225bb9d5"
    assert row["behave_core_commit"] == "29888c7ad364aa18cfb340f4c25a8e395f24260f"
    assert row["fuel_model_number"] == "1"
    assert float(row["midflame_wind_ft_min"]) == 0.0
    assert float(row["slope_percent"]) == 0.0


def test_behave7_r2_reference_spread_rate_unit_conversion_is_consistent() -> None:
    row = _row()
    spread_rate_chains_h = float(row["spread_rate_chains_h"])
    spread_rate_m_s = float(row["spread_rate_m_s"])

    assert spread_rate_chains_h == pytest.approx(4.4262698923571939, abs=1e-15)
    assert spread_rate_m_s == pytest.approx(spread_rate_chains_h * 20.1168 / 3600.0, abs=1e-15)


def test_behave7_r2_reference_contains_required_fm1_native_parameters() -> None:
    row = _row()

    assert float(row["fuel_bed_depth_ft"]) == 1.0
    assert float(row["dead_moisture_of_extinction_fraction"]) == 0.12
    assert float(row["heat_content_dead_btu_lb"]) == 8000.0
    assert float(row["fuel_load_1h_lb_ft2"]) == 0.034
    assert float(row["savr_1h_ft_inv"]) == 3500.0
    assert float(row["total_mineral_fraction"]) == 0.0555
    assert float(row["effective_mineral_fraction"]) == 0.01
    assert float(row["particle_density_lb_ft3"]) == 32.0
