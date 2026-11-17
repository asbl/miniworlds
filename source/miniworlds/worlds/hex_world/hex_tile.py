from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

import miniworlds.base.app as app
import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.hex_world.hex_neighbour_cache as hex_neighbour_cache
import miniworlds.worlds.tiled_world.tile as tile_mod

if TYPE_CHECKING:
    from miniworlds.worlds.hex_world.hex_corner import HexCorner
    from miniworlds.worlds.hex_world.hex_edge import HexEdge
    from miniworlds.worlds.hex_world.hex_world import HexWorld


class HexTile(hex_neighbour_cache.HexNeighbourCacheMixin, tile_mod.Tile):
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
        """Return the up to six neighboring hex tiles.

        The list is a copy; changing it does not affect the world.
        """
        return list(self._neighbour_tiles_shared())

    def _neighbour_tiles_shared(self) -> List[HexTile]:
        """Return the cached neighbour list itself (do not modify it).

        Used by path finding, which reads the list in a hot loop and
        would pay for a copy on every step.
        """
        cached = self._cached_neighbour_tiles()
        if cached is not None:
            return cached

        column, row = self.position
        tiles = self.world.tiles
        neighbours: List[HexTile] = []
        for delta_column, delta_row in hex_coords.neighbour_offset_deltas(row):
            tile = tiles.get((column + delta_column, row + delta_row))
            if tile is not None:
                neighbours.append(tile)

        self._cache_neighbour_tiles(neighbours)
        return neighbours

    def get_neighbour(self, direction: str) -> Optional[HexTile]:
        """Return the neighboring hex in one direction, or `None` at the border.

        Args:
            direction: One of `"o"`, `"so"`, `"sw"`, `"w"`, `"nw"`, `"no"`.

        Raises:
            DirectionNotFoundError: If `direction` is not a hex direction.

        Examples:
            ::

                east = world.get_tile((3, 3)).get_neighbour("o")
                if east is not None:
                    east.highlight()
        """
        vector = hex_coords.direction_vector(direction, hex_coords.CUBE_DIRECTIONS)
        cube = hex_coords.offset_to_cube(self.position)
        position = hex_coords.cube_to_offset(
            (cube[0] + vector[0], cube[1] + vector[1], cube[2] + vector[2])
        )
        return self.world.tiles.get(position)

    def get_tiles_in_radius(self, radius: int, include_center: bool = False) -> List[HexTile]:
        """Return the tiles within `radius` steps of this hex.

        Unlike `world.get_tiles_in_radius`, the tile itself is not included
        by default, so `get_tiles_in_radius(1)` returns the same tiles as
        `get_neighbour_tiles()` (in ring order instead of direction order).

        Args:
            radius: Maximum hex distance.
            include_center: If `True`, this tile is the first result.

        Examples:
            ::

                for tile in world.get_tile((3, 3)).get_tiles_in_radius(2):
                    tile.highlight()
        """
        return self.world.get_tiles_in_radius(
            self.position, radius, include_center=include_center
        )

    def get_tiles_in_ring(self, radius: int) -> List[HexTile]:
        """Return the tiles at exactly `radius` steps from this hex.

        Examples:
            ::

                ring = world.get_tile((3, 3)).get_tiles_in_ring(2)
        """
        return self.world.get_tiles_in_ring(self.position, radius)

    def get_distance_to(self, other) -> int:
        """Return the hex distance (number of steps) to a tile, position, or actor.

        Examples:
            ::

                steps = tile.get_distance_to(goal_tile)
        """
        return self.world.get_distance(self.position, other)

    def distance_to(self, other) -> int:
        """Return the hex distance to another tile (same as `get_distance_to`).

        The rectangular `Tile.distance_to` measures the euclidean distance
        of the offset coordinates, which is wrong on a hex grid because of
        the shifted rows.
        """
        return self.get_distance_to(other)

    def get_neighbour_corners(self) -> List[HexCorner]:
        """Return the six corners of this hex, clockwise from the top tip.

        Examples:
            ::

                for corner in world.get_tile((2, 2)).get_neighbour_corners():
                    print(corner.position)
        """
        return self._cached_neighbours(
            "corners",
            lambda: [self.get_corner(direction) for direction in hex_coords.CORNER_ORDER],
        )

    def get_neighbour_edges(self) -> List[HexEdge]:
        """Return the six edges of this hex, clockwise from the north-east edge.

        Examples:
            ::

                for edge in world.get_tile((2, 2)).get_neighbour_edges():
                    print(edge.position)
        """
        return self._cached_neighbours(
            "edges",
            lambda: [self.get_edge(direction) for direction in hex_coords.EDGE_ORDER],
        )

    def highlight(self, color: Tuple[int, ...] = (255, 255, 0, 90)) -> None:
        """Highlight this hex with a translucent color.

        The highlight is drawn on the world background below the actors
        and stays until `clear_highlight` is called.

        Args:
            color: RGB or RGBA color; with RGB a default transparency is used.

        Examples:
            ::

                @world.register
                def on_tile_enter(self, tile):
                    tile.highlight((255, 255, 255, 80))

                @world.register
                def on_tile_leave(self, tile):
                    tile.clear_highlight()
        """
        self.world.highlight_tiles([self], color)

    def clear_highlight(self) -> None:
        """Remove the highlight of this hex."""
        self.world.clear_highlights([self])

    @property
    def is_highlighted(self) -> bool:
        """bool: Whether this hex is currently highlighted."""
        return self.position in self.world._tile_highlights

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
