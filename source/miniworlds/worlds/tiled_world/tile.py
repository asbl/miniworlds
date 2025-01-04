from __future__ import annotations

from collections import OrderedDict
from typing import List, Optional, Tuple
from typing import TYPE_CHECKING
import miniworlds.worlds.tiled_world.tile_elements as tile_elements
import miniworlds.base.app as app

if TYPE_CHECKING:
    import miniworlds.worlds.tiled_world.corner as corner
    import miniworlds.worlds.tiled_world.tiled_world as tiled_world_mod



class Tile(tile_elements.TileBase):
    tile_vectors = {
        "w": (+1, 0),
        "nw": (+1, +1),
        "no": (-1, +1),
        "o": (-1, 0),
        "so": (-1, -1),
        "sw": (+1, -1),
    }

    corner_vectors = OrderedDict(
        [
            ("nw", (+0.5, +0.5)),
            ("no", (-0.5, +0.5)),
            ("so", (-0.5, -0.5)),
            ("sw", (+0.5, -0.5)),
        ]
    )

    edge_vectors = {
        "w": (-0.5, 0),
        "o": (+0.5, 0),
        "s": (0, +0.5),
        "n": (0, -0.5),
    }

    @classmethod
    def from_position(cls, position, world: "tiled_world_mod.TiledWorld" = None) -> "tile_elements.TileBase":
        return world.get_tile(position)

    @classmethod
    def from_actor(cls, actor):
        return actor.world.get_tile(actor.position)

    def __init__(self, position, world=None):
        super().__init__(position, world)
        self.tiles = []
        self.corners = []
        self.edges = []

    def get_neighbour_corners(self) -> List["corner.Corner"]:
        if self.corners:
            return self.corners
        else:
            neighbours = []
            for corner, vector in self.corner_vectors.items():
                neighbour = self.world.get_corner(self.position + vector)
                if neighbour:
                    neighbours.append(neighbour)
            self.corners = neighbours
            return self.corners

    def to_pixel(self) -> Tuple[float, float]:
        x = self.position[0] * self.world.tile_size
        y = self.position[1] * self.world.tile_size
        return x, y

    @staticmethod
    def get_position_pixel_dict(world):
        return world.get_center_points()

    def to_center(self):
        topleft = self.to_pixel()
        return topleft + self.get_local_center_coordinate(self.world)

    @classmethod
    def from_pixel(cls, pixel_position,
                   world: Optional["tiled_world_mod.TiledWorld"] = None) -> "tile_elements.TileBase":
        if not world:
            world = app.App.running_world
        x = pixel_position[0] // world.tile_size
        y = pixel_position[1] // world.tile_size
        return cls((x, y), world=None)

    def __sub__(self, other):
        import miniworlds.positions.vector as world_vector #t
        return world_vector.Vector(self.position[0] - other.position[0], self.position[1] - other.position[1])

    def distance_to(self, other):
        vec = self - other
        return vec.length()
