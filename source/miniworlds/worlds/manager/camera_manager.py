import pygame
from typing import Tuple, Set

import miniworlds.appearances.background as background
import miniworlds.actors.actor as actor_mod


class CameraManager(pygame.sprite.Sprite):
    """CameraManager defines a movable viewport into a 2D world and tracks visible actors."""

    def __init__(self, view_x: int, view_y: int, world):
        super().__init__()
        self.world = world

        # Viewport settings
        self.screen_topleft: Tuple[int, int] = (0, 0)  # Where the camera starts on the screen
        self._topleft: Tuple[int, int] = (0, 0)        # Camera top-left in world coordinates
        self._world_size_x = view_x
        self._world_size_y = view_y
        self.view: Tuple = (view_x, view_y)
        self._cached_rect = self.get_rect()
        self._cached_screen_rect = self.get_screen_rect()

        # Actor tracking
        self.view_actors_last_frame: Set = set()
        self._view_actors_actual_frame: Set = set()
        self._view_active_actors: Set = set()
        self._view_update_frame: int = -1

        # Resize flags
        self._resize = True
        self._disable_resize = False
        self._strict = True  # Constrain camera inside world
        self.dirty = False
        

    # --- Resize Control ---
    def disable_resize(self):
        self._disable_resize = True

    def enable_resize(self):
        self._disable_resize = False
        self.reload_camera()

    # --- Properties ---
    @property
    def width(self) -> int:
        return self.view[0]

    @width.setter
    def width(self, value: int):
        self._set_width(value)

    def _set_width(self, value: int):
        if value > self._world_size_x:
            self._world_size_x = value
        self.view = (value, self.view[1])
        self._resize = True
        self.dirty = True
        self.reload_camera()

    @property
    def height(self) -> int:
        return self.view[1]

    @height.setter
    def height(self, value: int):
        self._set_height(value)

    def _set_height(self, value: int):
        if value > self._world_size_y:
            self._world_size_y = value
        self.view = (self.view[0], value)
        self._resize = True
        self.dirty = True
        self.reload_camera()

    @property
    def world_size_x(self) -> int:
        return self._world_size_x

    @world_size_x.setter
    def world_size_x(self, value: int):
        self.view = (min(self.view[0], value), self.view[1])
        self._world_size_x = value
        self.dirty = True
        self.reload_camera()

    @property
    def world_size_y(self) -> int:
        return self._world_size_y

    @world_size_y.setter
    def world_size_y(self, value: int):
        self.view = (self.view[0], min(self.view[1], value))
        self._world_size_y = value
        self.dirty = True
        self.reload_camera()

    @property
    def world_size(self) -> Tuple[int, int]:
        return self._world_size_x, self._world_size_y

    @world_size.setter
    def world_size(self, value: Tuple[int, int]):
        self._world_size_x, self._world_size_y = value

    # --- Camera Position ---
    @property
    def x(self) -> int:
        return self._topleft[0]

    @x.setter
    def x(self, value: int):
        self.topleft = (value, self._topleft[1])
        self.dirty = True

    @property
    def y(self) -> int:
        return self._topleft[1]

    @y.setter
    def y(self, value: int):
        self.topleft = (self._topleft[0], value)
        self.dirty = True

    @property
    def topleft(self) -> Tuple[int, int]:
        return self._topleft

    @topleft.setter
    def topleft(self, value: Tuple[int, int]):
        self._set_topleft(value)

    def _set_topleft(self, value: Tuple[int, int]):
        if self._strict:
            value = (self._limit_x(value[0]), self._limit_y(value[1]))
        if value != self._topleft:
            self._topleft = value
            self.reload_actors_in_view()
        self.dirty = True

    def _limit_x(self, value: int) -> int:
        return max(0, min(value, self._world_size_x - self.view[0]))

    def _limit_y(self, value: int) -> int:
        return max(0, min(value, self._world_size_y - self.view[1]))

    # --- Geometry Helpers ---
    @property
    def rect(self) -> pygame.Rect:
        if self.dirty:
            return self.get_rect()
        else:
            return self._cached_rect

    @property
    def screen_rect(self) -> pygame.Rect:
        if self.dirty:
            return self.get_screen_rect()
        else:
            return self._cached_screen_rect


    def cache_rects(self):
        self._cached_rect = self.get_rect()
        self._cached_screen_rect = self.get_screen_rect()

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(*self._topleft, *self.view)

    def get_screen_rect(self) -> pygame.Rect:
        return pygame.Rect(*self.screen_topleft, *self.view)

    def get_screen_position(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """Converts global world position to screen position."""
        return (
            self.screen_topleft[0] + pos[0] - self._topleft[0],
            self.screen_topleft[1] + pos[1] - self._topleft[1]
        )

    def get_local_position(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        return pos[0] - self._topleft[0], pos[1] - self._topleft[1]

    def get_global_coordinates_for_world(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        return pos[0] + self._topleft[0], pos[1] + self._topleft[1]

    # --- Actor Handling ---
    def reload_actors_in_view(self):
        for actor in self.get_actors_in_view():
            actor.dirty = 1  # Mark for re-rendering

    def get_actors_in_view(self):
        # Collect all actors and compute their global rects only once
        actor_rect_pairs = [
            (actor, actor.position_manager.get_global_rect())
            for actor in self.world.actors
        ]

        # Keep only actors whose rects intersect with the current view rect
        current_frame_actors = {
            actor for actor, rect in actor_rect_pairs
            if self.rect.colliderect(rect)
        }

        # Update internal state as usual
        self.view_actors_last_frame = self._view_actors_actual_frame
        self._view_actors_actual_frame = current_frame_actors
        self._view_active_actors = current_frame_actors.union(self.view_actors_last_frame)
        self._view_update_frame = self.world.frame

        return self._view_active_actors

    def is_actor_in_view(self, actor: "actor_mod.Actor") -> bool:
        return actor.position_manager.get_global_rect().colliderect(self.rect)

    def is_actor_repainted(self, actor: "actor_mod.Actor") -> bool:
        return self.world.frame == 0 or self.is_actor_in_view(actor)

    def from_actor(self, actor: "actor_mod.Actor"):
        """Move camera to center on an actor."""
        if actor.center:
            center = actor.center
            self.topleft = (
                center[0] - self.view[0] // 2 - actor.width // 2,
                center[1] - self.view[1] // 2 - actor.height // 2
            )
        else:
            self.topleft = (0, 0)

    def is_in_screen(self, pixel: Tuple[int, int]) -> bool:
        return bool(pixel) and self.screen_rect.collidepoint(pixel)

    # --- Internal System Calls ---
    def reload_camera(self):
        """Reloads and possibly resizes the app view."""
        self.clear_camera_cache()
        if self._resize and not self._disable_resize:
            self.world.app.resize()
            self._resize = False
        self.world.background.set_dirty("all", background.Background.RELOAD_ACTUAL_IMAGE)

    def clear_camera_cache(self):
        """Reset the internal actor-view cache."""
        self._view_actors_actual_frame.clear()
        self._view_update_frame = -1

    def update(self):
        if self.dirty:
            self.cache_rects()
            self.dirty = False