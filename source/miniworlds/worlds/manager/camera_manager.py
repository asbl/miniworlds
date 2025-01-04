import pygame
from typing import Tuple

import miniworlds.appearances.background as background
import miniworlds.actors.actor as actor_mod


class CameraManager(pygame.sprite.Sprite):
    """Defines a camera which shows specific parts of a World."""

    def __init__(self, view_x, view_y, world):
        super().__init__()
        self.world = world
        self.screen_topleft = (0, 0) # topleft of screen position
        self._topleft = (0, 0) # topleft world coordinates
        self._world_size_x = view_x
        self._world_size_y = view_y
        self.view = view_x, view_y
        self.view_actors_last_frame: set = set()
        "CameraManager.view_actors_last_frame All actors which where in last frames view"
        self._view_actors_actual_frame: set = set()
        "CameraManager.view_actors_actual_frame All actors in current frame"
        self._view_active_actors: set = set()
        "CameraManager.active_view_actors Al actors in the last two frames (which could have moved)"
        self._view_update_frame: int = 0
        "CameraManager.view_update_frame The frame to which view_actors resolves."
        self._resize = True  # Should app be resized?
        self._strict = True
        self._disable_resize = False

    def disable_resize(self):
        self._disable_resize = True

    def enable_resize(self):
        self._disable_resize = False
        self.reload_camera()

    @property
    def width(self):
        """overwritten in TiledCameraManager"""
        return self.view[0]

    @width.setter
    def width(self, value):
        self._set_width(value)

    def _set_width(self, value):
        if value > self.world_size_x:
            self._world_size_x = value
        self.view = (value, self.view[1])
        self._resize = True
        self.reload_camera()

    @property
    def height(self):
        return self.view[1]

    @height.setter
    def height(self, value):
        self._set_height(value)

    def _set_height(self, value):
        if value > self.world_size_y:
            self._world_size_y = value
        self.view = (self.view[0], value)
        self._resize = True
        self.reload_camera()

    @property
    def world_size_x(self):
        return self._world_size_x

    @world_size_x.setter
    def world_size_x(self, value):
        # If world size > camera view, shrink view
        if value < self.view[0]:
            self.view = (value, self.view[1])
        # set world size
        self._world_size_x = value
        self.reload_camera()

    @property
    def world_size_y(self):
        return self._world_size_y

    @world_size_y.setter
    def world_size_y(self, value):
        # If world size > camera view, shrink view
        if value < self.view[1]:
            self.view = (self.view[0], value)
        # set world size
        self._world_size_y = value
        self.reload_camera()

    @property
    def world_size(self) -> Tuple[float, float]:
        return (self._world_size_x, self._world_size_y)

    @world_size.setter
    def world_size(self, value: Tuple[float, float]):
        self._world_size_x = value[0]
        self._world_size_y = value[1]

    def reload_camera(self):
        self.clear_camera_cache()
        if self._resize and not self._disable_resize:
            self.world.app.resize()
            self._resize = False
        self.world.background.set_dirty(
            "all", background.Background.RELOAD_ACTUAL_IMAGE
        )

    def clear_camera_cache(self):
        self._view_actors_actual_frame = set()
        self._view_update_frame = -1

    def get_screen_rect(self) -> pygame.Rect:
        return pygame.Rect(self.screen_topleft[0], self.screen_topleft[1], self.width, self.height)

    def get_screen_position(self, pos: tuple) -> pygame.Rect:
        """Gets screen position for a global position.

        Args:
            pos (tuple): The global position

        Returns:
            tuple: A local position
        """
        return self.screen_topleft[0] + pos[0] - self.topleft[0], self.screen_topleft[1] + pos[1] - self.topleft[1]

    def get_local_position(self, pos: tuple) -> tuple:
        """Gets local position defined by camera for a global position

        Args:
            pos (tuple): The global position

        Returns:
            tuple: A local position
        """
        return pos[0] - self.topleft[0], pos[1] - self.topleft[1]

    def get_global_coordinates_for_world(self, pos):
        """
        Gets global coordinates for window
        """
        return pos[0] + self.topleft[0], pos[1] + self.topleft[1]

    @property
    def x(self):
        """Sets the x-position of camera"""
        return self.topleft[0]

    @x.setter
    def x(self, value):
        self.topleft = value, self._topleft[1]
        self.reload_actors_in_view()

    @property
    def y(self):
        """Sets the y-position of camera"""
        return self.topleft[1]

    @y.setter
    def y(self, value):
        self.topleft = self._topleft[0], value
        self.reload_actors_in_view()

    def _limit_x(self, value):
        if value < 0:
            return 0
        elif value >= self.world_size_x - self.view[0]:
            return self.world_size_x - self.view[0]
        else:
            return value

    def _limit_y(self, value):
        if value < 0:
            return 0
        elif value >= self.world_size_y - self.view[1]:
            return self.world_size_y - self.view[1]
        else:
            return value

    @property
    def topleft(self):
        return self._topleft[0], self._topleft[1]

    @topleft.setter
    def topleft(self, value):
        self._set_topleft(value)

    def _set_topleft(self, value):
        old_topleft = self._topleft
        if self._strict:
            new_x = self._limit_x(value[0])
            new_y = self._limit_y(value[1])
            value = new_x, new_y
        self._topleft = value
        if old_topleft != self._topleft:
            self.reload_actors_in_view()

    @property
    def rect(self):
        return self.get_rect()

    def get_rect(self) -> pygame.Rect:
        """Gets rect of camera view."""
        return pygame.Rect(
            self.topleft[0],
            self.topleft[1],
            self.width,
            self.height,
        )

    def reload_actors_in_view(self) -> set:
        """called, when camera is moved"""
        actors_in_view = self.get_actors_in_view()
        for actor in actors_in_view:
            actor.dirty = 1
        del actors_in_view

    def get_actors_in_view(self) -> set:
        """gets all actors in view.
        This caches the actors per frame and is reloaded every frame.

        Returns:
            set: _description_
        """
        if self.world.frame == self._view_update_frame:
            # The method was called this frame - Load the stored actors
            found_actors = self._view_actors_actual_frame
        else:
            # The method was not called this frame. Load actors from last frame.
            found_actors = set()
            for actor in self.world.actors:
                # actor.rect is the _local(!) rect, so pygame.sprite.colliderect can't be used
                # This code snippet is checking if the rectangle of an actor in the world is colliding
                # with the rectangle of the camera's view.
                if self.is_actor_in_view(actor):
                    found_actors.add(actor)
            self.view_actors_last_frame = self._view_actors_actual_frame
            self._view_actors_actual_frame = found_actors
            # actors_in_frame_and_last_frame = found_actors.copy()
            found_actors.union(self.view_actors_last_frame)
            self._view_active_actors = found_actors.union(self.view_actors_last_frame)
            self._view_update_frame = self.world.frame
        return self._view_active_actors

    def from_actor(self, actor: "actor_mod.Actor") -> None:
        """Gets camera from actor center-position"""
        if actor.center:
            center = actor.center
            width = self.view[0] // 2
            height = self.view[1] // 2
            self.topleft = (
                center[0] - width - actor.width // 2,
                center[1] - height - actor.height // 2,
            )
        else:
            self.topleft = (0, 0)

    def is_actor_repainted(self, actor):
        """Actors are repainted in frame 0 so they get size, rect, ...."""
        return self.world.frame == 0 or self.is_actor_in_view(actor)

    def is_actor_in_view(self, actor):
        if actor.position_manager.get_global_rect().colliderect(self.rect):
            return True
        else:
            return False

    def is_in_screen(self, pixel):
        if not pixel:
            return False
        if self.get_screen_rect().collidepoint(pixel):
            return True
        else:
            return False
