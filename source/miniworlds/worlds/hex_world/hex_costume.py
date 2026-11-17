from __future__ import annotations

import pygame

import miniworlds.appearances.costume as costume_mod


# RGB of the placeholder color every new costume starts with.
_PLACEHOLDER_RGB = (255, 0, 255)


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

    def _update_draw_shape(self) -> None:
        super()._update_draw_shape()
        current_image = self.image_manager.images_list[self.image_manager.image_index]
        if self._is_on_tile() and current_image["type"] == self.image_manager.COLOR:
            # Clear the rectangular color image, so that only the hexagon
            # remains visible.
            self.draw_shapes.insert(0, (pygame.Surface.fill, [(0, 0, 0, 0)]))
            if not self._is_filled and tuple(current_image["source"])[:3] != _PLACEHOLDER_RGB:
                # The color was set explicitly, e.g. with
                # `actor.add_costume((r, g, b))`, and no filled inner shape
                # is drawn. Redraw the color as a hexagon, otherwise the
                # actor would be invisible. The pink placeholder of an
                # actor without any costume stays outline-only.
                self.draw_shapes.insert(
                    1,
                    (
                        pygame.draw.polygon,
                        [current_image["source"], self._hex_points(), 0],
                    ),
                )

    def _inner_shape(self) -> tuple:
        if self._is_on_tile():
            return pygame.draw.polygon, [self._hex_points(), 0]
        return super()._inner_shape()

    def _outer_shape(self) -> tuple:
        if self._is_on_tile():
            return pygame.draw.polygon, [self._hex_points(), self.border]
        return super()._outer_shape()
