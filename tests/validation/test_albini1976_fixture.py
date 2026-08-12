import csv
import hashlib
from pathlib import Path

FIXTURE = Path(__file__).parent / "data" / "albini1976_worked_examples.csv"
EXPECTED_SHA256 = "e8e3444d5bef61d1179c0a8ed402b505b5cf6e7eb9b5bb1c575e61c132c58e5a"


def test_albini1976_worked_example_snapshot_is_unchanged() -> None:
    """Protect the Grade A worked-example snapshot from accidental edits."""

    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_albini1976_worked_examples_match_documented_outputs() -> None:
    with FIXTURE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    assert len(rows) == 2

    level_ground = rows[0]
    assert level_ground["fuelModelNumber"] == "3"
    assert level_ground["wind20ftMph"] == "8"
    assert level_ground["slopePercent"] == "0"
    assert level_ground["expectedSpreadRateChainsPerHour"] == "97"
    assert level_ground["expectedFlameLengthFt"] == "12.5"

    calm_wind = rows[1]
    assert calm_wind["fuelModelNumber"] == "2"
    assert calm_wind["wind20ftMph"] == "0"
    assert calm_wind["slopePercent"] == "70"
    assert calm_wind["expectedSpreadRateChainsPerHour"] == "34"
    assert calm_wind["expectedFlameLengthFt"] == "6.2"
