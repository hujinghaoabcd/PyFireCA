import importlib.util
import sys
from pathlib import Path

from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood


def _load_benchmark_module():
    path = Path(__file__).resolve().parents[1] / "benchmarks" / "ca_discretization.py"
    spec = importlib.util.spec_from_file_location("pyfireca_ca_discretization_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load CA discretization benchmark module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_anisotropic_fm1_moore8_reduces_arrival_error_vs_vn4() -> None:
    benchmark = _load_benchmark_module()

    vn4 = benchmark.run_case(
        VonNeumannNeighborhood(),
        neighborhood_name="VN4",
        shape=(11, 11),
        cell_size_m=30.0,
        head_direction_deg=30.0,
    )
    moore8 = benchmark.run_case(
        MooreNeighborhood(),
        neighborhood_name="Moore8",
        shape=(11, 11),
        cell_size_m=30.0,
        head_direction_deg=30.0,
    )

    assert moore8.metrics.rmse_s < vn4.metrics.rmse_s
    assert moore8.metrics.mae_s < vn4.metrics.mae_s
