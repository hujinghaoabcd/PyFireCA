import importlib.util
import sys
from pathlib import Path

import pytest

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


def test_heading_sweep_preserves_square_lattice_symmetry() -> None:
    benchmark = _load_benchmark_module()
    results = benchmark.run_heading_sweep(
        headings_deg=(0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0),
        shape=(11, 11),
        cell_size_m=30.0,
    )
    indexed = {(result.neighborhood, result.head_direction_deg): result for result in results}

    for neighborhood in ("VN4", "Moore8"):
        for first, reflected in ((0.0, 90.0), (15.0, 75.0), (30.0, 60.0)):
            first_metrics = indexed[(neighborhood, first)].metrics
            reflected_metrics = indexed[(neighborhood, reflected)].metrics
            assert first_metrics.mae_s == pytest.approx(reflected_metrics.mae_s, rel=1e-12)
            assert first_metrics.rmse_s == pytest.approx(reflected_metrics.rmse_s, rel=1e-12)


def test_cell_size_sweep_keeps_physical_half_extent_fixed() -> None:
    benchmark = _load_benchmark_module()
    results = benchmark.run_cell_size_sweep(
        cell_sizes_m=(10.0, 20.0, 30.0, 60.0),
        half_extent_m=60.0,
        head_direction_deg=30.0,
    )

    expected_shapes = {
        10.0: (13, 13),
        20.0: (7, 7),
        30.0: (5, 5),
        60.0: (3, 3),
    }
    assert len(results) == 8
    for result in results:
        assert result.shape == expected_shapes[result.cell_size_m]
        radius_cells = (result.shape[0] - 1) // 2
        assert radius_cells * result.cell_size_m == pytest.approx(60.0)


def test_centered_square_shape_rejects_inexact_extent() -> None:
    benchmark = _load_benchmark_module()

    with pytest.raises(ValueError, match="integer multiple"):
        benchmark.centered_square_shape(half_extent_m=100.0, cell_size_m=30.0)
