from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

import miniworlds.base.app as app
import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.tiled_world.tile as tile_mod

if TYPE_CHECKING:
    from miniworlds.worlds.hex_world.hex_corner import HexCorner
    from miniworlds.worlds.hex_world.hex_edge import HexEdge
    from miniworlds.worlds.hex_world.hex_world import HexWorld


class HexTile(tile_mod.Tile):
    """A hexagonal tile in a HexWorld.

    Tiles are addressed with offset coordinates `(column, row)`, like
    tiles in a TiledWorld. Odd rows are shifted half a hex to the right;
    because of this shift, the diagonal neighbors of a hex depend on the
    row parity (see the `HexWorld` docstring for the full convention).
    """

    tile_vectors = dict(hex_coords.CUBE_DIRECTIONS)
    corner_vectors = dict(hex_coords.CORNER_DIRECTIONS)
    edge_vectors = dict(hex_coords.EDGE_DIRECTIONS)

    @classmethod
    def from_position(cls, position: Tuple[int, int], world: HexWorld) -> HexTile:
        return world.get_tile(position)

    @classmethod
    def from_pixel(
        cls, pixel_position: Tuple[float, float], world: Optional[HexWorld] = None
    ) -> HexTile:
        """Return the hex tile containing a pixel position.

        The conversion is exact: the pixel is converted to fractional cube
        coordinates and rounded to the nearest hex center. The position is
        not checked against the world bounds; use
        `world.get_tile_from_pixel` for a bounds-checked lookup that
        returns `None` outside the world.
        """
        if world is None:
            world = app.App.get_running_world()
        cube = hex_coords.pixel_to_cube(pixel_position, world.tile_size)
        return cls(hex_coords.cube_to_offset(cube), world)

    @staticmethod
    def get_position_pixel_dict(world: HexWorld) -> dict:
        return world.get_center_points()

    def to_pixel(self) -> Tuple[float, float]:
        """Return the topleft pixel of the hex bounding box."""
        center = self.to_center()
        half_width = hex_coords.hex_width(self.world.tile_size) / 2
        half_height = hex_coords.hex_height(self.world.tile_size) / 2
        return (center[0] - half_width, center[1] - half_height)

    def to_center(self) -> Tuple[float, float]:
        """Return the center pixel of the hex."""
        return hex_coords.hex_center(self.position, self.world.tile_size)

    @staticmethod
    def get_local_center_coordinate(world: HexWorld) -> Tuple[float, float]:
        half_width = hex_coords.hex_width(world.tile_size) / 2
        half_height = hex_coords.hex_height(world.tile_size) / 2
        return (half_width, half_height)

    def get_local_corner_points(self) -> List[Tuple[float, float]]:
        """Return the six corner pixels relative to the hex bounding box topleft."""
        topleft = self.to_pixel()
        return [
            (point[0] - topleft[0], point[1] - topleft[1])
            for point in hex_coords.corner_pixel_points(self.position, self.world.tile_size)
        ]

    def get_neighbour_tiles(self) -> List[HexTile]:
        """Return the up to six neighboring hex tiles."""
        if self._neighbour_tiles is not None:
            return self._neighbour_tiles

        cube = hex_coords.offset_to_cube(self.position)
        neighbours: List[HexTile] = []
        for vector in hex_coords.CUBE_DIRECTIONS.values():
            neighbour_cube = (
                cube[0] + vector[0],
                cube[1] + vector[1],
                cube[2] + vector[2],
            )
            neighbour_position = hex_coords.cube_to_offset(neighbour_cube)
            if self.world.is_tile(neighbour_position):
                neighbours.append(self.world.get_tile(neighbour_position))

        self._neighbour_tiles = neighbours
        return neighbours

    def get_corner(self, direction: str) -> HexCorner:
        """Return the corner of this hex in the given direction.

        Args:
            direction: Corner direction, e.g. `"no"`.

        Examples:
            ::

                corner = world.get_tile((2, 2)).get_corner("no")
        """
        return self.world.get_corner(self.position, direction)

    def get_edge(self, direction: str) -> HexEdge:
        """Return the edge of this hex in the given direction.

        Args:
            direction: Edge direction, e.g. `"o"`.

        Examples:
            ::

                edge = world.get_tile((2, 2)).get_edge("o")
        """
        return self.world.get_edge(self.position, direction)

    def __str__(self) -> str:
        return f"Hex-Tile at {self.position}"
