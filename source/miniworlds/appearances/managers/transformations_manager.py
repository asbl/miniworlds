from collections import defaultdict
import pygame
from typing import TypedDict, Callable


class TransformationPipelineEntry(TypedDict):
    key: str
    func: Callable
    attr: str
    is_optional: bool


class TransformationsManager:

    def __init__(self, appearance):
        self.surface = None
        self.appearance = appearance
        self.reload_transformations = defaultdict(bool)

        self.cached_image = pygame.Surface((0, 0))
        self.cached_images = defaultdict(pygame.Surface)

        self.transformations_pipeline: list[TransformationPipelineEntry] = [
            {"key": "orientation", "func": self.transformation_set_orientation, "attr": "orientation", "is_optional": False},
            {"key": "texture", "func": self.transformation_texture, "attr": "_is_textured", "is_optional": False},
            {"key": "scale", "func": self.transformation_scale, "attr": "_is_scaled", "is_optional": False},
            {"key": "scale_to_width", "func": self.transformation_scale_to_width, "attr": "_is_scaled_to_width", "is_optional": False},
            {"key": "scale_to_height", "func": self.transformation_scale_to_height, "attr": "_is_scaled_to_height", "is_optional": False},
            {"key": "upscale", "func": self.transformation_upscale, "attr": "_is_upscaled", "is_optional": False},
            {"key": "flip", "func": self.transformation_flip, "attr": "_is_flipped", "is_optional": False},
            {"key": "coloring", "func": self.transformation_coloring, "attr": "coloring", "is_optional": False},
            {"key": "transparency", "func": self.transformation_transparency, "attr": "transparency", "is_optional": False},
            {"key": "draw_images", "func": self.transformation_draw_images, "attr": "draw_images", "is_optional": False},
            {"key": "draw_shapes", "func": self.transformation_draw_shapes, "attr": "draw_shapes", "is_optional": False},
            {"key": "rotate", "func": self.transformation_rotate, "attr": "_is_rotatable", "is_optional": False},
        ]

    def get_size(self):
        return self.appearance.parent.size

    def get_width(self):
        return self.get_size()[0]

    def get_height(self):
        return self.get_size()[1]

    def blit(self, image: "pygame.Surface"):
        """Helper function: creates a new surface with parent size and blits the transformed image to it."""
        self.surface = pygame.Surface(self.get_size(), pygame.SRCALPHA)
        if self.appearance._is_centered:
            x = (self.surface.get_width() - image.get_width()) / 2
            y = (self.surface.get_height() - image.get_height()) / 2
        else:
            x, y = 0, 0
        self.surface.blit(image, (x, y))

    def reset_reload_transformations(self):
        """Resets reload flags for all transformations — next image will be fully loaded from cache."""
        for key in self.reload_transformations.keys():
            self.reload_transformations[key] = False

    def process_transformation_pipeline(self, image: pygame.Surface, appearance) -> pygame.Surface:
        """Processes the image through the transformation pipeline, using cache when appropriate."""
        for entry in self.transformations_pipeline:
            key = entry["key"]
            func = entry["func"]
            attr = entry["attr"]

            should_apply = getattr(appearance, attr, False) and self.get_size() != (0, 0)

            if (
                key in self.reload_transformations
                and not self.reload_transformations[key]
                and key in self.cached_images
                and self.cached_images[key]
            ):
                if should_apply:
                    image = self.cached_images[key]  # Use cached version
            else:
                if should_apply and image.get_width() != 0 and image.get_height() != 0:
                    image = func(image, appearance)  # Apply transformation
                    self.cached_images[key] = image
        return image

    def flag_reload_actions_for_transformation_pipeline(self, transformation_string):
        """Flags all transformations starting from the given one to be reloaded."""
        reload = False
        for transformation in self.transformations_pipeline:
            key = transformation["key"]
            if key == transformation_string or transformation_string == "all":
                reload = True
            if reload:
                self.reload_transformations[key] = True
        if self.appearance.parent:
            self.appearance.parent.dirty = 1

    def transformation_texture(self, image, appearance):
        background = pygame.Surface((appearance.parent.width, appearance.parent.height))
        if appearance._texture_size[0] != 0:
            texture_width = appearance._texture_size[0]
        else:
            texture_width = appearance.parent.tile_size if hasattr(appearance.parent, "tile_size") and appearance.parent.tile_size != 1 else image.get_width()

        if appearance._texture_size[1] != 0:
            texture_height = appearance._texture_size[1]
        else:
            texture_height = appearance.parent.tile_size if hasattr(appearance.parent, "tile_size") and appearance.parent.tile_size != 1 else image.get_height()

        image = pygame.transform.scale(image, (texture_width, texture_height))
        background.fill((255, 255, 255))
        i, j, width, height = 0, 0, 0, 0
        while width < appearance.parent.width:
            while height < appearance.parent.height:
                width = i * texture_width
                height = j * texture_height
                j += 1
                background.blit(image, (width, height))
            j, height = 0, 0
            i += 1
        self.blit(background)
        return self.surface

    def transformation_upscale(self, image: pygame.Surface, appearance) -> pygame.Surface:
        if self.get_size() != (0, 0):
            scale_factor_x = self.get_width() / image.get_width()
            scale_factor_y = self.get_height() / image.get_height()
            scale_factor = min(scale_factor_x, scale_factor_y)
            new_width = int(image.get_width() * scale_factor)
            new_height = int(image.get_height() * scale_factor)
            image = pygame.transform.scale(image, (new_width, new_height))
        self.blit(image)
        return self.surface

    def transformation_scale(self, image: pygame.Surface, appearance) -> pygame.Surface:
        image = pygame.transform.scale(image, self.get_size())
        self.blit(image)
        return self.surface

    def transformation_scale_to_height(self, image: pygame.Surface, appearance) -> pygame.Surface:
        scale_factor = self.get_height() / image.get_height()
        new_width = int(image.get_width() * scale_factor)
        new_height = int(image.get_height() * scale_factor)
        image = pygame.transform.scale(image, (new_width, new_height))
        self.blit(image)
        return self.surface

    def transformation_scale_to_width(self, image: pygame.Surface, appearance) -> pygame.Surface:
        scale_factor = self.get_width() / image.get_width()
        new_width = int(image.get_width() * scale_factor)
        new_height = int(image.get_height() * scale_factor)
        image = pygame.transform.scale(image, (new_width, new_height))
        self.blit(image)
        return self.surface

    def transformation_rotate(self, image: pygame.Surface, appearance) -> pygame.Surface:
        if appearance.parent.direction != 0:
            rotated_image = pygame.transform.rotozoom(image, -appearance.parent.direction, 1)
            self.surface = rotated_image
            return rotated_image
        self.surface = image
        return image

    def transformation_set_orientation(self, image: pygame.Surface, appearance) -> pygame.Surface:
        if appearance.parent.orientation != 0:
            image = pygame.transform.rotate(image, -appearance.parent.orientation)
        return image

    def transformation_flip(self, image: pygame.Surface, appearance) -> pygame.Surface:
        flipped_image = pygame.transform.flip(image, appearance._is_flipped, False)
        self.blit(flipped_image)
        return self.surface

    def transformation_coloring(self, image: pygame.Surface, appearance) -> pygame.Surface:
        image = image.copy()
        parent_color = self.appearance.parent.fill_color
        image.fill(parent_color, None)
        self.surface = image
        return self.surface

    def transformation_transparency(self, image: pygame.Surface, appearance) -> pygame.Surface:
        image.set_alpha(appearance.alpha)
        self.surface = image
        return image

    def transformation_draw_images(self, image: pygame.Surface, appearance) -> pygame.Surface:
        for draw_action in appearance.draw_images:
            surface, rect = draw_action
            surface = pygame.transform.scale(surface, (rect[2], rect[3]))
            image.blit(surface, rect)
        self.surface = image
        return image

    def transformation_draw_shapes(self, image: pygame.Surface, appearance) -> pygame.Surface:
        for draw_action in appearance.draw_shapes:
            draw_action[0](image, *draw_action[1])
        self.surface = image
        return image

    @staticmethod
    def crop_image(self, image: pygame.Surface, parent, appearance) -> pygame.Surface:
        cropped_surface = pygame.Surface(self.get_size())
        cropped_surface.fill((255, 255, 255))
        cropped_surface.blit(image, (0, 0), (0, 0, self.get_size()))
        self.blit(cropped_surface)
        return self.surface
