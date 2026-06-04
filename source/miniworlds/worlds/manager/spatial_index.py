from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Set, Tuple, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from miniworlds.actors.actor import Actor


Cell = Tuple[int, int]


class SpatialIndex:
    """Uniform-grid broad phase for actor rectangle and point queries."""

    def __init__(self, cell_size: int = 64) -> None:
        if cell_size <= 0:
            raise ValueError("cell_size must be greater than zero")
        self.cell_size = cell_size
        self._cells: DefaultDict[Cell, Set["Actor"]] = defaultdict(set)
        self._actor_cells: dict["Actor", frozenset[Cell]] = {}
        self._actor_bounds: dict["Actor", Tuple[int, int, int, int]] = {}

    def _bounds_for_rect(self, rect: pygame.Rect) -> Tuple[int, int, int, int]:
        left = rect.left // self.cell_size
        top = rect.top // self.cell_size
        right = (rect.right - 1 if rect.width > 0 else rect.left) // self.cell_size
        bottom = (rect.bottom - 1 if rect.height > 0 else rect.top) // self.cell_size
        return left, top, right, bottom

    def _cells_for_bounds(
        self, bounds: Tuple[int, int, int, int]
    ) -> frozenset[Cell]:
        left, top, right, bottom = bounds
        return frozenset(
            (x, y)
            for x in range(left, right + 1)
            for y in range(top, bottom + 1)
        )

    def _cells_for_rect(self, rect: pygame.Rect) -> frozenset[Cell]:
        return self._cells_for_bounds(self._bounds_for_rect(rect))

    def update(self, actor: "Actor", rect: pygame.Rect | None = None) -> None:
        if rect is None:
            rect = actor.position_manager.get_global_rect()

        new_bounds = self._bounds_for_rect(rect)
        if self._actor_bounds.get(actor) == new_bounds:
            return

        new_cells = self._cells_for_bounds(new_bounds)
        old_cells = self._actor_cells.get(actor, frozenset())

        for cell in old_cells - new_cells:
            actors = self._cells[cell]
            actors.discard(actor)
            if not actors:
                del self._cells[cell]
        for cell in new_cells - old_cells:
            self._cells[cell].add(actor)
        self._actor_cells[actor] = new_cells
        self._actor_bounds[actor] = new_bounds

    def remove(self, actor: "Actor") -> None:
        self._actor_bounds.pop(actor, None)
        for cell in self._actor_cells.pop(actor, frozenset()):
            actors = self._cells[cell]
            actors.discard(actor)
            if not actors:
                del self._cells[cell]

    def query_rect(self, rect: pygame.Rect) -> Set["Actor"]:
        actors: Set["Actor"] = set()
        for cell in self._cells_for_rect(rect):
            actors.update(self._cells.get(cell, ()))
        return actors

    def query_point(self, point: Tuple[float, float]) -> Set["Actor"]:
        cell = (int(point[0] // self.cell_size), int(point[1] // self.cell_size))
        return set(self._cells.get(cell, ()))

    def clear(self) -> None:
        self._cells.clear()
        self._actor_cells.clear()
        self._actor_bounds.clear()

    def __len__(self) -> int:
        return len(self._actor_cells)
