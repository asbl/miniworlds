from typing import Union, TYPE_CHECKING
import pygame

import miniworlds.appearances.appearance as appear
import miniworlds.appearances.managers.transformations_costume_manager as transformations_costume_manager

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod


class Costume(appear.Appearance):
    """A costume contains one or multiple images

    Every actor has a costume which defines the "look" of the actor.
    You can switch the images in a costume to animate the actor.

    A costume is created if you add an image to an actor with actor.add_image(path_to_image)
    """

    def __init__(self, actor):
        super().__init__()
        self.parent = actor  #: the parent of a costume is the associated actor.
        self.actor = self.parent
        self._info_overlay = False # managed by property
        self._is_rotatable = False # managed by property in appearance
        self._fill_color = None # managed by property in appearance
        self._border_color = None # managed by property in appearance
        self.transformations_manager = (
            transformations_costume_manager.TransformationsCostumeManager(self)
        )

    def get_manager(self):
        return self.actor.costume_manager

    @property
    def world(self) -> "world_mod.World":
        return self.parent.world

    def after_init(self):
        # Called in metaclass
        self._set_default_color_values()
        super().after_init()

    def _set_default_color_values(self):
        self._set_actor_default_values()
        self._set_world_default_values()

    def _set_actor_default_values(self):
        self._info_overlay = False
        self._is_rotatable = True
        self.fill_color = (255, 0, 255, 255)
        self.border_color = (100, 100, 255)

    def _set_world_default_values(self):
        if self.actor.world.draw.default_fill_color:
            self.fill_color = self.world.draw.default_fill_color
        if self.actor.world.draw.default_is_filled:
            self._is_filled = self.world.draw.default_is_filled
        if self.actor.world.draw.default_stroke_color:
            self.border_color = self.world.draw.default_stroke_color
        if self.actor.world.draw.default_border_color:
            self.border_color = self.world.draw.default_border_color
        if self.actor.world.draw.default_border:
            self.border = self.actor.world.draw.default_border

    @property
    def info_overlay(self):
        """Shows info overlay (Rectangle around the actor and Direction marker)"""
        return self._info_overlay

    @info_overlay.setter
    def info_overlay(self, value):
        self._info_overlay = value
        self.set_dirty("all", Costume.RELOAD_ACTUAL_IMAGE)

    def set_image(self, source: Union[int, "appear.Appearance, tuple"]) -> bool:
        """
        :param source: index, Appearance or color.
        :return: True if image exists
        """
        return super().set_image(source)

    def _inner_shape(self) -> tuple:
        """Returns inner shape of costume

        Returns:
            pygame.Rect: Inner shape (Rectangle with size of actor)
        """
        size = self.parent.position_manager.get_size()
        return pygame.draw.rect, [pygame.Rect(0, 0, size[0], size[1]), 0]

    def _outer_shape(self) -> tuple:
        """Returns outer shape of costume

        Returns:
            pygame.Rect: Outer shape (Rectangle with size of actors without filling.)
        """
        size = self.parent.position_manager.get_size()
        return pygame.draw.rect, [pygame.Rect(0, 0, size[0], size[1]), self.border]

    def rotated(self):
        if self.actor._is_actor_repainted():
            self.set_dirty("rotate", self.RELOAD_ACTUAL_IMAGE)

    def origin_changed(self):
        if self.actor._is_actor_repainted():
            self.set_dirty("origin_changed", self.RELOAD_ACTUAL_IMAGE)

    def resized(self):
        self.set_dirty("scale", self.RELOAD_ACTUAL_IMAGE)

    def visibility_changed(self):
        if self.actor._is_actor_repainted():
            self.set_dirty("all", self.RELOAD_ACTUAL_IMAGE)

    def set_dirty(self, value="all", status=1):
        super().set_dirty(value, status)
        if (
            hasattr(self, "actor")
            and self.actor
            and self.actor.collision_type == "mask"
        ):
            self.actor.mask = pygame.mask.from_surface(self.actor.image, threshold=100)


    def get_rect(self):
        frame = self.actor.world.frame if self.actor else 0
        if frame < self._cached_rect[0]:
            return self._cached_rect[1]
        rect = self.image.get_rect()
        self._cached_rect = (frame, rect)
        return rect