import numpy as np

from pyfireca.gis import RasterMetadata
from pyfireca.outputs import terminal_state_from_result
from pyfireca.simulator import StaticWildfireSimulationResult
from pyfireca.state import FireState


def _result() -> StaticWildfireSimulationResult:
    metadata = RasterMetadata(
        shape=(2, 3),
        crs="EPSG:32633",
        transform=(30.0, 0.0, 0.0, 0.0, -30.0, 60.0),
    )
    return StaticWildfireSimulationResult(
        arrival_times_s=np.array(
            [
                [0.0, 10.0, np.inf],
                [np.inf, 30.0, np.inf],
            ],
            dtype=np.float64,
        ),
        domain_mask=np.array(
            [
                [True, True, True],
                [False, True, False],
            ],
            dtype=bool,
        ),
        metadata=metadata,
        cell_size_m=30.0,
        runtime_s=0.1,
    )


def test_terminal_state_preserves_domain_and_reachability_semantics() -> None:
    state = terminal_state_from_result(_result())

    assert state.tolist() == [
        [
            int(FireState.BURNED),
            int(FireState.BURNED),
            int(FireState.UNBURNED),
        ],
        [
            int(FireState.UNBURNABLE),
            int(FireState.BURNED),
            int(FireState.UNBURNABLE),
        ],
    ]
