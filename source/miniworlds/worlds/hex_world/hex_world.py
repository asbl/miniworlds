from __future__ import annotations

from typing import Dict, List, Tuple

import miniworlds.base.exceptions as miniworlds_exception
import miniworlds.worlds.hex_world.hex_camera_manager as hex_camera_manager
import miniworlds.worlds.hex_world.hex_corner as hex_corner_mod
import miniworlds.worlds.hex_world.hex_edge as hex_edge_mod
import miniworlds.worlds.hex_world.hex_tile as hex_tile_mod
import miniworlds.worlds.hex_world.hex_tile_factory as hex_tile_factory
import miniworlds.worlds.hex_world.hex_world_connector as hex_world_connector
import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.tiled_world.tiled_world as tiled_world


class HexWorld(tiled_world.TiledWorld):
    """A world that consists of hexagonal tiles.

    Hexes are addressed with offset coordinates `(column, row)`, like
    tiles in a TiledWorld. Odd rows are shifted half a hex to the right
    (pointy-top layout). Actors can also be placed on corners (shared by
    up to three hexes) or edges (shared by two hexes).

    Examples:
        ::

            from miniworlds import HexWorld, Actor

            world = HexWorld(7, 7, tile_size=40)
            actor = Actor((3, 3))
            actor.fill_color = (255, 0, 0)

            world.run()
    """

    is_hex = True

    def __init__(self, x: int = 20, y: int = 16, tile_size: int = 40, empty=False):
        """Create a hex world.

        Args:
            x: Number of columns.
            y: Number of rows.
            tile_size: The hex size in pixels (circumradius of the hex).
            empty: If `True`, tiles, edges, and corners are not created
                automatically.
        """
        super().__init__(x=x, y=y, tile_size=tile_size, empty=empty)

    @staticmethod
    def _get_camera_manager_class():
        return hex_camera_manager.HexCameraManager

    @staticmethod
    def _get_world_connector_class():
        return hex_world_connector.HexWorldConnector

    def _get_tile_factory(self):
        return hex_tile_factory.HexTileFactory()

    def _templates(self):
        return hex_tile_mod.HexTile, hex_edge_mod.HexEdge, hex_corner_mod.HexCorner

    def to_pixel(self, position, size=(0, 0), origin=(0, 0)):
        """Convert a hex position to the pixel position of its center.

        Args:
            position: Hex position as `(column, row)`.
            size: Reserved for compatibility.
            origin: Pixel offset added to the converted position.

        Returns:
            Pixel position as `(x, y)`.

        Examples:
            ::

                pixel = world.to_pixel((2, 3))
        """
        center = hex_coords.hex_center(position, self.tile_size)
        return (center[0] + origin[0], center[1] + origin[1])

    def get_tile_from_pixel(self, position):
        """Return the hex tile under a screen pixel.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            The hex tile under the pixel.

        Examples:
            ::

                tile = world.get_tile_from_pixel((80, 120))
        """
        tile_cls = self.tile_factory.tile_cls
        return tile_cls.from_pixel(position, self)

    def get_corner_from_pixel(self, position):
        """Return the corner nearest to a screen pixel.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            The nearest corner.

        Examples:
            ::

                corner = world.get_corner_from_pixel(mouse_pos)
        """
        tile = self.get_tile_from_pixel(position)
        nearest_corner = None
        nearest_distance = None
        for direction in hex_coords.CORNER_ORDER:
            corner = self.get_corner(tile.position, direction)
            corner_pixel = corner.to_pixel()
            distance = (
                (corner_pixel[0] - position[0]) ** 2
                + (corner_pixel[1] - position[1]) ** 2
            )
            if nearest_distance is None or distance < nearest_distance:
                nearest_corner = corner
                nearest_distance = distance
        return nearest_corner

    def get_edge_from_pixel(self, position):
        """Return the edge nearest to a screen pixel.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            The nearest edge.

        Examples:
            ::

                edge = world.get_edge_from_pixel(mouse_pos)
        """
        tile = self.get_tile_from_pixel(position)
        nearest_edge = None
        nearest_distance = None
        for direction in hex_coords.CUBE_DIRECTIONS:
            edge = self.get_edge(tile.position, direction)
            edge_pixel = edge.to_pixel()
            distance = (
                (edge_pixel[0] - position[0]) ** 2
                + (edge_pixel[1] - position[1]) ** 2
            )
            if nearest_distance is None or distance < nearest_distance:
                nearest_edge = edge
                nearest_distance = distance
        return nearest_edge

    def get_center_points(self) -> Dict[Tuple[int, int], Tuple[float, float]]:
        """Return a mapping of hex positions to their center pixels."""
        center_points = dict()
        for position, tile in self.tiles.items():
            center_points[position] = tile.to_center()
        return center_points

    def get_corner(self, position, direction=None):
        """Return a corner by corner position or hex position plus direction.

        Args:
            position: Corner position, or hex position when `direction` is set.
            direction: Optional corner direction, e.g. `"no"`.

        Returns:
            The matching corner.

        Raises:
            CornerNotFoundError: If no corner exists at the resolved position.

        Examples:
            ::

                corner = world.get_corner((3, 3), "no")
        """
        corner_cls = self.tile_factory.corner_cls
        if direction is not None:
            position = corner_cls(position, direction, self).position
        if position in self.corners:
            return self.corners[position]
        raise miniworlds_exception.CornerNotFoundError(position)

    def get_edge(self, position, direction=None):
        """Return an edge by edge position or hex position plus direction.

        Args:
            position: Edge position, or hex position when `direction` is set.
            direction: Optional edge direction, e.g. `"o"`.

        Returns:
            The matching edge.

        Raises:
            EdgeNotFoundError: If no edge exists at the resolved position.

        Examples:
            ::

                edge = world.get_edge((3, 3), "o")
        """
        edge_cls = self.tile_factory.edge_cls
        if direction is not None:
            position = edge_cls(position, direction, self).position
        if position in self.edges:
            return self.edges[position]
        raise miniworlds_exception.EdgeNotFoundError(position)

    def get_tiles_in_radius(self, position, radius: int) -> List[hex_tile_mod.HexTile]:
        """Return all tiles within a hex distance of `radius`.

        Args:
            position: Hex position as `(column, row)`.
            radius: Maximum hex distance (0 includes only the tile itself).

        Returns:
            List of tiles within the radius, including the tile itself.

        Examples:
            ::

                neighbours = world.get_tiles_in_radius((3, 3), 1)
        """
        cube = hex_coords.offset_to_cube(position)
        tiles = []
        for tile_position, tile in self.tiles.items():
            if hex_coords.cube_distance(cube, hex_coords.offset_to_cube(tile_position)) <= radius:
                tiles.append(tile)
        return tiles

    def get_tiles_in_ring(self, position, radius: int) -> List[hex_tile_mod.HexTile]:
        """Return all tiles at exactly `radius` hex distance.

        Args:
            position: Hex position as `(column, row)`.
            radius: Hex distance.

        Returns:
            List of tiles at the given distance.

        Examples:
            ::

                ring = world.get_tiles_in_ring((3, 3), 2)
        """
        cube = hex_coords.offset_to_cube(position)
        tiles = []
        for tile_position, tile in self.tiles.items():
            if hex_coords.cube_distance(cube, hex_coords.offset_to_cube(tile_position)) == radius:
                tiles.append(tile)
        return tiles
