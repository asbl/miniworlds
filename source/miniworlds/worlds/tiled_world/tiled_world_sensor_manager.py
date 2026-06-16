import math
from typing import Optional, Tuple, Union

import miniworlds.actors.actor as actor_module
import miniworlds.worlds.manager.sensor_manager as worldsensor
import miniworlds.worlds.tiled_world.tile as tile_mod
import miniworlds.worlds.tiled_world.tiled_world as world_module


class TiledWorldSensorManager(worldsensor.SensorManager):
    """
    The TiledWorldConnector connects a actor to a tiled_world
    """

    def __init__(self, actor: "actor_module.Actor", world: "world_module.TiledWorld"):
        super().__init__(actor, world)
        self.actor.fps = actor.world.default_actor_speed

    @staticmethod
    def get_destination(start, direction, distance) -> Tuple[float, float]:
        x = start[0] + round(math.sin(math.radians(direction)) * distance)
        y = start[1] - round(math.cos(math.radians(direction)) * distance)
        return x, y

    def detect_borders(self, distance=0):
        """
        Checks if actor is touching borders

        Args:
            distance: If distance > 0, it will be checked, if the actor is touching borders, if moved two steps forward

        Returns: A List of touched borders, e.g. ["left", "top"]

        """
        target = self.get_destination(
            self.actor.position, self.actor.direction, distance
        )
        x, y = target
        borders = []
        if x <= 0:
            borders.append("left")
        if y + 1 >= self.world.world_size_y:
            borders.append("bottom")
        if x + 1 >= self.world.world_size_x:
            borders.append("right")
        if y <= 0:
            borders.append("top")
        return borders

    def detect_actors(self, filter=None) -> list:
        """
        Senses actors at current position

        Args:
            distance: If distance > 0, it will be checked, if the actor is touching other actors,
            if moved two steps forward
            actors: Filters by actor_type. actor_type is a Class of actor.

        Returns: A list of actors at actor position

        """
        target_position = self.actor.position
        actor_list: list = list()
        if self.world and self.contains_position(target_position):
            # Use tiled spatial index if available
            tiled_spatial_index = getattr(self.world, "_tiled_spatial_index", None)
            if tiled_spatial_index is not None:
                actor_list = list(
                    tiled_spatial_index.query_exact_position(target_position)
                )
            else:
                actor_list = self.world.detect_actors(target_position)
        if not actor_list:
            actor_list = []
        actor_list = self._remove_self_from_actor_list(actor_list)
        actor_list = self._filter_actor_list(actor_list, filter)
        return actor_list

    def detect_actor(self, filter=None) -> "actor_module.Actor":
        """
        Senses actors at current position. The method is faster than sensing_actors.

        Args:
            distance: If distance > 0, it will be checked, if the actor is touching other actors,
            if moved two steps forward
            actors: Filters by actor_type. actor_type is a Class of actor.

        Returns: The first actor at current position or None.

        """
        actor_list = self.detect_actors(filter=filter)
        actor_list = self._remove_self_from_actor_list(actor_list)
        actor_list = self._filter_actor_list(actor_list, filter)
        if actor_list:
            return actor_list[0]

    def remove_from_world(self) -> None:
        """Removes a actor from world"""
        if self.actor in self.world._dynamic_actors:
            self.world._dynamic_actors.remove(self.actor)
        if self.actor in self.world.static_actors_dict[self.actor.position]:
            self.world.static_actors_dict[self.actor.position.to_tuple()].remove(
                self.actor
            )
        super().remove_from_world()

    def self_remove(self):
        self.remove_from_world()

    def detect_point(self, position: Tuple[float, float]) -> bool:
        return self.actor.position == position

    def detect_pixel(self, position: Tuple[float, float]) -> bool:
        return self.actor.position == self.world.get_from_pixel(position)

    def detect_color_at(self, direction: Optional[int] = 0, distance: int = 0) -> Tuple:
        if not direction:
            direction = self.actor.direction
        destination = self.get_destination(self.actor.position, direction, distance)
        destination = self.world.to_pixel(destination)
        return self.world.background.get_color(destination)

    def get_distance_to(
        self, obj: Union["actor_module.Actor", Tuple[float, float]]
    ) -> float:
        tile1 = tile_mod.Tile.from_actor(self.actor)
        if isinstance(obj, actor_module.Actor):
            tile2 = tile_mod.Tile.from_actor(obj)
        else:
            tile2 = self.actor.world.get_tile(obj)
        return tile1.distance_to(tile2)

    def get_actors_at_position(self, position):
        return [actor for actor in self.world.actors if actor.position == position]
