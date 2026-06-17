from typing import Optional, Union, TYPE_CHECKING
import pygame

import miniworlds.appearances.appearance as appear
import miniworlds.appearances.managers.transformations_costume_manager as transformations_costume_manager

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod


class Costume(appear.Appearance):
    """Appearance for an actor.

    A costume contains one or more images and defines how an actor looks. You
    can switch images in a costume to animate the actor.

    Args:
        actor: Optional actor to attach the costume to.
        source: Optional image path, surface, color tuple, or list of image
            sources.

    Examples:
        ::

            actor.add_costume("images/player.png")

            costume = Costume()
            costume.add_image("images/walk1.png")
            actor.add_costume(costume)

            costume = Costume(actor, "images/player.png")
    """

    _managed_creation_depth = 0

    def __init__(self, actor=None, source=None):
        if source is None and self._is_image_source(actor):
            source = actor
            actor = None
        super().__init__()
        self.parent = actor  #: the parent of a costume is the associated actor.
        self.actor = self.parent
        self._initial_source = source
        self._info_overlay = False # managed by property
        self._is_rotatable = False # managed by property in appearance
        self._fill_color = None # managed by property in appearance
        self._border_color = None # managed by property in appearance
        self.transformations_manager = (
            transformations_costume_manager.TransformationsCostumeManager(self)
        )

    @staticmethod
    def _is_image_source(value) -> bool:
        return type(value) in [str, pygame.Surface, tuple, list]

    @classmethod
    def create_managed(cls, actor):
        cls._managed_creation_depth += 1
        try:
            return cls(actor)
        finally:
            cls._managed_creation_depth -= 1

    @classmethod
    def _is_managed_creation(cls) -> bool:
        return getattr(cls, "_managed_creation_depth", 0) > 0

    def bind_to_actor(self, actor) -> None:
        self.parent = actor
        self.actor = actor

    def get_manager(self):
        """Return the owning costume manager of the actor."""
        return self.actor.costume_manager

    @property
    def world(self) -> "world_mod.World":
        """Owning world of this costume."""
        return self.parent.world

    def after_init(self):
        """Apply actor and world defaults after construction."""
        self._set_actor_default_values()
        if self.actor is not None:
            self._set_world_default_values()
        super().after_init()
        if self._initial_source is not None:
            if isinstance(self._initial_source, list):
                self.add_images(self._initial_source)
            else:
                self.add_image(self._initial_source)
        if self.actor is not None and not type(self)._is_managed_creation():
            self.actor.add_costume(self)

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
        """bool: Whether to draw a debug overlay around the actor.

        Examples:
            ::

                actor.costume.info_overlay = True
        """
        return self._info_overlay

    @info_overlay.setter
    def info_overlay(self, value):
        self._info_overlay = value
        self.set_dirty("all", Costume.RELOAD_ACTUAL_IMAGE)

    def set_image(self, source: Union[int, "appear.Appearance", tuple]) -> bool:
        """Select the active costume image.

        Args:
            source: Image index, appearance, or color tuple.

        Returns:
            `True` if the image exists.

        Examples:
            ::

                costume.set_image(0)
        """
        return super().set_image(source)

    def _inner_shape(self) -> tuple:
        """Return the inner costume shape.

        Returns:
            Draw function and rectangle arguments.
        """
        size = self.parent.position_manager.get_size()
        return pygame.draw.rect, [pygame.Rect(0, 0, size[0], size[1]), 0]

    def _outer_shape(self) -> tuple:
        """Return the outer costume shape.

        Returns:
            Draw function and rectangle arguments.
        """
        size = self.parent.position_manager.get_size()
        return pygame.draw.rect, [pygame.Rect(0, 0, size[0], size[1]), self.border]

    def rotated(self):
        """Mark rotation-dependent rendering as dirty after actor rotation."""
        if not self.actor._is_actor_repainted() or not self.is_rotatable:
            return
        frame = getattr(getattr(self.actor, "world", None), "frame", None)
        if (
            frame is not None
            and getattr(self, "_rotation_dirty_frame", None) == frame
            and self.dirty >= self.RELOAD_ACTUAL_IMAGE
        ):
            return
        self._rotation_dirty_frame = frame
        self.set_dirty("rotate", self.RELOAD_ACTUAL_IMAGE)

    def origin_changed(self):
        """Mark rendering as dirty after an origin change."""
        if self.actor._is_actor_repainted():
            self.set_dirty("origin_changed", self.RELOAD_ACTUAL_IMAGE)

    def resized(self):
        """Mark scaling-dependent rendering as dirty."""
        self.set_dirty("scale", self.RELOAD_ACTUAL_IMAGE)

    def visibility_changed(self):
        """Mark full rendering as dirty after visibility updates."""
        if self.actor._is_actor_repainted():
            self.set_dirty("all", self.RELOAD_ACTUAL_IMAGE)

    def set_dirty(self, value="all", status=1):
        """Set dirty flags and keep actor rect/mask caches in sync."""
        super().set_dirty(value, status)
        if hasattr(self, "_cached_rect"):
            self._cached_rect = (-1, self._cached_rect[1])
        if hasattr(self, "actor") and self.actor and hasattr(self.actor, "position_manager"):
            self.actor.position_manager._invalidate_rect_cache()
        if (
            hasattr(self, "actor")
            and self.actor
            and getattr(self.actor, "_static", False)
            and hasattr(self.actor.world, "_static_tile_layer_dirty")
        ):
            self.actor.world._static_tile_layer_dirty = True
        if (
            hasattr(self, "actor")
            and self.actor
            and self.actor.collision_type == "mask"
        ):
            self.actor.mask = pygame.mask.from_surface(self.actor.image, threshold=100)


    def get_rect(self):
        """Return a frame-cached local rect for the rendered costume image."""
        frame = self.actor.world.frame if self.actor else 0
        if frame == self._cached_rect[0]:
            return self._cached_rect[1]
        rect = self.image.get_rect()
        self._cached_rect = (frame, rect)
        return rect
