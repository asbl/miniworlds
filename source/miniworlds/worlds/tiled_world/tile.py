from __future__ import annotations

from collections import OrderedDict
from typing import List, Optional, Tuple, TYPE_CHECKING

import miniworlds.worlds.tiled_world.tile_elements as tile_elements
import miniworlds.base.app as app

if TYPE_CHECKING:
    from miniworlds.worlds.tiled_world.corner import Corner
    from miniworlds.worlds.tiled_world.tiled_world import TiledWorld
    from miniworlds.positions.vector import Vector


class Tile(tile_elements.TileBase):
    tile_vectors: dict[str, Tuple[int, int]] = {
        "w": (+1, 0),
        "nw": (+1, +1),
        "no": (-1, +1),
        "o": (-1, 0),
        "so": (-1, -1),
        "sw": (+1, -1),
    }

    corner_vectors: OrderedDict[str, Tuple[float, float]] = OrderedDict([
        ("nw", (+0.5, +0.5)),
        ("no", (-0.5, +0.5)),
        ("so", (-0.5, -0.5)),
        ("sw", (+0.5, -0.5)),
    ])

    edge_vectors: dict[str, Tuple[float, float]] = {
        "w": (-0.5, 0),
        "o": (+0.5, 0),
        "s": (0, +0.5),
        "n": (0, -0.5),
    }

    def __init__(self, position: Tuple[int, int], world: Optional[TiledWorld] = None):
        super().__init__(position, world)
        self._cached_corners: Optional[List[Corner]] = None  # Cache explizit und privat

    @classmethod
    def from_position(cls, position: Tuple[int, int], world: TiledWorld) -> Tile:
        return world.get_tile(position)

    @classmethod
    def from_actor(cls, actor) -> Tile:
        return actor.world.get_tile(actor.position)

    def get_neighbour_corners(self) -> List[Corner]:
        if self._cached_corners is not None:
            return self._cached_corners

        neighbours = []
        for vector in self.corner_vectors.values():
            corner = self.world.get_corner(self.position + vector)
            if corner:
                neighbours.append(corner)

        self._cached_corners = neighbours
        return neighbours

    def to_pixel(self) -> Tuple[float, float]:
        x = self.position[0] * self.world.tile_size
        y = self.position[1] * self.world.tile_size
        return x, y

    @staticmethod
    def get_position_pixel_dict(world: TiledWorld) -> dict:
        return world.get_center_points()
        
    def to_center(self) -> Tuple[float, float]:
        x, y = self.to_pixel()
        dx, dy = self.get_local_center_coordinate(self.world)
        return x + dx, y + dy

    @classmethod
    def from_pixel(cls, pixel_position: Tuple[float, float], world: Optional[TiledWorld] = None) -> Tile:
        if world is None:
            world = app.App.running_world
        x = int(pixel_position[0] // world.tile_size)
        y = int(pixel_position[1] // world.tile_size)
        return cls((x, y), world)

    def __sub__(self, other: Tile) -> Vector:
        from miniworlds.positions.vector import Vector
        return Vector(self.position[0] - other.position[0], self.position[1] - other.position[1])

    def distance_to(self, other: Tile) -> float:
        return (self - other).length()

