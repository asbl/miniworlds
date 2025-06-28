import math
import pygame
from typing import Tuple, Union

import miniworlds.worlds.manager.position_manager as actor_position_manager
import miniworlds.appearances.costume as costume
import miniworlds.worlds.tiled_world.tiled_world as tiled_world
import miniworlds.worlds.tiled_world.tile as tile_mod
import miniworlds.worlds.tiled_world.corner as corner_mod
import miniworlds.worlds.tiled_world.edge as edge_mod
import miniworlds.actors.actor as actor_mod


class TiledWorldPositionManager(actor_position_manager.Positionmanager):
    def __init__(
        self,
        actor: "actor_mod.Actor",
        world: "tiled_world.TiledWorld",
        position: Tuple[int, int],
    ):
        super().__init__(actor, world, position)
        self._size: Tuple[int, int] = (1, 1)
        self._scaled_size: Tuple[int, int] = (1, 1)

    def get_global_rect(self) -> pygame.Rect:
        """Returns the global rect of the actor in the world space.
        
        This rect may lie outside the visible screen.

        Returns:
            pygame.Rect: A rect with the actor's global coordinates.
        """
        size = self.get_size()
        rect = (
            self.actor.costume.get_rect()
            if self.actor.has_costume()
            else pygame.Rect(0, 0, *size)
        )

        position = self.actor.position

        if self.actor.world.is_tile(position):
            rect.topleft = tile_mod.Tile.from_position(position, self.actor.world).to_pixel()
        elif self.actor.world.is_corner(position):
            rect.center = corner_mod.Corner.from_position(position, self.actor.world).to_pixel()
        elif self.actor.world.is_edge(position):
            rect.center = edge_mod.Edge.from_position(position, self.actor.world).to_pixel()
        else:
            rect.topleft = (-size[0], -size[1])

        return rect

    def get_local_rect(self) -> pygame.Rect:
        global_rect = self.get_global_rect()
        local_pos = self.actor.world.camera.get_local_position(global_rect.topleft)

        if self.actor.world.is_tile(self.actor.position):
            global_rect.topleft = local_pos
        else:
            global_rect.center = local_pos

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

    def store_origin(self):
        """Overwrite base class"""
        pass

    def restore_origin(self):
        """Overwrite base class"""
        pass
