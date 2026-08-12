import importlib.util
import sys
from pathlib import Path

import pytest


def _load_benchmark_module():
    path = Path(__file__).resolve().parents[1] / "benchmarks" / "edge_coupling.py"
    spec = importlib.util.spec_from_file_location("pyfireca_edge_coupling_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load edge-coupling benchmark module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(("left_fuel", "right_fuel"), [(1, 2), (2, 1)])
def test_half_cell_boundary_delta_matches_two_half_segment_equation(
    left_fuel: int,
    right_fuel: int,
) -> None:
    benchmark = _load_benchmark_module()
    result = benchmark.run_interface_case(left_fuel=left_fuel, right_fuel=right_fuel)

    expected_delta = 15.0 * (
        1.0 / result.target_rate_m_s - 1.0 / result.source_rate_m_s
    )
    observed_delta = (
        result.half_cell_boundary_arrival_s - result.source_only_boundary_arrival_s
    )

    assert observed_delta == pytest.approx(expected_delta, rel=1e-12)
    assert result.downstream_arrival_difference_s == pytest.approx(expected_delta, rel=1e-12)


def test_reversing_fuel_boundary_reverses_source_only_interface_bias() -> None:
    benchmark = _load_benchmark_module()
    fm1_to_fm2 = benchmark.run_interface_case(left_fuel=1, right_fuel=2)
    fm2_to_fm1 = benchmark.run_interface_case(left_fuel=2, right_fuel=1)

    assert fm1_to_fm2.downstream_arrival_difference_s == pytest.approx(
        -fm2_to_fm1.downstream_arrival_difference_s,
        rel=1e-12,
    )
    assert fm1_to_fm2.downstream_arrival_difference_s != pytest.approx(0.0)
