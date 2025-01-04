import pygame
import math
import miniworlds.appearances.managers.transformations_manager as transformations_manager


class TextTransformationsCostumeManager(transformations_manager.TransformationsManager):
    def __init__(self, appearance):
        super().__init__(appearance)
        self.transformations_pipeline.append(
            ("write_text", self.transformation_write_text, "text", False),
        )

    def transformation_write_text(self, image: pygame.Surface, appearance) -> pygame.Surface:
        text_surf = appearance.font_manager.transformation_write_text(image, appearance, appearance.color)
        self.surface = text_surf
        return text_surf

