from __future__ import annotations

import abc
import math
from typing import List, Dict, Tuple, TYPE_CHECKING

import miniworlds.base.app as app
import miniworlds.worlds.tiled_world.tile as tile_mod

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod


class TileBase(abc.ABC):
    """Base class for Tiles and TileDelimiters (like Corners, Edges)."""

    corner_vectors: dict = {}
    tile_vectors: dict = {}

    # Cache: maps world id to a dict of tile positions and their corresponding pixel coordinates
    _position_pixel_cache: Dict[int, Dict[Tuple[int, int], Tuple[float, float]]] = {}

    # Cache: maps world id to a list of (tile position, pixel coordinate) tuples for fast iteration
    _position_pixel_list_cache: Dict[int, List[Tuple[Tuple[int, int], Tuple[float, float]]]] = {}

    def __init__(self, position: Tuple[int, int], world: world_mod.World = None):
        self._neighbour_tiles = None
        self.int_coord = self._internal_coordinates()
        self.world = world or app.App.running_world
        self.position = position
        self._world_position = position
        self.positions = [self.position]

    @classmethod
    @abc.abstractmethod
    def from_position(cls, position: Tuple[int, int], world: world_mod.World) -> TileBase:
        """Create a tile from a world-relative position."""
        pass

    @staticmethod
    def _get_corner_cls():
        return TileDelimiter

    @staticmethod
    def _get_edge_cls():
        return TileDelimiter

    @classmethod
    def from_pixel(cls, pixel_position: Tuple[float, float], world: world_mod.World) -> TileBase:
        """
        Finds the nearest tile to a given pixel coordinate.

        This method uses caching to avoid redundant recalculation of the mapping
        between tile grid positions and their corresponding pixel coordinates for
        a given world. It also uses squared distance instead of Euclidean distance
        for better performance.

        Args:
            pixel_position (Tuple[float, float]): The (x, y) pixel position.
            world (world_mod.World): The world instance containing the tile layout.

        Returns:
            TileBase: The tile object closest to the given pixel position.
        """
        world_id = id(world)

        if world_id not in cls._position_pixel_cache:
            # Compute and cache the pixel positions for all tiles in the world
            position_pixel_dict = cls.get_position_pixel_dict(world)
            cls._position_pixel_cache[world_id] = position_pixel_dict
            cls._position_pixel_list_cache[world_id] = list(position_pixel_dict.items())

        # Find the tile position with the smallest squared distance to the pixel
        nearest_pos = min(
            cls._position_pixel_list_cache[world_id],
            key=lambda item: (item[1][0] - pixel_position[0]) ** 2 + (item[1][1] - pixel_position[1]) ** 2
        )[0]

        return cls.from_position(nearest_pos, world)

    @staticmethod
    def get_position_pixel_dict(world: world_mod.World) -> dict:
        """Returns a mapping of tile positions to pixel coordinates."""
        pass

    @staticmethod
    def get_local_center_coordinate(world: world_mod.World) -> Tuple[float, float]:
        """Returns the center point offset for a tile, in local pixel coordinates."""
        ts = world.tile_size
        return ts / 2, ts / 2

    @staticmethod
    def _internal_coordinates() -> Tuple[float, float]:
        """Returns internal coordinates, if needed (override in subclass)."""
        return 0.0, 0.0

    def merge(self, other: TileBase):
        """Merge tile positions from another tile at the same location."""
        assert other.position == self.position, "Tiles must share the same position to merge."
        for pos in other.positions:
            if pos not in self.positions:
                self.positions.append(pos)

    def get_actors(self) -> List:
        """Returns all actors currently on this tile."""
        return [actor for actor in self.world.actors if actor.position == self.position]

    def add_actor(self, actor):
        """Places an actor on this tile."""
        actor.position = self.position

    def get_neighbour_tiles(self) -> List[tile_mod.Tile]:
        """Returns neighboring tiles around this tile."""
        if self._neighbour_tiles is not None:
            return self._neighbour_tiles

        neighbours = []
        for direction, vector in self.tile_vectors.items():
            new_pos = tuple(self.position[i] + vector[i] for i in range(2))
            if self.world.is_tile(new_pos):
                tile = self.world.get_tile(new_pos)
                if tile and tile not in neighbours:
                    neighbours.append(tile)

        self._neighbour_tiles = neighbours
        return neighbours

    def get_local_corner_points(self):
        """Returns corner point offsets for rendering."""
        return [
            self._get_corner_cls()(self._world_position, direction, self.world)
            .get_local_coordinate_for_tile(self)
            for direction, vector in self.corner_vectors.items()
        ]


class TileDelimiter(TileBase):
    """Base class for corners and edges (tile delimiters)."""

    angles: Dict[str, int] = {}
    direction_angles: Dict[str, int] = {}

    def __init__(self, position, direction: str, world):
        super().__init__(position, world)
        self.tile = self.world.get_tile(position)
        self.direction_str = direction
        self.direction = self.direction_vectors()[direction]
        self.position = tuple(self.tile.position[i] + self.direction[i] for i in range(2))
        self.positions = [(self.position, self.direction)]
        self.angle = self.direction_angles[direction]

    @classmethod
    def from_position(cls, position, world):
        """Create a tile delimiter (override expected)."""
        return cls(position, direction="default", world=world)

    @classmethod
    @abc.abstractmethod
    def direction_vectors(cls) -> Dict[str, Tuple[int, int]]:
        """Returns the available directions."""
        pass

    def get_direction(self):
        return self.direction_angles[self.direction_str]

    def get_local_coordinate_for_tile(self, tile) -> Tuple[float, float]:
        """Returns pixel offset of delimiter relative to given tile."""
        dx = self.to_pixel()[0] - tile.to_pixel()[0]
        dy = self.to_pixel()[1] - tile.to_pixel()[1]
        return dx, dy

    def get_local_coordinate_for_base_tile(self) -> Tuple[float, float]:
        """Returns offset in pixels from base tile center."""
        center = TileBase.get_local_center_coordinate(self.world)
        if self.angles:
            direction = self._get_direction_string(self.direction)
            angle_index = self.angles[direction]
            angle_rad = 2.0 * math.pi * (self.start_angle() - angle_index) / len(self.angles)
            radius = self.world.tile_size / 2
            return (
                center[0] + radius * math.cos(angle_rad),
                center[1] + radius * math.sin(angle_rad),
            )
        return center

    def to_pixel(self) -> Tuple[float, float]:
        """Returns absolute pixel position of this delimiter."""
        base_pixel = self.tile.to_pixel()
        offset = self.get_local_coordinate_for_base_tile()
        return base_pixel[0] + offset[0], base_pixel[1] + offset[1]

    def _get_direction_string(self, direction: Tuple[int, int]) -> str:
        """Returns the string key for a direction vector."""
        for name, vec in self.direction_vectors().items():
            if vec == direction:
                return name
        raise ValueError(f"Unknown direction vector: {direction}")

    def get_angle(self, direction: str) -> int:
        """Returns angle for a given direction string."""
        return self.angles[direction]

    def start_angle(self) -> int:
        """Override: starting angle offset for layouting (e.g. hex rotation)."""
        return 0
