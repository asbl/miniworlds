import pygame
import miniworlds.appearances.managers.transformations_manager as transformations_manager


class TextTransformationsCostumeManager(transformations_manager.TransformationsManager):
    def __init__(self, appearance):
        super().__init__(appearance)

        # Extend the transformation pipeline with the custom 'write_text' transformation
        self.transformations_pipeline.append({
            "key": "write_text",                  # Unique identifier for this transformation
            "func": self.transformation_write_text,  # Function to apply the transformation
            "attr": "text",                       # Attribute to check whether transformation should be applied
            "is_optional": False                  # Flag to mark whether transformation is optional
        })

    def transformation_write_text(self, image: pygame.Surface, appearance) -> pygame.Surface:
        """
        Applies text rendering to the surface using the font manager.

        This method assumes that `appearance.font_manager.transformation_write_text`
        handles rendering text to a new surface and returns it.

        Args:
            image (pygame.Surface): The input surface before rendering text.
            appearance: The appearance object containing rendering properties.

        Returns:
            pygame.Surface: The updated surface with text rendered.
        """
        # Ensure font_manager exists to avoid runtime errors
        if not hasattr(appearance, "font_manager"):
            raise AttributeError("Appearance is missing 'font_manager', which is required to render text.")

        # Render text using the font manager
        text_surf = appearance.font_manager.transformation_write_text(
            image,
            appearance,
            appearance.color
        )

        # Store the resulting surface and return it
        self.surface = text_surf
        return text_surf
