from __future__ import annotations

from typing import Dict, List, Tuple

import miniworlds.base.exceptions as miniworlds_exception
import miniworlds.worlds.hex_world.hex_camera_manager as hex_camera_manager
import miniworlds.worlds.hex_world.hex_corner as hex_corner_mod
import miniworlds.worlds.hex_world.hex_edge as hex_edge_mod
import miniworlds.worlds.hex_world.hex_tile as hex_tile_mod
import miniworlds.worlds.hex_world.hex_tile_factory as hex_tile_factory
import miniworlds.worlds.hex_world.hex_world_connector as hex_world_connector
import miniworlds.worlds.hex_world.hex_world_sensor_manager as hex_world_sensor_manager
import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.tiled_world.tile_elements as tile_elements
import miniworlds.worlds.tiled_world.tiled_world as tiled_world


class HexWorld(tiled_world.TiledWorld):
    """A world that consists of hexagonal tiles.

    Hexes are addressed with offset coordinates `(column, row)`, like
    tiles in a TiledWorld. Odd rows are shifted half a hex to the right
    (pointy-top layout). Actors can also be placed on corners (shared by
    up to three hexes) or edges (shared by two hexes).

    The six neighbors of a hex are reached with the directions
    `"o"`, `"so"`, `"sw"`, `"w"`, `"nw"`, `"no"`. Because odd rows are
    shifted, the diagonal neighbors depend on the row parity:

    * Odd rows: `"no"` and `"so"` point to `(column + 1, row - 1)` and
      `(column + 1, row + 1)`, while `"nw"` and `"sw"` point to
      `(column, row - 1)` and `(column, row + 1)`.
    * Even rows: `"no"` and `"so"` point to `(column, row - 1)` and
      `(column, row + 1)`, while `"nw"` and `"sw"` point to
      `(column - 1, row - 1)` and `(column - 1, row + 1)`.

    `"o"` and `"w"` always point to `(column + 1, row)` and
    `(column - 1, row)`.

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

    def _setup_tiles(self):
        """Add a tile for each world position, without per-add cache work.

        `add_tile_to_world` bumps the structure version and drops the
        position-pixel cache on every call. Both are pure overhead while the
        world model is built, because no lookup can run before setup
        finishes; they run once at the end instead of once per tile.
        """
        tiles = self.tiles
        tile_cls = self.tile_factory.tile_cls
        for column in range(self.world_size_x):
            for row in range(self.world_size_y):
                tile = tile_cls((column, row), self)
                tiles[tile.position] = tile
        tile_elements.TileBase.invalidate_position_pixel_cache(self)
        self._tile_structure_version += 1

    def _setup_corners(self):
        """Add and merge all corners, keyed without discarded objects.

        `add_corner_to_world` constructs a `HexCorner` for every
        (tile, direction) pair and merges about two thirds of them away.
        Here the merged key is computed first (pure math) and only the
        first instance of each corner is constructed; further references
        are appended exactly like `TileBase.merge` does.
        """
        corners = self.corners
        _tile_cls, _edge_cls, corner_cls = self._templates()
        for tile_position in list(self.tiles):
            for direction in hex_coords.CORNER_DIRECTIONS:
                corner_position = hex_coords.corner_position(tile_position, direction)
                corner = corners.get(corner_position)
                if corner is None:
                    corners[corner_position] = corner_cls(
                        tile_position, direction, self
                    )
                else:
                    reference = (corner_position, direction)
                    if reference not in corner.positions:
                        corner.positions.append(reference)
        tile_elements.TileBase.invalidate_position_pixel_cache(self)
        self._tile_structure_version += 1

    def _setup_edges(self):
        """Add and merge all edges, keyed without discarded objects.

        Same key-first strategy as `_setup_corners`: only the first instance
        of each edge is constructed, further references are appended like
        `TileBase.merge` does.
        """
        edges = self.edges
        _tile_cls, edge_cls, _corner_cls = self._templates()
        for tile_position in list(self.tiles):
            for direction in hex_coords.EDGE_DIRECTIONS:
                edge_position = hex_coords.edge_position(tile_position, direction)
                edge = edges.get(edge_position)
                if edge is None:
                    edges[edge_position] = edge_cls(tile_position, direction, self)
                else:
                    reference = (edge_position, direction)
                    if reference not in edge.positions:
                        edge.positions.append(reference)
        tile_elements.TileBase.invalidate_position_pixel_cache(self)
        self._tile_structure_version += 1

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

    def _world_pixel_from_screen(self, position) -> Tuple[float, float]:
        """Translate a screen (mouse) pixel into world pixel coordinates.

        Mouse events deliver window coordinates. The camera view is
        drawn at `camera.screen_topleft` in the window and shows the
        world scrolled by `camera.topleft`, while hex geometry is laid
        out in world pixels. Pixel queries must therefore translate the
        pixel before the hex math, so a click picks what is visible at
        the clicked position for scrolled cameras and docked windows.

        With an unscrolled camera at the window origin the translation
        is the identity.
        """
        topleft = self.camera.topleft
        window_topleft = self.camera.screen_topleft
        return (
            position[0] - window_topleft[0] + topleft[0],
            position[1] - window_topleft[1] + topleft[1],
        )

    def _tile_from_world_pixel(self, world_pixel):
        tile_position = hex_coords.cube_to_offset(
            hex_coords.pixel_to_cube(world_pixel, self.tile_size)
        )
        if not self.is_tile(tile_position):
            return None
        return self.tiles[tile_position]

    def _picking_tiles(self, world_pixel):
        """Return the registered tiles whose edges and corners are pickable.

        The pixel usually lies on a registered tile; its six edges and
        corners then contain the nearest edge and corner to the pixel.
        Near the border of the world, the pixel rounds to a position
        outside the world, although registered edges and corners lie
        visually on it (the rim of the board area belongs to the border
        hexes). The registered neighbours are candidates instead, so
        edges and corners on the border of the world remain clickable.
        """
        tile = self._tile_from_world_pixel(world_pixel)
        if tile is not None:
            return [tile]
        cube = hex_coords.pixel_to_cube(world_pixel, self.tile_size)
        neighbour_cubes = [
            (cube[0] + vector[0], cube[1] + vector[1], cube[2] + vector[2])
            for vector in hex_coords.CUBE_DIRECTIONS.values()
        ]
        tiles = []
        seen_positions = set()
        for candidate in [cube] + neighbour_cubes:
            tile_position = hex_coords.cube_to_offset(candidate)
            if tile_position in seen_positions:
                continue
            if self.is_tile(tile_position):
                seen_positions.add(tile_position)
                tiles.append(self.tiles[tile_position])
        return tiles

    def get_tile_from_pixel(self, position):
        """Return the hex tile under a screen pixel.

        The pixel is translated to world pixels first, so the query
        also works while the camera is scrolled or the world is docked
        next to other worlds.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            The registered hex tile under the pixel (the same object as
            `world.get_tile(...)`), or `None` if the pixel lies outside
            the world (no tile exists at the rounded hex position).

        Examples:
            ::

                tile = world.get_tile_from_pixel((80, 120))
                if tile is not None:
                    tile.fill_color = (255, 0, 0)
        """
        return self._tile_from_world_pixel(self._world_pixel_from_screen(position))

    def get_from_pixel(self, position):
        """Return the hex position for a screen pixel.

        The pixel is translated to world pixels first, so the query
        also works while the camera is scrolled or the world is docked
        next to other worlds.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            Hex position as `(column, row)`, or `None` if the pixel
            lies outside the camera view or outside the world.

        Examples:
            ::

                hex_position = world.get_from_pixel((80, 120))
        """
        world_pixel = self._world_pixel_from_screen(position)
        if not self.camera.get_rect().collidepoint(world_pixel):
            return None
        tile = self._tile_from_world_pixel(world_pixel)
        if tile is None:
            return None
        return tile.position

    def get_actors_from_pixel(self, position):
        """Return all actors under a screen pixel.

        Actors on the hex tile under the pixel are returned, plus actors
        on corners or edges whose center lies within the detection radius
        (`tile_size / 3`, same as `actor.detect_pixel`) of the pixel.

        The pixel is translated to world pixels first, so the query
        also works while the camera is scrolled or the world is docked
        next to other worlds. Corner and edge actors are detected
        without a tile under the pixel, so roads and settlements on
        the border of the world remain clickable.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            Actors located under the pixel. An empty list if no actor
            is under the pixel.

        Examples:
            ::

                actors = world.get_actors_from_pixel(mouse_pos)
        """
        world_pixel = self._world_pixel_from_screen(position)
        tile = self._tile_from_world_pixel(world_pixel)
        actors = list(self.detect_actors(tile.position)) if tile is not None else []
        radius = (
            self.tile_size
            * hex_world_sensor_manager.HexWorldSensorManager.DETECTION_RADIUS_FACTOR
        )
        squared_radius = radius * radius
        for actor in self.actors:
            actor_position = actor.position
            if self.is_corner(actor_position):
                center = self.get_corner(actor_position).to_pixel()
            elif self.is_edge(actor_position):
                center = self.get_edge(actor_position).to_pixel()
            else:
                continue
            if (
                (center[0] - world_pixel[0]) ** 2
                + (center[1] - world_pixel[1]) ** 2
                <= squared_radius
            ):
                actors.append(actor)
        return actors

    def get_corner_from_pixel(self, position):
        """Return the corner nearest to a screen pixel.

        The pixel is translated to world pixels first, so the query
        also works while the camera is scrolled or the world is docked
        next to other worlds. Pixels near the border of the world pick
        from the border hexes, so corners on the border (settlement
        positions on a Catan board) remain clickable.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            The nearest corner, or `None` if the pixel is outside
            the camera view or outside the world.

        Examples:
            ::

                corner = world.get_corner_from_pixel(mouse_pos)
        """
        world_pixel = self._world_pixel_from_screen(position)
        if not self.camera.get_rect().collidepoint(world_pixel):
            return None
        nearest_corner = None
        nearest_distance = None
        for tile in self._picking_tiles(world_pixel):
            for direction in hex_coords.CORNER_ORDER:
                corner = self.get_corner(tile.position, direction)
                corner_pixel = corner.to_pixel()
                distance = (
                    (corner_pixel[0] - world_pixel[0]) ** 2
                    + (corner_pixel[1] - world_pixel[1]) ** 2
                )
                if nearest_distance is None or distance < nearest_distance:
                    nearest_corner = corner
                    nearest_distance = distance
        return nearest_corner

    def get_edge_from_pixel(self, position):
        """Return the edge nearest to a screen pixel.

        The pixel is translated to world pixels first, so the query
        also works while the camera is scrolled or the world is docked
        next to other worlds. Pixels near the border of the world pick
        from the border hexes, so edges on the border (road positions
        on a Catan board) remain clickable.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            The nearest edge, or `None` if the pixel is outside
            the camera view or outside the world.

        Examples:
            ::

                edge = world.get_edge_from_pixel(mouse_pos)
        """
        world_pixel = self._world_pixel_from_screen(position)
        if not self.camera.get_rect().collidepoint(world_pixel):
            return None
        nearest_edge = None
        nearest_distance = None
        for tile in self._picking_tiles(world_pixel):
            for direction in hex_coords.CUBE_DIRECTIONS:
                edge = self.get_edge(tile.position, direction)
                edge_pixel = edge.to_pixel()
                distance = (
                    (edge_pixel[0] - world_pixel[0]) ** 2
                    + (edge_pixel[1] - world_pixel[1]) ** 2
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

    def view_position_ranges(self, camera_rect):
        """Return position ranges covering `camera_rect` for index queries.

        Positions on a hex world live in three different coordinate spaces:
        tiles in offset coordinates `(column, row)`, corners in tripled cube
        coordinates, and edges in doubled cube coordinates. The chunk key of
        the tiled spatial index is derived from the raw position, so one
        range per space is returned. Every actor whose pixel rect may
        intersect the camera rect is covered by one of the ranges, while
        each range stays bounded by the visible window.

        Args:
            camera_rect: Camera rectangle in world pixels.

        Returns:
            A list of `((min_x, min_y), (max_x, max_y))` position pair
            ranges, covering tile, corner, and edge positions.

        Examples:
            ::

                ranges = world.view_position_ranges(world.camera.rect)
        """
        tile_size = self.tile_size
        width = hex_coords.hex_width(tile_size)
        row_height = 1.5 * tile_size
        # A hex bounding box (width x 2 * tile_size) must intersect the
        # camera rect. The +/-1 margins also cover the hexes that share
        # only a corner or an edge with a visible hex.
        col0 = int((camera_rect.left - 2 * width) // width) - 1
        col1 = int(camera_rect.right // width) + 1
        row0 = int((camera_rect.top - 2 * tile_size) // row_height) - 1
        row1 = int(camera_rect.bottom // row_height) + 1
        tile_range = ((col0 - 1, row0 - 1), (col1 + 1, row1 + 1))
        # Corners sit at 3 * cube + corner vector (components up to 2),
        # edges at 2 * cube + direction vector (components up to 1). Both
        # inherit the cube range of the visible offset range.
        cubes = [
            hex_coords.offset_to_cube(position)
            for position in ((col0, row0), (col0, row1), (col1, row0), (col1, row1))
        ]
        q_min = min(cube[0] for cube in cubes)
        q_max = max(cube[0] for cube in cubes)
        r_min = min(cube[1] for cube in cubes)
        r_max = max(cube[1] for cube in cubes)
        corner_range = ((3 * q_min - 2, 3 * r_min - 2), (3 * q_max + 2, 3 * r_max + 2))
        edge_range = ((2 * q_min - 1, 2 * r_min - 1), (2 * q_max + 1, 2 * r_max + 1))
        return [tile_range, corner_range, edge_range]

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
        if direction is not None:
            position = hex_coords.corner_position(position, direction)
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
        if direction is not None:
            position = hex_coords.edge_position(position, direction)
        if position in self.edges:
            return self.edges[position]
        raise miniworlds_exception.EdgeNotFoundError(position)

    def get_tiles_in_radius(self, position, radius: int) -> List[hex_tile_mod.HexTile]:
        """Return all tiles within a hex distance of `radius`.

        Neighbors are computed in cube coordinates, so the result is
        independent of the row parity described in the `HexWorld`
        docstring.

        Args:
            position: Hex position as `(column, row)`.
            radius: Maximum hex distance (0 includes only the tile itself).

        Returns:
            List of tiles within the radius, including the tile itself,
            ordered from the center outwards in ring traversal order.
            Positions outside the world are skipped.

        Examples:
            ::

                neighbours = world.get_tiles_in_radius((3, 3), 1)
        """
        if radius < 0:
            return []
        tiles = []
        for ring_radius in range(radius + 1):
            tiles.extend(self.get_tiles_in_ring(position, ring_radius))
        return tiles

    def get_tiles_in_ring(self, position, radius: int) -> List[hex_tile_mod.HexTile]:
        """Return all tiles at exactly `radius` hex distance.

        Neighbors are computed in cube coordinates, so the result is
        independent of the row parity described in the `HexWorld`
        docstring.

        Args:
            position: Hex position as `(column, row)`.
            radius: Hex distance.

        Returns:
            List of tiles at the given distance, in ring traversal
            order starting at the westernmost hex of the ring.
            Positions outside the world are skipped.

        Examples:
            ::

                ring = world.get_tiles_in_ring((3, 3), 2)
        """
        cube = hex_coords.offset_to_cube(position)
        tiles = []
        for ring_cube in hex_coords.cube_ring(cube, radius):
            tile_position = hex_coords.cube_to_offset(ring_cube)
            if self.is_tile(tile_position):
                tiles.append(self.get_tile(tile_position))
        return tiles
