import pygame
import miniworlds.appearances.managers.transformations_manager as transformations_manager


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
        i = 0
        j = 0
        while i <= parent.height:
            pygame.draw.line(image, appearance._grid_color, (0, i), (self.get_width(), i), 1)
            i += parent.tile_size
        while j <= parent.width:
            pygame.draw.line(image, appearance._grid_color, (j, 0), (j, self.get_height()), 1)
            j += parent.tile_size

        return image
