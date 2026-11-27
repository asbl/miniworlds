from __future__ import annotations

from numbers import Real
from typing import Callable, Dict, List, Optional, Tuple

import miniworlds.base.api_validation as api_validation
import miniworlds.base.exceptions as miniworlds_exception
import miniworlds.worlds.hex_world.hex_camera_manager as hex_camera_manager
import miniworlds.worlds.hex_world.hex_corner as hex_corner_mod
import miniworlds.worlds.hex_world.hex_edge as hex_edge_mod
import miniworlds.worlds.hex_world.hex_tile as hex_tile_mod
import miniworlds.worlds.hex_world.hex_tile_factory as hex_tile_factory
import miniworlds.worlds.hex_world.hex_pathfinding as hex_pathfinding
import miniworlds.worlds.hex_world.hex_world_connector as hex_world_connector
import miniworlds.worlds.hex_world.hex_world_sensor_manager as hex_world_sensor_manager
import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.tiled_world.tile_elements as tile_elements
import miniworlds.worlds.tiled_world.tiled_world as tiled_world


def _components_2d(value, parameter_name: str, what: str):
    """Return the two numeric components of a 2D value, validating the input.

    Accepts `(x, y)` sequences and objects with numeric `x`/`y` attributes
    (like `pygame.Vector2`).
    """
    example = f"{parameter_name} = (80, 120)" if what == "pixel" else f"{parameter_name} = (2, 3)"

    def invalid():
        raise TypeError(
            api_validation.with_try_hint(
                f"{parameter_name} must be a {what}, got "
                f"{type(value).__name__}: {value!r}",
                example,
            )
        )

    if isinstance(value, (str, bytes)):
        invalid()
    if hasattr(value, "__len__"):
        if len(value) != 2:
            invalid()
        components = (value[0], value[1])
    elif hasattr(value, "x") and hasattr(value, "y"):
        components = (value.x, value.y)
    else:
        invalid()
    for index, component in enumerate(components):
        api_validation.ensure_real(
            component, f"{parameter_name}[{index}]", api_validation.with_try_hint, example
        )
    return components


def _ensure_pixel(position, parameter_name: str = "position") -> None:
    """Validate a screen pixel `(x, y)` with a beginner-friendly error."""
    _components_2d(position, parameter_name, "pixel (x, y)")


def _as_tile_list(tiles):
    """Accept a single tile or hex position, or an iterable of them."""
    if hasattr(tiles, "position"):
        return [tiles]
    if (
        isinstance(tiles, tuple)
        and len(tiles) == 2
        and all(isinstance(component, Real) and not isinstance(component, bool) for component in tiles)
    ):
        return [tiles]
    return tiles


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
        # Highlights and hover state must exist before the base class builds
        # the background, because the background reads them while rendering.
        self._tile_highlights: Dict[Tuple[int, int], Tuple[int, ...]] = {}
        self._hovered_tile = None
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

    def add_tile_to_world(self, position):
        """Create and register a hex tile at a world grid position.

        Args:
            position: Tile position as `(column, row)` of whole numbers.

        Returns:
            The created tile instance.

        Raises:
            TypeError: If `position` is not a `(column, row)` pair of
                whole numbers.

        Examples:
            ::

                tile = world.add_tile_to_world((2, 3))
        """
        position = hex_coords.to_offset(position)
        return super().add_tile_to_world(position)

    def to_pixel(self, position, size=(0, 0), origin=(0, 0)):
        """Convert a hex position to its pixel position.

        Args:
            position: Hex position as `(column, row)`, or a corner/edge
                key (3-tuple) of this world, which maps to the corner or
                edge pixel (e.g. `world.to_pixel(actor.position)` also
                works for actors on corners and edges).
            size: Reserved for compatibility.
            origin: Pixel offset added to the converted position.

        Returns:
            Pixel position as `(x, y)`.

        Raises:
            TypeError: If `position` is neither a `(column, row)` pair nor
                a corner/edge key of this world.

        Examples:
            ::

                pixel = world.to_pixel((2, 3))
        """
        if (
            not isinstance(position, (str, bytes))
            and hasattr(position, "__len__")
            and len(position) == 3
        ):
            if self.is_corner(position):
                pixel = self.corners[position].to_pixel()
            elif self.is_edge(position):
                pixel = self.edges[position].to_pixel()
            else:
                raise TypeError(
                    f"{position!r} is not a corner or edge position of this world.\n"
                    "Try: world.to_pixel((2, 3)) or "
                    "world.to_pixel(world.get_corner((2, 3), 'n').position)"
                )
            return (pixel[0] + origin[0], pixel[1] + origin[1])
        try:
            column, row = _components_2d(position, "position", "(column, row) position")
        except TypeError:
            raise TypeError(
                api_validation.with_try_hint(
                    f"position must be a (column, row) tuple, a corner key, or an "
                    f"edge key, got {type(position).__name__}: {position!r}",
                    "world.to_pixel((2, 3))",
                )
            ) from None
        center = hex_coords.hex_center((column, row), self.tile_size)
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
        _ensure_pixel(position)
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
                    tile.highlight()
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
        hint = ""
        if direction is None and self.is_tile(position):
            hint = (
                "A tile position needs a corner direction, "
                "e.g. world.get_corner((3, 3), 'n')."
            )
        raise miniworlds_exception.CornerNotFoundError(position, hint)

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
        hint = ""
        if direction is None and self.is_tile(position):
            hint = (
                "A tile position needs an edge direction, "
                "e.g. world.get_edge((3, 3), 'o')."
            )
        raise miniworlds_exception.EdgeNotFoundError(position, hint)

    def get_tiles_in_radius(
        self, position, radius: int, include_center: bool = True
    ) -> List[hex_tile_mod.HexTile]:
        """Return all tiles within a hex distance of `radius`.

        The result is independent of the row parity described in the
        `HexWorld` docstring. Offsets of a ring are computed once per row
        parity and radius, so repeated queries are cheap.

        Args:
            position: Hex position `(column, row)`, a tile, or an actor.
            radius: Maximum hex distance (0 includes only the tile itself).
            include_center: If `False`, the tile at `position` is left out.

        Returns:
            List of tiles within the radius, ordered from the center
            outwards in ring traversal order. Positions outside the world
            are skipped.

        Raises:
            TypeError: If `radius` or `position` has the wrong type.

        Examples:
            ::

                neighbours = world.get_tiles_in_radius((3, 3), 1)
                around = world.get_tiles_in_radius((3, 3), 2, include_center=False)
        """
        position = hex_coords.to_offset(position)
        radius = self._checked_radius(radius)
        if radius > self.world_size_x + self.world_size_y:
            radius = min(radius, self._max_distance(position))
        tiles = self._tiles_at_offset_deltas(
            position, hex_coords.disc_offset_deltas, radius
        )
        if not include_center and tiles:
            tiles = tiles[1:] if tiles[0].position == position else tiles
        return tiles

    def get_tiles_in_ring(self, position, radius: int) -> List[hex_tile_mod.HexTile]:
        """Return all tiles at exactly `radius` hex distance.

        The result is independent of the row parity described in the
        `HexWorld` docstring.

        Args:
            position: Hex position `(column, row)`, a tile, or an actor.
            radius: Hex distance.

        Returns:
            List of tiles at the given distance, in ring traversal
            order starting at the westernmost hex of the ring.
            Positions outside the world are skipped.

        Raises:
            TypeError: If `radius` or `position` has the wrong type.

        Examples:
            ::

                ring = world.get_tiles_in_ring((3, 3), 2)
        """
        position = hex_coords.to_offset(position)
        radius = self._checked_radius(radius)
        if radius > self.world_size_x + self.world_size_y and radius > self._max_distance(position):
            return []
        return self._tiles_at_offset_deltas(
            position, hex_coords.ring_offset_deltas, radius
        )

    def get_distance(self, first, second) -> int:
        """Return the hex distance (number of steps) between two hexes.

        The distance does not depend on the row parity and ignores
        blocked tiles; use `find_path` to count steps around obstacles.

        Args:
            first: Hex position, tile, or actor.
            second: Hex position, tile, or actor.

        Returns:
            The number of hexes you have to step from `first` to `second`.

        Examples:
            ::

                if world.get_distance(robot, goal) <= 2:
                    print("Goal in reach")
        """
        return hex_coords.hex_distance(
            hex_coords.to_offset(first), hex_coords.to_offset(second)
        )

    def get_tiles_in_line(self, start, end) -> List[hex_tile_mod.HexTile]:
        """Return the tiles on the straight line between two hexes.

        Both ends are included. Positions of the line outside the world
        are skipped. Together with `tile.is_blocking` this answers
        line-of-sight questions.

        Args:
            start: Hex position, tile, or actor.
            end: Hex position, tile, or actor.

        Returns:
            The tiles from `start` to `end`.

        Examples:
            ::

                visible = all(
                    not tile.is_blocking
                    for tile in world.get_tiles_in_line(archer, target)
                )
        """
        first = hex_coords.offset_to_cube(hex_coords.to_offset(start))
        last = hex_coords.offset_to_cube(hex_coords.to_offset(end))
        tiles = self.tiles
        found = []
        for cube in hex_coords.cube_line(first, last):
            tile = tiles.get(hex_coords.cube_to_offset(cube))
            if tile is not None:
                found.append(tile)
        return found

    @staticmethod
    def _checked_radius(radius) -> int:
        api_validation.ensure_int(
            radius,
            "radius",
            api_validation.with_try_hint,
            "world.get_tiles_in_radius((3, 3), 2)",
        )
        return radius

    def _tiles_at_offset_deltas(self, position, deltas_for, radius: int) -> List[hex_tile_mod.HexTile]:
        """Return the existing tiles at the offset deltas of a ring or disc.

        The deltas depend only on the row parity, so each hex is found with
        one tuple addition and one dictionary lookup.
        """
        if radius < 0:
            return []
        column, row = position
        tiles = self.tiles
        found = []
        for delta_column, delta_row in deltas_for(row, radius):
            tile = tiles.get((column + delta_column, row + delta_row))
            if tile is not None:
                found.append(tile)
        return found

    def _max_distance(self, position) -> int:
        """Return an upper bound for the distance from `position` to any tile.

        Rings and discs beyond this distance contain no tile, so huge radii
        do not walk (and cache) rings far outside the world. It is only
        needed for radii larger than the world itself. The farthest
        tile of a rectangular world is at one of its corners; the margin of
        two rings covers the zigzag of the odd-r offset layout.
        """
        cube = hex_coords.offset_to_cube(position)
        last_column, last_row = self.world_size_x - 1, self.world_size_y - 1
        corners = ((0, 0), (last_column, 0), (0, last_row), (last_column, last_row))
        return 2 + max(
            hex_coords.cube_distance(cube, hex_coords.offset_to_cube(corner))
            for corner in corners
        )

    # ------------------------------------------------------------------
    # Path finding
    # ------------------------------------------------------------------

    def find_path(
        self,
        start,
        goal,
        blocked: Optional[Callable[[hex_tile_mod.HexTile], bool]] = None,
        cost: Optional[Callable[[hex_tile_mod.HexTile], float]] = None,
        max_cost: Optional[float] = None,
        min_cost: Optional[float] = None,
    ) -> List[hex_tile_mod.HexTile]:
        """Return the cheapest path between two hexes.

        Entering a tile costs `tile.cost` (default `1`). A tile is
        impassable if `tile.is_blocking` is set or an actor with
        `is_blocking = True` stands on it. The goal must be passable.

        Args:
            start: Start hex as position, tile, or actor.
            goal: Goal hex as position, tile, or actor.
            blocked: Optional function `blocked(tile) -> bool` that replaces
                the default blocking rule.
            cost: Optional function `cost(tile) -> float` that replaces
                `tile.cost`. Costs must not be negative.
            max_cost: Optional budget; more expensive paths are not returned.
            min_cost: Cheapest step cost of a custom `cost` function; speeds
                up the search. Too large values can return non-optimal paths.

        Returns:
            The tiles from start to goal, both included, or an empty list
            if there is no path.

        Raises:
            TileNotFoundError: If start or goal is not a tile of the world.

        Examples:
            ::

                world.get_tile((2, 2)).is_blocking = True   # water
                path = world.find_path((0, 0), (5, 4))
                for tile in path:
                    tile.highlight()
        """
        return hex_pathfinding.find_path(
            self, start, goal, blocked=blocked, cost=cost,
            max_cost=max_cost, min_cost=min_cost,
        )

    def get_reachable_tiles(
        self,
        start,
        max_cost: float,
        blocked: Optional[Callable[[hex_tile_mod.HexTile], bool]] = None,
        cost: Optional[Callable[[hex_tile_mod.HexTile], float]] = None,
    ) -> List[hex_tile_mod.HexTile]:
        """Return all hexes reachable within a movement budget.

        With default costs `max_cost` is the number of steps; blocked
        tiles are walked around, so the result can be smaller than
        `get_tiles_in_radius`.

        Args:
            start: Start hex as position, tile, or actor.
            max_cost: Movement budget.
            blocked: Optional `blocked(tile) -> bool`, see `find_path`.
            cost: Optional `cost(tile) -> float`, see `find_path`.

        Returns:
            The reachable tiles including the start tile, ordered from
            the cheapest to the most expensive.

        Examples:
            ::

                for tile in world.get_reachable_tiles(robot.position, 3):
                    tile.highlight((0, 200, 0, 80))
        """
        return hex_pathfinding.get_reachable_tiles(
            self, start, max_cost, blocked=blocked, cost=cost
        )

    def find_nearest(
        self,
        start,
        is_target: Callable[[hex_tile_mod.HexTile], bool],
        blocked: Optional[Callable[[hex_tile_mod.HexTile], bool]] = None,
        cost: Optional[Callable[[hex_tile_mod.HexTile], float]] = None,
        max_cost: Optional[float] = None,
        include_start: bool = False,
    ) -> List[hex_tile_mod.HexTile]:
        """Return the path to the nearest hex that satisfies `is_target`.

        The nearest hex is the cheapest one to reach, not the one with the
        smallest hex distance. A target may be blocked (for example an
        enemy that blocks its hex): the path ends on it.

        Args:
            start: Start hex as position, tile, or actor.
            is_target: Function `is_target(tile) -> bool`.
            blocked: Optional `blocked(tile) -> bool`, see `find_path`.
            cost: Optional `cost(tile) -> float`, see `find_path`.
            max_cost: Optional budget; more expensive targets are ignored.
            include_start: If `True`, the start hex can be the target.

        Returns:
            The tiles from start to the nearest target, both included,
            or an empty list if no target is reachable.

        Examples:
            ::

                path = world.find_nearest(robot, lambda tile: tile.terrain == "forest")
                if path:
                    robot.position = path[1].position
        """
        return hex_pathfinding.find_nearest(
            self, start, is_target, blocked=blocked, cost=cost,
            max_cost=max_cost, include_start=include_start,
        )

    def has_line_of_sight(
        self,
        start,
        goal,
        blocked: Optional[Callable[[hex_tile_mod.HexTile], bool]] = None,
    ) -> bool:
        """Return whether no blocked hex lies on the line between two hexes.

        The line is the one of `get_tiles_in_line`. Only the hexes strictly
        between start and goal count; a blocked goal can still be seen.

        Args:
            start: Start hex as position, tile, or actor.
            goal: Goal hex as position, tile, or actor.
            blocked: Optional `blocked(tile) -> bool`, see `find_path`.

        Examples:
            ::

                if world.has_line_of_sight(guard, player):
                    print("spotted")
        """
        return hex_pathfinding.has_line_of_sight(self, start, goal, blocked=blocked)

    def get_path_cost(
        self,
        path,
        cost: Optional[Callable[[hex_tile_mod.HexTile], float]] = None,
    ) -> float:
        """Return the cost of a path (the first hex is not counted).

        Args:
            path: A list of tiles, for example the result of `find_path`.
            cost: Optional `cost(tile) -> float`, see `find_path`.

        Examples:
            ::

                path = world.find_path((0, 0), (5, 3))
                print(world.get_path_cost(path))
        """
        return hex_pathfinding.get_path_cost(path, cost=cost)

    # ------------------------------------------------------------------
    # Highlights and hover
    # ------------------------------------------------------------------

    def highlight_tiles(self, tiles, color: Tuple[int, ...] = (255, 255, 0, 90)) -> None:
        """Highlight hexes with a translucent color.

        The highlights are drawn on the background below the actors and
        stay until `clear_highlights` is called.

        Args:
            tiles: A single tile or hex position, or a list of them.
            color: RGB or RGBA color; with RGB a default transparency is used.

        Examples:
            ::

                world.highlight_tiles(world.get_tiles_in_radius((3, 3), 1))
        """
        color = self._normalize_highlight_color(color)
        changed = False
        for tile in _as_tile_list(tiles):
            position = hex_pathfinding._to_position(tile)
            if self._tile_highlights.get(position) != color:
                self._tile_highlights[position] = color
                changed = True
        if changed:
            self._refresh_highlights()

    def clear_highlights(self, tiles=None) -> None:
        """Remove highlights.

        Args:
            tiles: A single tile or hex position, or a list of them, to
                clear. Without it, all highlights are removed.

        Examples:
            ::

                world.clear_highlights()
        """
        if tiles is None:
            changed = bool(self._tile_highlights)
            self._tile_highlights.clear()
        else:
            changed = False
            for tile in _as_tile_list(tiles):
                if self._tile_highlights.pop(hex_pathfinding._to_position(tile), None) is not None:
                    changed = True
        if changed:
            self._refresh_highlights()

    @staticmethod
    def _ensure_color_component(value, parameter_name: str) -> None:
        api_validation.ensure_real(
            value, parameter_name, api_validation.with_try_hint, f"{parameter_name} = 255"
        )

    @staticmethod
    def _normalize_highlight_color(color) -> Tuple[int, ...]:
        if isinstance(color, list):
            color = tuple(color)
        if not isinstance(color, tuple):
            raise TypeError(
                api_validation.with_try_hint(
                    f"color must be a tuple like (r, g, b) or (r, g, b, a), got "
                    f"{type(color).__name__}: {color!r}",
                    "color = (255, 0, 0)",
                )
            )
        if len(color) not in (3, 4):
            raise ValueError(f"A highlight color needs 3 or 4 components, got {color!r}")
        for index, component in enumerate(color):
            HexWorld._ensure_color_component(component, f"color[{index}]")
        if any(not 0 <= component <= 255 for component in color):
            raise ValueError(
                api_validation.with_try_hint(
                    f"color components must be between 0 and 255, got {color!r}",
                    "color = (255, 255, 0)",
                )
            )
        color = tuple(int(component) for component in color)
        if len(color) == 3:
            return color + (90,)
        return color

    def _refresh_highlights(self) -> None:
        background = getattr(self, "background", None)
        if background is not None:
            background.set_dirty("all", background.LOAD_NEW_IMAGE)

    @property
    def hovered_tile(self):
        """The hex under the mouse, or `None`.

        The value is kept up to date while the world has an
        `on_tile_enter` or `on_tile_leave` handler (or `on_mouse_motion`).

        Examples:
            ::

                @world.register
                def on_tile_enter(self, tile):
                    print(tile.position)
        """
        return self._hovered_tile

    def _update_hovered_tile(self, mouse_pos):
        """Track the hovered hex; return `(left_tile, entered_tile)` on change."""
        new_tile = None if mouse_pos is None else self.get_tile_from_pixel(mouse_pos)
        old_tile = self._hovered_tile
        if new_tile is old_tile:
            return None
        self._hovered_tile = new_tile
        return old_tile, new_tile
