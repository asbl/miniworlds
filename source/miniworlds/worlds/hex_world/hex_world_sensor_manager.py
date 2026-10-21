from __future__ import annotations

import math
from typing import Optional, Tuple, Union

import miniworlds.actors.actor as actor_module
import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.tiled_world.tiled_world_sensor_manager as tiled_sensor_manager


class HexWorldSensorManager(tiled_sensor_manager.TiledWorldSensorManager):
    """Sensor manager for hex worlds.

    Click and pixel detection for actors on hexes uses the exact hex
    picking inherited from the tiled sensor manager. Actors on corners
    or edges are detected when the pixel is close to the corner or edge
    center, so settlements and roads can be clicked.

    Distances between actors on hexes are hex distances (number of
    hexes between the positions), not euclidean offset distances.
    """

    # Maximum pixel distance for corner/edge detection, relative to tile size.
    DETECTION_RADIUS_FACTOR = 1.0 / 3.0

    def detect_pixel(self, position: Tuple[float, float]) -> bool:
        world = self.actor.world
        if world.is_corner(self.actor.position):
            corner = world.tile_factory.corner_cls.from_position(
                self.actor.position, world
            )
            return self._pixel_distance(position, corner.to_pixel()) <= self._detection_radius()
        if world.is_edge(self.actor.position):
            edge = world.tile_factory.edge_cls.from_position(self.actor.position, world)
            return self._pixel_distance(position, edge.to_pixel()) <= self._detection_radius()
        return super().detect_pixel(position)

    def _detection_radius(self) -> float:
        return self.actor.world.tile_size * self.DETECTION_RADIUS_FACTOR

    def get_distance_to(
        self, obj: Union["actor_module.Actor", Tuple[float, float]]
    ) -> float:
        """Return the distance to another actor or position.

        For actors and positions on hex tiles, the hex distance (the
        number of hexes between the positions) is returned. If a corner
        or edge is involved, the pixel distance between the corner,
        edge, or hex centers is returned.
        """
        world = self.actor.world
        start = self.actor.position
        target = obj.position if isinstance(obj, actor_module.Actor) else obj
        if world.is_tile(start) and world.is_tile(target):
            return float(
                hex_coords.cube_distance(
                    hex_coords.offset_to_cube(start), hex_coords.offset_to_cube(target)
                )
            )
        start_center = self._center_pixel(start)
        target_center = self._center_pixel(target)
        if start_center is not None and target_center is not None:
            return self._pixel_distance(start_center, target_center)
        return super().get_distance_to(obj)

    def _center_pixel(self, position) -> Optional[Tuple[float, float]]:
        """Return the center pixel of a tile, corner, or edge position."""
        world = self.actor.world
        if world.is_tile(position):
            return world.get_tile(position).to_center()
        if world.is_corner(position):
            return world.get_corner(position).to_pixel()
        if world.is_edge(position):
            return world.get_edge(position).to_pixel()
        return None

    @staticmethod
    def _pixel_distance(first: Tuple[float, float], second: Tuple[float, float]) -> float:
        return math.sqrt(
            (first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2
        )
