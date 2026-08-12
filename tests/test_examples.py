import runpy
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


def test_static_raster_rothermel_example_runs() -> None:
    example = Path(__file__).resolve().parents[1] / "examples" / "static_raster_rothermel.py"
    output = StringIO()

    with redirect_stdout(output):
        runpy.run_path(str(example), run_name="__main__")

    rendered = output.getvalue()
    assert "Arrival time (s):" in rendered
    assert "FireState at 20 min:" in rendered
