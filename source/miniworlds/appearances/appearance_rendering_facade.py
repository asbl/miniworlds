from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Union

import numpy
import pygame

import miniworlds.appearances.managers.image_manager as image_manager
import miniworlds.tools.binding as binding
import miniworlds.tools.color as color_mod
from miniworlds.base.exceptions import MiniworldsError

if TYPE_CHECKING:
    from miniworlds.appearances.appearance import Appearance


class AppearanceRenderingFacade:
    def __init__(self, owner: "Appearance"):
        self.owner = owner

    def _call_owner_override(self, method_name: str) -> bool:
        owner_method = type(self.owner).__dict__.get(method_name)
        if owner_method is None or type(self.owner).__name__ == "Appearance":
            return False
        owner_method(self.owner)
        return True

    def remove_last_image(self):
        self.owner.image_manager.remove_last_image()

    def add_image(self, source: Union[str, Tuple, pygame.Surface]) -> int:
        if type(source) not in [str, pygame.Surface, tuple]:
            raise MiniworldsError(
                f"Error: Image source has wrong format (expected str or pygame.Surface, got {type(source)}"
            )
        return self.owner.image_manager.add_image(source)

    def set_image(self, source: Union[int, "Appearance", tuple]) -> bool:
        if isinstance(source, int):
            return self.owner.image_manager.set_image_index(source)
        if type(source) == tuple:
            surface = image_manager.ImageManager.get_surface_from_color(source)
            self.owner.image_manager.replace_image(
                surface, image_manager.ImageManager.COLOR, source
            )

    def add_images(self, sources: list):
        assert isinstance(sources, list)
        for source in sources:
            self.add_image(source)

    def animate(self, loop: bool = False):
        self.owner._animation_start_frame = self.owner.world.frame
        self.owner.is_animated = True
        if loop:
            self.owner.loop = True

    def after_animation(self):
        pass

    def to_colors_array(self) -> numpy.ndarray:
        return pygame.surfarray.array3d(self.owner.image)

    def from_array(self, arr: numpy.ndarray):
        surf = pygame.surfarray.make_surface(arr)
        self.owner.image_manager.replace_image(
            surf, image_manager.ImageManager.SURFACE, None
        )

    def fill(self, value):
        self.owner._is_filled = value
        if self.owner.is_filled:
            self.owner.fill_color = color_mod.Color(value).get()
        self.owner.set_dirty("all", self.owner.RELOAD_ACTUAL_IMAGE)

    def set_filled(self, value):
        self.owner._is_filled = value

    def get_color(self, position):
        x = int(position[0])
        y = int(position[1])
        if 0 <= x < self.owner.image.get_width() and 0 <= y < self.owner.image.get_height():
            return self.owner.image.get_at((x, y))
        return None

    def get_rect(self):
        frame = self.owner.actor.world.frame
        if frame < self.owner._cached_rect[0]:
            return self.owner._cached_rect[1]
        rect = self.owner.image.get_rect()
        self.owner._cached_rect = (frame, rect)
        return rect

    def draw(self, source, position, width, height):
        if isinstance(source, str):
            self.draw_on_image(source, position, width, height)
        elif isinstance(source, tuple):
            self.draw_color_on_image(source, position, width, height)

    def draw_on_image(self, path, position, width, height):
        file = self.owner.image_manager.find_image_file(path)
        surface = self.owner.image_manager.load_image(file)
        self.draw_image_append(
            surface, pygame.Rect(position[0], position[1], width, height)
        )
        self.owner.set_dirty("draw_images", self.owner.RELOAD_ACTUAL_IMAGE)

    def draw_color_on_image(self, color, position, width, height):
        surface = pygame.Surface((width, height))
        surface.fill(color)
        self.draw_image_append(
            surface, pygame.Rect(position[0], position[1], width, height)
        )
        self.owner.set_dirty("draw_images", self.owner.RELOAD_ACTUAL_IMAGE)

    def to_string(self) -> str:
        return (
            self.owner.__class__.__name__
            + "with ID ["
            + str(self.owner.id)
            + "] for parent:["
            + str(self.owner.parent)
            + "], images: "
            + str(self.owner.image_manager.images_list)
        )

    def get_image(self):
        if (
            self.owner.dirty >= self.owner.RELOAD_ACTUAL_IMAGE
            and not self.owner._flag_transformation_pipeline
        ):
            self.owner.dirty = 0
            self.owner._flag_transformation_pipeline = True
            self.before_transformation_pipeline()
            image = self.owner.image_manager.load_image_from_image_index()
            image = self.owner.transformations_manager.process_transformation_pipeline(
                image, self.owner
            )
            self.after_transformation_pipeline()
            self.owner._flag_transformation_pipeline = False
            self.owner._image = image
        return self.owner._image

    def before_transformation_pipeline(self):
        self._call_owner_override("_before_transformation_pipeline")

    def after_transformation_pipeline(self) -> None:
        self._call_owner_override("_after_transformation_pipeline")

    def update(self):
        if self.owner.parent:
            self.load_image()
            return 1

    def load_image(self):
        if (
            self.owner.is_animated
            and self.owner._animation_start_frame != self.owner.world.frame
        ):
            if self.owner.world.frame != 0 and self.owner.world.frame % self.owner.animation_speed == 0:
                self.owner.image_manager.next_image()
        self.get_image()

    def register(self, method: callable):
        return binding.bind_method(self.owner, method)

    def draw_shape_append(self, shape, arguments):
        self.owner.draw_shapes.append((shape, arguments))

    def draw_shape_set(self, shape, arguments):
        self.owner.draw_shapes = [(shape, arguments)]

    def draw_image_append(self, surface, rect):
        self.owner.draw_images.append((surface, rect))

    def draw_image_set(self, surface, rect):
        self.owner.draw_images = [(surface, rect)]

    @property
    def dirty(self):
        return self.owner._dirty

    @dirty.setter
    def dirty(self, value):
        if value == 0:
            self.owner._dirty = 0
        else:
            self.set_dirty(value)

    def set_dirty(self, value="all", status=1):
        if self.owner.parent and hasattr(self.owner, "transformations_manager"):
            if value and self.owner.images and self.owner.get_manager()._is_display_initialized:
                if not self._call_owner_override("_update_draw_shape"):
                    self.update_draw_shape()
                self.owner.transformations_manager.flag_reload_actions_for_transformation_pipeline(
                    value
                )
            if status >= self.owner._dirty:
                self.owner._dirty = status
                self.owner.parent.dirty = 1

    def update_draw_shape(self) -> None:
        self.owner.draw_shapes = []
        if self.owner.parent and self.owner._inner_shape() and self.owner.image_manager:
            if self.owner._is_filled and not self.owner.image_manager.is_image():
                self.draw_shape_append(
                    self.owner._inner_shape()[0], self.owner._inner_shape_arguments()
                )
        if self.owner.parent and self.owner._outer_shape() and self.owner.border:
            self.draw_shape_append(
                self.owner._outer_shape()[0], self.owner._outer_shape_arguments()
            )

    def inner_shape(self) -> tuple:
        return pygame.draw.rect, [
            pygame.Rect(0, 0, self.owner.parent.size[0], self.owner.parent.size[1]),
            0,
        ]

    def outer_shape(self) -> tuple:
        return pygame.draw.rect, [
            pygame.Rect(0, 0, self.owner.parent.size[0], self.owner.parent.size[1]),
            self.owner.border,
        ]

    def inner_shape_arguments(self) -> List:
        color = self.owner.fill_color
        return [color] + self.owner._inner_shape()[1]

    def outer_shape_arguments(self) -> List:
        color = self.owner.border_color
        return [color] + self.owner._outer_shape()[1]