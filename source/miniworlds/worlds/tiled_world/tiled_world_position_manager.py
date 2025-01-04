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
import miniworlds.base.exceptions as exceptions


class TiledWorldPositionManager(actor_position_manager.Positionmanager):
    def __init__(
        self,
        actor: "actor_mod.Actor",
        world: "tiled_world.TiledWorld",
        position: [int, int],
    ):
        super().__init__(actor, world, position)
        self._size = (1, 1)
        self._scaled_size = (1, 1)

    def get_global_rect(self):
        if self.actor.costume:
            rect = self.actor.costume.get_rect()
        else:
            rect = pygame.Rect(0, 0, self.get_size()[0], self.get_size()[1])
        if self.actor.world.is_tile(self.actor.position):
            rect.topleft = tile_mod.Tile.from_position(
                self.actor.position, self.actor.world
            ).to_pixel()
            return rect
        elif self.actor.world.is_corner(self.actor.position):
            rect.center = corner_mod.Corner.from_position(
                self.actor.position, self.actor.world
            ).to_pixel()
            return rect
        elif self.actor.world.is_edge(self.actor.position):
            rect.center = edge_mod.Edge.from_position(
                self.actor.position, self.actor.world
            ).to_pixel()
            return rect
        else:
            rect.topleft = (-self.get_size()[0], -self.get_size()[1])
        return rect

    def get_local_rect(self):
        rect = self.get_global_rect()
        # Move actor-rect to camera local coordinates, 
        # depending if actor is on a tile, edge or corner
        if self.actor.world.is_tile(self.actor.position):
            rect.topleft = self.actor.world.camera.get_local_position(
                    self.get_global_rect().topleft
                )
        elif self.actor.world.is_corner(self.actor.position):
            rect.center = self.actor.world.camera.get_local_position(
                    self.get_global_rect().topleft
                )
        elif self.actor.world.is_edge(self.actor.position):
            rect.center = self.actor.world.camera.get_local_position(
                    self.get_global_rect().topleft
                )
        return rect

    def get_size(self):
        if self.actor.world:
            return (
                self.actor.world.tile_size * self._scaled_size[0],
                self.actor.world.tile_size * self._scaled_size[1],
            )
        else:
            return 0

    def set_size(self, value: Union[int, Tuple], scale=True):
        if isinstance(value, int) or isinstance(value, float):  # convert int to tuple
            value = (value, value)
        if scale and value != self._scaled_size and self.actor.costume:
            self._scaled_size = value
            self.actor.costume.set_dirty("scale", costume.Costume.RELOAD_ACTUAL_IMAGE)

    def set_center(self, value):
        self.position = value

    def point_towards_position(self, destination) -> float:
        """
        Actor points towards a given position

        Args:
            destination: The position to which the actor should pointing

        Returns:
            The new direction

        """
        pos = self.actor.position
        x = destination[0] - pos[0]
        y = destination[1] - pos[1]
        if x != 0:
            m = y / x
            if x < 0:
                # destination is left
                self.actor.direction = math.degrees(math.atan(m)) - 90
            else:
                # destination is right
                self.actor.direction = math.degrees(math.atan(m)) + 90
            return self.actor.direction
        else:
            m = 0
            if destination[1] > self.actor.position[1]:
                self.actor.direction = 180
                return self.actor.direction
            else:
                self.actor.direction = 0
                return self.actor.direction

    def move_towards_position(self, position, distance=1):
        if self.actor.position == position:
            return self
        else:
            direction = self.direction_from_two_points(self.actor.position, position)
            self.set_direction(direction)
            self.move(distance)
            return self

    def store_origin(self):
        pass

    def restore_origin(self):
        pass
