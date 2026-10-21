from __future__ import annotations

import pygame

import miniworlds.appearances.costume as costume_mod


class HexCostume(costume_mod.Costume):
    """Costume for actors on hex worlds.

    Actors placed on a hex tile are drawn as hexagons instead of
    rectangles. Actors on corners or edges keep the rectangular shape.
    """

    def _is_on_tile(self) -> bool:
        world = self.actor.world
        # Actors can move to other worlds after their costume was created
        # (e.g. widgets created while a HexWorld is running are later added
        # to a toolbar or console). Only draw hexagons on hex worlds.
        return (
            world is not None
            and getattr(world, "is_hex", False)
            and world.is_tile(self.actor.position)
        )

    def _hex_points(self) -> list:
        width, height = self.parent.position_manager.get_size()
        return [
            (width / 2, 0),
            (width, height / 4),
            (width, 3 * height / 4),
            (width / 2, height),
            (0, 3 * height / 4),
            (0, height / 4),
        ]

    def _inner_shape(self) -> tuple:
        if self._is_on_tile():
            return pygame.draw.polygon, [self._hex_points(), 0]
        return super()._inner_shape()

    def _outer_shape(self) -> tuple:
        if self._is_on_tile():
            return pygame.draw.polygon, [self._hex_points(), self.border]
        return super()._outer_shape()
