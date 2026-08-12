"""Neighborhood definitions for raster cellular automata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

Offset = tuple[int, int]


class Neighborhood(Protocol):
    """Structural protocol for a raster CA neighborhood."""

    def offsets(self) -> tuple[Offset, ...]:
        """Return relative neighbor offsets, excluding the center cell."""
        ...


def _validate_radius(radius: int) -> None:
    if isinstance(radius, bool) or not isinstance(radius, int) or radius < 1:
        raise ValueError("radius must be a positive integer")


@dataclass(frozen=True, slots=True)
class MooreNeighborhood:
    """Square Chebyshev neighborhood around a raster cell.

    Parameters
    ----------
    radius
        Positive integer Chebyshev radius. ``radius=1`` yields the classic
        eight-neighbor Moore neighborhood.
    """

    radius: int = 1

    def __post_init__(self) -> None:
        _validate_radius(self.radius)

    def offsets(self) -> tuple[Offset, ...]:
        """Return unique relative neighbor offsets, excluding the center."""

        r = self.radius
        return tuple(
            (dy, dx)
            for dy in range(-r, r + 1)
            for dx in range(-r, r + 1)
            if not (dy == 0 and dx == 0)
        )


@dataclass(frozen=True, slots=True)
class VonNeumannNeighborhood:
    """Manhattan-distance neighborhood around a raster cell.

    Parameters
    ----------
    radius
        Positive integer Manhattan radius. ``radius=1`` yields the classic
        four-neighbor Von Neumann neighborhood.
    """

    radius: int = 1

    def __post_init__(self) -> None:
        _validate_radius(self.radius)

    def offsets(self) -> tuple[Offset, ...]:
        """Return unique relative neighbor offsets, excluding the center."""

        r = self.radius
        return tuple(
            (dy, dx)
            for dy in range(-r, r + 1)
            for dx in range(-r, r + 1)
            if (dy != 0 or dx != 0) and abs(dy) + abs(dx) <= r
        )


def valid_neighbor_indices(
    row: int,
    col: int,
    shape: tuple[int, int],
    offsets: tuple[Offset, ...],
) -> tuple[tuple[int, int], ...]:
    """Map relative offsets to in-bounds raster indices.

    The initial boundary policy is clipping: neighbors falling outside the
    raster are omitted. Periodic or padded boundary policies are intentionally
    deferred until a concrete scientific requirement appears.
    """

    height, width = shape
    if height < 1 or width < 1:
        raise ValueError("shape dimensions must be positive")
    if not (0 <= row < height and 0 <= col < width):
        raise IndexError(f"cell ({row}, {col}) is outside raster shape {shape}")

    neighbors: list[tuple[int, int]] = []
    for dy, dx in offsets:
        nr = row + dy
        nc = col + dx
        if 0 <= nr < height and 0 <= nc < width:
            neighbors.append((nr, nc))
    return tuple(neighbors)
