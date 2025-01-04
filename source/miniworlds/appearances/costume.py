from typing import Union
import pygame

import miniworlds.appearances.appearance as appear
import miniworlds.appearances.managers.transformations_costume_manager as transformations_costume_manager
import miniworlds.worlds.world as world


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
        self.info_overlay = False
        self.is_rotatable = False
        self.fill_color = None
        self.border_color = None
        self.transformations_manager = (
            transformations_costume_manager.TransformationsCostumeManager(self)
        )

    @property
    def world(self) -> "world.World":
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
        if self.actor.world.default_fill_color:
            self.fill_color = self.world.default_fill_color
        if self.actor.world.default_is_filled:
            self._is_filled = self.world.default_is_filled
        if self.actor.world.default_stroke_color:
            self.border_color = self.world.default_stroke_color
        if self.actor.world.default_border_color:
            self.border_color = self.world.default_border_color
        if self.actor.world.default_border:
            self.border = self.actor.world.default_border

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
        if self.world.camera.is_actor_repainted(self.actor):
            self.set_dirty("rotate", self.RELOAD_ACTUAL_IMAGE)

    def origin_changed(self):
        if self.world.camera.is_actor_repainted(self.actor):
            self.set_dirty("origin_changed", self.RELOAD_ACTUAL_IMAGE)

    def resized(self):
        self.set_dirty("scale", self.RELOAD_ACTUAL_IMAGE)

    def visibility_changed(self):
        if self.world.camera.is_actor_repainted(self.actor):
            self.set_dirty("all", self.RELOAD_ACTUAL_IMAGE)

    def set_dirty(self, value="all", status=1):
        super().set_dirty(value, status)
        if (
            hasattr(self, "actor")
            and self.actor
            and self.actor.collision_type == "mask"
        ):
            self.actor.mask = pygame.mask.from_surface(self.actor.image, threshold=100)
