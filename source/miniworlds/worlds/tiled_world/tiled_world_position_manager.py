import math
from typing import Tuple, Union

import pygame

import miniworlds.actors.actor as actor_mod
import miniworlds.appearances.costume as costume
import miniworlds.worlds.manager.position_manager as actor_position_manager
import miniworlds.worlds.tiled_world.tiled_world as tiled_world


class TiledWorldPositionManager(actor_position_manager.Positionmanager):
    def __init__(
        self,
        actor: "actor_mod.Actor",
        world: "tiled_world.TiledWorld",
        position: Tuple[int, int],
    ):
        self._position = position
        super().__init__(actor, world, position)
        self._size: Tuple[int, int] = (1, 1)
        self._scaled_size: Tuple[int, int] = (1, 1)
        self._tiled_spatial_index_update()

    def _tiled_spatial_index_update(self):
        """Update the actor's position in the tiled spatial index."""
        tiled_spatial_index = getattr(self.actor.world, "_tiled_spatial_index", None)
        if tiled_spatial_index is not None and self.actor in self.actor.world.actors:
            tiled_spatial_index.update(self.actor)

    def get_global_rect(self) -> pygame.Rect:
        """Returns the global rect of the actor in the world space.

        This rect may lie outside the visible screen. The result is cached
        per frame (like in the base class); position changes invalidate the
        cache via `_invalidate_rect_cache`.

        Returns:
            pygame.Rect: A rect with the actor's global coordinates.
        """
        frame = self.actor.world.frame
        if frame == self._cached_global_rect[0]:
            return self._cached_global_rect[1]

        size = self.get_size()
        rect = (
            self.actor.costume.get_rect().copy()
            if self.actor.has_costume()
            else pygame.Rect(0, 0, *size)
        )

        position = self.actor.position
        tile_factory = self.actor.world.tile_factory

        if self.actor.world.is_tile(position):
            rect.topleft = tile_factory.tile_cls.from_position(
                position, self.actor.world
            ).to_pixel()
        elif self.actor.world.is_corner(position):
            rect.center = tile_factory.corner_cls.from_position(
                position, self.actor.world
            ).to_pixel()
        elif self.actor.world.is_edge(position):
            rect.center = tile_factory.edge_cls.from_position(
                position, self.actor.world
            ).to_pixel()
        else:
            rect.topleft = (-size[0], -size[1])

        self._cached_global_rect = (frame, rect)
        return rect

    def get_local_rect(self) -> pygame.Rect:
        """Returns the actor rect in camera-local coordinates.

        Cached per frame and camera position: the draw path reads the local
        rect several times per actor and frame, and the underlying global
        rect plus the camera offset recomputation dominated large scenes
        with a moving camera. Invalidated like the global rect via
        `_invalidate_rect_cache`, and by camera movement through the
        (frame, topleft) cache key.
        """
        world = self.actor.world
        camera = world.camera
        key = (world.frame, getattr(camera, "_topleft", None))
        if key == self._cached_local_rect[0]:
            return self._cached_local_rect[1]

        global_rect = self.get_global_rect().copy()

        if world.is_tile(self.actor.position):
            global_rect.topleft = camera.get_local_position(global_rect.topleft)
        else:
            global_rect.center = camera.get_local_position(global_rect.center)

        self._cached_local_rect = (key, global_rect)
        return global_rect

    def get_size(self) -> Tuple[int, int]:
        if self.actor.world:
            tile_size = self.actor.world.tile_size
            return tile_size * self._scaled_size[0], tile_size * self._scaled_size[1]
        return (0, 0)

    def set_size(self, value: Union[int, float, Tuple[int, int]], scale: bool = True):
        if isinstance(value, (int, float)):
            value = (value, value)

        if scale and value != self._scaled_size and self.actor.costume:
            self._scaled_size = value
            self.actor.costume.set_dirty("scale", costume.Costume.RELOAD_ACTUAL_IMAGE)

    @property
    def position(self) -> Tuple[float, float]:
        """Current tile, corner, or edge position."""
        return self._position

    @position.setter
    def position(self, value: Tuple[float, float]) -> None:
        """Override position setter to update tiled spatial index."""
        old_position = getattr(self, "_position", None)
        self._position = value
        if old_position is not None and old_position != value:
            self._tiled_spatial_index_update()

    def set_center(self, value: Tuple[int, int]):
        self.position = value

    def point_towards_position(self, destination: Tuple[float, float]) -> float:
        """Rotates the actor to face a specific destination position."""
        x_diff = destination[0] - self.actor.position[0]
        y_diff = destination[1] - self.actor.position[1]

        if x_diff != 0:
            angle = math.degrees(math.atan2(y_diff, x_diff))
            self.actor.direction = angle + 90
        else:
            self.actor.direction = 180 if y_diff > 0 else 0

        return self.actor.direction

    def move_towards_position(self, target: Tuple[int, int], distance: float = 1):
        if self.actor.position != target:
            direction = self.direction_from_two_points(self.actor.position, target)
            self.set_direction(direction)
            self.move(distance)
        return self

    def move_away_from_position(self, target: Tuple[int, int], distance: float = 1):
        if self.actor.position != target:
            direction = self.direction_from_two_points(target, self.actor.position)
            self.set_direction(direction)
            self.move(distance)
        return self

    def store_origin(self):
        """Overwrite base class"""
        pass

    def restore_origin(self):
        """Overwrite base class"""
        pass
