import csv
import hashlib
from pathlib import Path

FIXTURE = Path(__file__).parent / "data" / "behave7_surface_reference.csv"
EXPECTED_SHA256 = "2c54aee4d10a5632a2197a53f2bcf1e96b1d4210b852fff931192052c1c2b303"


def test_behave7_surface_reference_snapshot_is_unchanged() -> None:
    """Protect the pinned upstream snapshot from accidental edits."""

    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_behave7_surface_reference_has_expected_schema_and_rows() -> None:
    with FIXTURE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    assert len(rows) == 8
    assert rows[0]["fuelModelNumber"] == "124"
    assert rows[0]["spreadRate"] == "19.677584"

    nonburnable = [row for row in rows if row["fuelModelNumber"] == "91"]
    assert len(nonburnable) == 1
    assert nonburnable[0]["spreadRate"] == "0.0"
