import pygame
import pygame

import miniworlds.appearances.managers.transformations_manager as transformations_manager
import miniworlds.worlds.hex_world.hex_coords as hex_coords


class TransformationsBackgroundManager(transformations_manager.TransformationsManager):
    def __init__(self, appearance):
        super().__init__(appearance)
        self.transformations_pipeline.extend([
            {"key": "grid", "func": self.transformation_grid, "attr": "grid", "is_optional": False},
        ])

    def get_size(self):
        size = (self.appearance.parent.camera.width, self.appearance.parent.camera.height)
        return size

    def transformation_grid(self, image: pygame.Surface, appearance) -> pygame.Surface:
        parent = self.appearance.parent
        if getattr(parent, "is_hex", False):
            return self._transformation_grid_hex(image, appearance)
        i = 0
        j = 0
        while i <= parent.height:
            pygame.draw.line(image, appearance._grid_color, (0, i), (self.get_width(), i), 1)
            i += parent.tile_size
        while j <= parent.width:
            pygame.draw.line(image, appearance._grid_color, (j, 0), (j, self.get_height()), 1)
            j += parent.tile_size

        return image

    def _transformation_grid_hex(self, image: pygame.Surface, appearance) -> pygame.Surface:
        parent = self.appearance.parent
        for position in parent.tiles:
            points = hex_coords.corner_pixel_points(position, parent.tile_size)
            pygame.draw.polygon(image, appearance._grid_color, points, 1)
        return image
