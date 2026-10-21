from __future__ import annotations

import math
from typing import Tuple

import miniworlds.worlds.tiled_world.tiled_world_sensor_manager as tiled_sensor_manager


class HexWorldSensorManager(tiled_sensor_manager.TiledWorldSensorManager):
    """Sensor manager for hex worlds.

    Click and pixel detection for actors on hexes uses the exact hex
    picking inherited from the tiled sensor manager. Actors on corners
    or edges are detected when the pixel is close to the corner or edge
    center, so settlements and roads can be clicked.
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

    @staticmethod
    def _pixel_distance(first: Tuple[float, float], second: Tuple[float, float]) -> float:
        return math.sqrt(
            (first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2
        )
