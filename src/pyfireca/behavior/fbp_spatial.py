"""Static spatially heterogeneous Canadian FBP directional edge provider."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from pyfireca.behavior.fbp import FBPInputs, FBPModel
from pyfireca.behavior.fbp_directional import HomogeneousFBPDirectionalSpreadRate
from pyfireca.neighborhood import Offset

FBPInputsProvider = Callable[[int, int], FBPInputs]


@dataclass(slots=True)
class StaticSpatialFBPDirectionalSpreadRate:
    """Provide source-cell directional FBP ROS for a heterogeneous static landscape.

    One :class:`HomogeneousFBPDirectionalSpreadRate` is calculated lazily and
    cached per source cell. All outgoing edges then reuse the same FBP behavior
    state and ellipse.

    The baseline edge semantic remains source-cell controlled; target-cell
    averaging is a separate modeling assumption and is not hidden here.
    """

    model: FBPModel
    inputs_provider: FBPInputsProvider
    _cell_providers: dict[tuple[int, int], HomogeneousFBPDirectionalSpreadRate] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.model, FBPModel):
            raise TypeError("model must be FBPModel")
        if not callable(self.inputs_provider):
            raise TypeError("inputs_provider must be callable")

    def _provider_at(self, row: int, col: int) -> HomogeneousFBPDirectionalSpreadRate:
        key = (row, col)
        cached = self._cell_providers.get(key)
        if cached is not None:
            return cached

        inputs = self.inputs_provider(row, col)
        if not isinstance(inputs, FBPInputs):
            raise TypeError(
                "inputs_provider must return FBPInputs; "
                f"got {type(inputs).__name__} at ({row}, {col})"
            )
        provider = HomogeneousFBPDirectionalSpreadRate(inputs=inputs, model=self.model)
        self._cell_providers[key] = provider
        return provider

    def spread_rate_m_s(self, row: int, col: int, offset: Offset) -> float:
        """Return FBP radial ROS for one outgoing source-cell edge."""

        return self._provider_at(row, col).spread_rate_m_s(row, col, offset)

    def clear_cache(self) -> None:
        """Discard cached source-cell FBP behavior states."""

        self._cell_providers.clear()

    @property
    def cached_cell_count(self) -> int:
        """Return the number of source cells evaluated so far."""

        return len(self._cell_providers)
