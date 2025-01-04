from __future__ import annotations

import abc
import math
from abc import abstractmethod
from typing import List, Dict, Type, Tuple
from typing import TYPE_CHECKING

import miniworlds.base.app as app
import miniworlds.worlds.tiled_world.tile as tile_mod
if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod


class TileBase(abc.ABC):
    """Base Class for Tiles AND TileDelimiters (Corners, Edges)

    Tiles are defined by a position. Multiple positions can be stores, if Tile can be described by multiple
    positions (e.g. in a Hex-world), multiple positions are stores per Tile.
    """

    corner_vectors: dict = None
    tile_vectors: dict = None

    def __init__(self, position, world: "world_mod.World" = None):
        self._neighbour_tiles = None
        self.int_coord = self._internal_coordinates()
        if world:
            self.world = world
        else:
            self.world = app.App.running_world
        self.position = position
        self._world_position = position
        self.positions = [(self.position)]

    @classmethod
    @abstractmethod
    def from_position(cls, position, world: "world_mod.World"):
        pass

    @staticmethod
    def _get_corner_cls():
        return TileDelimiter

    @staticmethod
    def _get_edge_cls():
        return TileDelimiter

    @classmethod
    def from_pixel(cls, pixel_position, world) -> "TileBase":
        min_value = math.inf
        nearest_world_position = None
        for world_pos, pixel in cls.get_position_pixel_dict(world).items():
            distance = math.sqrt(pow(pixel_position[0] - pixel[0], 2) + pow(pixel_position[1] - pixel[1], 2))
            if distance < min_value:
                min_value = distance
                nearest_world_position = world_pos
        return cls.from_position(nearest_world_position, world)

    @staticmethod
    def get_position_pixel_dict(world) -> dict:
        pass

    @staticmethod
    def get_local_center_coordinate(world: "world_mod.World") -> Tuple[float, float]:
        return world.tile_size / 2, world.tile_size / 2

    @staticmethod
    def _internal_coordinates() -> Tuple[float, float]:
        return tuple

    def merge(self, other):
        assert other.position == self.position
        for pos in other.positions:
            if pos not in self.positions:
                self.positions.append(pos)

    def get_actors(self):
        actors = []
        for tkn in self.world.actors:
            if tkn.position == self.position:
                actors.append(tkn)
        return actors

    def add_actor(self, actor):
        actor.position = self.position

    def get_neighbour_tiles(self) -> List["tile_mod.Tile"]:
        if hasattr(self, "_tiles") and self._neighbour_tiles:  # cached at end of this function
            return self._neighbour_tiles
        neighbours = []
        for tile, vectors in self.tile_vectors.items():
            for vector in vectors:
                if self.world.is_tile(self.position + vector):
                    neighbour = self.world.get_tile(self.position + vector)
                    if neighbour and neighbour not in neighbours:
                        neighbours.append(neighbour)
        self._neighbour_tiles = neighbours
        return self._neighbour_tiles

    def get_local_corner_points(self):
        points = []
        for corner_str, vector in self.corner_vectors.items():
            corner = self._get_corner_cls()(self._world_position, corner_str, self.world)
            offset = corner.get_local_coordinate_for_tile(self)
            points.append(offset)
        return points


class TileDelimiter(TileBase):
    """Base Class for corners and edges

    Delimiters are defined by:
      * The position of a Tile
      * A direction
    """

    @classmethod
    def from_position(cls, position, world: "world_mod.World"):
        return cls.from_position(position, world)

    angles: Dict[str, int] = dict()
    direction_angles: Dict[str, int] = dict()

    def __init__(self, position, direction, world):
        super().__init__(position, world)
        internal_coordinates = position
        self.tile = self.world.get_tile(internal_coordinates)
        self.direction = self.direction_vectors()[direction]
        self.position = self.tile.position + self.direction
        self.positions = [(self.position, self.direction)]
        self.direction_str = direction
        self.angle = self.direction_angles[self.direction_str]

    @classmethod
    def get_direction_from_string(cls, direction_string):
        return cls.direction_vectors()[direction_string]

    def _get_direction_string(self, direction) -> str:
        if type(direction) == tuple:
            for dir_string, dir_vector in self.direction_vectors().items():
                if direction == dir_vector:
                    return dir_string
        else:
            raise TypeError("Direction must be tuple")

    def get_local_coordinate_for_tile(self, tile):
        tile_pos = tile.to_pixel()
        delimiter_pos = self.to_pixel()
        local = delimiter_pos - tile_pos
        return local

    def get_local_coordinate_for_base_tile(self) -> Tuple[float, float]:
        """Gets pixel offset based on tile

        Returns:
            Offset as position (x, y and y coordinate measured )
        """
        center = TileBase.get_local_center_coordinate(self.world)

        if self.angles:
            direction_tuple = self.direction
            direction = self._get_direction_string(direction_tuple)
            angle_nr = self.angles[direction]
            base_size = self.world.tile_size
            start_angle = self.start_angle()
            angle = 2.0 * math.pi * (start_angle - angle_nr) / len(self.angles)
            offset = base_size / 2 * math.cos(angle), base_size / 2 * math.sin(angle)
            return offset + center
        else:
            return center

    def to_pixel(self) -> Tuple[float, float]:
        local = self.get_local_coordinate_for_base_tile()
        tile_pos = self.tile.to_pixel()
        return tile_pos + local

    @staticmethod
    @abstractmethod
    def direction_vectors() -> dict:
        return None

    def start_angle(self) -> int:
        pass

    def get_angle(self, direction) -> int:
        return self.angles[direction]

    def get_direction(self):
        dir_str = self._get_direction_string(self.direction)
        return self.direction_angles[dir_str]
