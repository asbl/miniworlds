from __future__ import annotations

from typing import List, Tuple, Optional, TYPE_CHECKING

import miniworlds.base.app as app
import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.tiled_world.corner as corner_mod
import miniworlds.worlds.tiled_world.tile_elements as tile_elements

if TYPE_CHECKING:
    from miniworlds.worlds.hex_world.hex_tile import HexTile
    from miniworlds.worlds.hex_world.hex_world import HexWorld


class HexCorner(corner_mod.Corner):
    """A corner of a hex, shared by up to three hexes.

    The corner position is a unique key in tripled cube coordinates: all
    hexes that share the corner compute the same key, so corners are
    merged when the world is built.
    """

    angles = {
        "n": 0,
        "no": 1,
        "so": 2,
        "s": 3,
        "sw": 4,
        "nw": 5,
    }

    direction_angles = {
        "n": 0,
        "no": 0,
        "so": 0,
        "s": 0,
        "sw": 0,
        "nw": 0,
    }

    def __init__(self, position, direction: str, world: Optional[HexWorld] = None):
        if world is None:
            world = app.App.get_running_world()
        tile_elements.TileBase.__init__(self, position, world)
        self.tile = self.world.get_tile(position)
        self.direction_str = direction
        self.direction = hex_coords.direction_vector(
            direction, hex_coords.CORNER_DIRECTIONS
        )
        self.position = hex_coords.corner_position(self.tile.position, direction)
        self._world_position = self.position
        self.positions = [(self.position, self.direction_str)]
        self.angle = self.direction_angles[direction]

    @staticmethod
    def direction_vectors():
        return hex_coords.CORNER_DIRECTIONS

    @classmethod
    def from_position(cls, position, world: HexWorld) -> HexCorner:
        return world.get_corner(position)

    def get_neighbour_tiles(self) -> List[HexTile]:
        """Return the up to three hexes that share this corner.

        The hexes are derived from the merged corner references, so no
        tile has to exist for every reference: references to positions
        outside the world are skipped.
        """
        if self._neighbour_tiles is not None:
            return self._neighbour_tiles

        tiles: List[HexTile] = []
        for position, direction in self.positions:
            vector = hex_coords.CORNER_DIRECTIONS[direction]
            cube = (
                (position[0] - vector[0]) // 3,
                (position[1] - vector[1]) // 3,
                (position[2] - vector[2]) // 3,
            )
            tile_position = hex_coords.cube_to_offset(cube)
            if self.world.is_tile(tile_position):
                tiles.append(self.world.get_tile(tile_position))

        self._neighbour_tiles = tiles
        return tiles

    def to_pixel(self) -> Tuple[float, float]:
        """Return the pixel position of the corner."""
        center = hex_coords.hex_center(self.tile.position, self.world.tile_size)
        offset = hex_coords.corner_pixel_offset(self.direction_str, self.world.tile_size)
        return (center[0] + offset[0], center[1] + offset[1])

    def start_angle(self) -> int:
        return 0

    def __str__(self) -> str:
        return f"Hex-Corner at {self.position}"
