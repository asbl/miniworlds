from __future__ import annotations

from typing import List, Tuple, Optional, TYPE_CHECKING

import miniworlds.base.app as app
import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.tiled_world.edge as edge_mod
import miniworlds.worlds.tiled_world.tile_elements as tile_elements

if TYPE_CHECKING:
    from miniworlds.worlds.hex_world.hex_tile import HexTile
    from miniworlds.worlds.hex_world.hex_world import HexWorld


class HexEdge(edge_mod.Edge):
    """An edge of a hex, shared by exactly two hexes.

    The edge position is a unique key in doubled cube coordinates: both
    hexes that share the edge compute the same key, so edges are merged
    when the world is built.
    """

    angles = {
        "o": 0,
        "so": 1,
        "sw": 2,
        "w": 3,
        "nw": 4,
        "no": 5,
    }

    direction_angles = {
        "o": 0,
        "so": 60,
        "sw": 120,
        "w": 180,
        "nw": 240,
        "no": 300,
    }

    def __init__(self, position, direction: str, world: Optional[HexWorld] = None):
        if world is None:
            world = app.App.get_running_world()
        tile_elements.TileBase.__init__(self, position, world)
        self.tile = self.world.get_tile(position)
        self.direction_str = direction
        self.direction = hex_coords.direction_vector(
            direction, hex_coords.EDGE_DIRECTIONS
        )
        self.position = hex_coords.edge_position(self.tile.position, direction)
        self._world_position = self.position
        self.positions = [(self.position, self.direction_str)]
        self.angle = self.direction_angles[direction]

    @staticmethod
    def direction_vectors():
        return hex_coords.EDGE_DIRECTIONS

    @classmethod
    def from_position(cls, position, world: HexWorld) -> HexEdge:
        return world.get_edge(position)

    def get_neighbour_tiles(self) -> List[HexTile]:
        """Return the up to two hexes that share this edge.

        The hexes are derived from the merged edge references, so no
        tile has to exist for every reference: references to positions
        outside the world are skipped.
        """
        if self._neighbour_tiles is not None:
            return self._neighbour_tiles

        tiles: List[HexTile] = []
        for position, direction in self.positions:
            vector = hex_coords.EDGE_DIRECTIONS[direction]
            cube = (
                (position[0] - vector[0]) // 2,
                (position[1] - vector[1]) // 2,
                (position[2] - vector[2]) // 2,
            )
            tile_position = hex_coords.cube_to_offset(cube)
            if self.world.is_tile(tile_position):
                tiles.append(self.world.get_tile(tile_position))

        self._neighbour_tiles = tiles
        return tiles

    def to_pixel(self) -> Tuple[float, float]:
        """Return the pixel position of the edge center."""
        center = hex_coords.hex_center(self.tile.position, self.world.tile_size)
        offset = hex_coords.edge_pixel_offset(self.direction_str, self.world.tile_size)
        return (center[0] + offset[0], center[1] + offset[1])

    def start_angle(self) -> int:
        return 0

    def __str__(self) -> str:
        return f"Hex-Edge at {self.position}"
