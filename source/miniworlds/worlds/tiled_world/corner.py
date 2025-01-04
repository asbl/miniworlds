import math
from typing import Optional

import miniworlds.base.app as app
import miniworlds.worlds.tiled_world.tile as tile
import miniworlds.worlds.tiled_world.tile_elements as tile_elements
import miniworlds.worlds.tiled_world.tiled_world as tiled_world_mod


class Corner(tile_elements.TileDelimiter):
    angles = {
        "no": 0,
        "nw": 1,
        "sw": 2,
        "so": 3,
    }

    direction_angles = {
        "no": 0,
        "nw": 0,
        "sw": 0,
        "so": 0,
    }

    @staticmethod
    def direction_vectors():
        return tile.Tile.corner_vectors

    @classmethod
    def from_position(cls, position, world: "tiled_world_mod.TiledWorld"):
        return world.get_corner(position)

    @classmethod
    def from_pixel(cls, position, world: Optional["tiled_world_mod.TiledWorld"] = None):
        if not world:
            world = app.App.window.worlds_manager.get_container_by_pixel(position[0], position[1])
        min_value = math.inf
        nearest_hex = None
        corner_points = world.get_corner_points()
        for corner_position, corner_pos in corner_points.items():
            distance = math.sqrt(pow(position[0] - corner_pos[0], 2) + pow(position[1] - corner_pos[1], 2))
            if distance < min_value:
                min_value = distance
                nearest_hex = corner_position
        return cls.from_position(nearest_hex, world)

    @classmethod
    def from_tile(cls, position, direction_string):
        world = app.App.running_world
        tile = world.get_tile(position)
        return world.get_corner(tile.position + cls.get_direction_from_string(direction_string))

    def start_angle(self):
        return 0.5
