import pytest

from pyfireca.arrival import ConstantDirectionalSpreadRate, StaticArrivalTimeSolver
from pyfireca.neighborhood import MooreNeighborhood, VonNeumannNeighborhood


def test_immediate_moore_and_von_neumann_neighborhoods_remain_supported() -> None:
    for neighborhood in (MooreNeighborhood(), VonNeumannNeighborhood()):
        solver = StaticArrivalTimeSolver(
            neighborhood=neighborhood,
            cell_size_m=30.0,
            spread_rate_provider=ConstantDirectionalSpreadRate(0.1),
        )
        assert solver.neighborhood is neighborhood


@pytest.mark.parametrize(
    "neighborhood",
    [MooreNeighborhood(radius=2), VonNeumannNeighborhood(radius=2)],
)
def test_long_range_offsets_fail_until_intermediate_cell_semantics_exist(
    neighborhood: object,
) -> None:
    with pytest.raises(ValueError, match="intermediate-cell traversal semantics"):
        StaticArrivalTimeSolver(
            neighborhood=neighborhood,  # type: ignore[arg-type]
            cell_size_m=30.0,
            spread_rate_provider=ConstantDirectionalSpreadRate(0.1),
        )
