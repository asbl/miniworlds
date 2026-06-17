from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union, cast

import pygame

import miniworlds.actors.actor as actor_mod
import miniworlds.appearances.background as background_mod
import miniworlds.base.exceptions as miniworlds_exception
import miniworlds.worlds.manager.camera_manager as world_camera_manager
import miniworlds.worlds.tiled_world.corner as corner_mod
import miniworlds.worlds.tiled_world.edge as edge_mod
import miniworlds.worlds.tiled_world.tile as tile_mod
import miniworlds.worlds.tiled_world.tile_factory as tile_factory
import miniworlds.worlds.tiled_world.tiled_world_camera_manager as tiled_camera_manager
import miniworlds.worlds.tiled_world.tiled_world_connector as tiled_world_connector
import miniworlds.worlds.world as world
from miniworlds.base.exceptions import TiledWorldTooBigError


class TiledWorld(world.World):
    """Grid-based world where actors are placed on tiles.

    A `TiledWorld` uses tile coordinates instead of pixel coordinates for actor
    positions. Actors can also be placed on tile corners or edges.

    Examples:
        ::

            Create a small grid world:

                from miniworlds import TiledWorld, Actor

                world = TiledWorld(6, 3)
                player = Actor((1, 1))
                player.fill_color = (255, 255, 255)

                @player.register
                def on_key_down_right(self):
                    self.move_in_direction("right")

                world.run()
    """

    def __init__(self, x: int = 20, y: int = 16, tile_size: int = 40, empty=False):
        """Create a tiled world.

        Args:
            x: Number of columns.
            y: Number of rows.
            tile_size: Tile size in pixels.
            empty: If `True`, tiles, edges, and corners are not created
                automatically.

        Examples:
            ::

                world = TiledWorld(8, 6)
                empty_world = TiledWorld(8, 6, empty=True)
        """
        self._tile_size: int = tile_size
        "TiledWorld.tile_size Defines the size of a single tile (All Tiles are square)"
        self.default_actor_speed: int = 1
        self.empty = empty
        self.tile_factory = self._get_tile_factory()
        self.tiles: defaultdict = defaultdict()
        self.corners: defaultdict = defaultdict()
        self.edges: defaultdict = defaultdict()
        self._static_tile_layer: pygame.Surface | None = None
        self._static_tile_layer_dirty = True
        # Initialize tiled spatial index for efficient actor queries
        self._tiled_spatial_index = None
        if x > 1000 or y > 1000:
            raise TiledWorldTooBigError(x, y, 40)
        super().__init__(x=x, y=y)
        self._tile_size = 40
        self.tick_rate = 20
        self._dynamic_actors_dict: defaultdict = defaultdict(
            list
        )  # the dict is regularly updated
        self._dynamic_actors: "pygame.sprite.Group" = (
            pygame.sprite.Group()
        )  # Set with all dynamic actors
        self.static_actors_dict: defaultdict = defaultdict(list)
        self.rotatable_actors = True
        self.is_tiled = True

    def _get_tile_factory(self):
        return tile_factory.TileFactory()

    def clear_tiles(self):
        """Remove all tiles, corners, and edges.

        Use `empty=True` in the constructor when you want to build all tiles
        manually from the start.

        Examples:
            ::

                world = TiledWorld(8, 8, empty=True)
                world.add_tile_to_world((0, 0))

                world.clear_tiles()
                world.add_tile_to_world((1, 1))
        """
        self.tiles.clear()
        self.corners.clear()
        self.edges.clear()

    @staticmethod
    def _get_camera_manager_class():
        return tiled_camera_manager.TiledCameraManager

    def _after_init_setup(self):
        """In this method, corners and edges are created."""
        if not self.empty:
            self._setup_tiles()
            self._setup_corners()
            self._setup_edges()

    def _templates(self):
        """Returns Classes for Tile, Edge and Corner"""
        return tile_mod.Tile, edge_mod.Edge, corner_mod.Corner

    def add_tile_to_world(self, position):
        """Creates and registers a tile at a world grid position.

        Args:
            position: Tile position as `(column, row)`.

        Returns:
            The created tile instance.

        Examples:
            ::

                tile = world.add_tile_to_world((2, 3))
        """
        tile_cls, edge_cls, corner_cls = self._templates()
        tile_pos = position
        tile = tile_cls(tile_pos, self)
        self.tiles[tile.position] = tile
        return tile

    def add_corner_to_world(self, position, direction):
        """Create and register a corner.

        Existing corners are merged when multiple tiles share the same corner.

        Args:
            position: Base tile position as `(column, row)`.
            direction: Corner direction key, for example `"nw"`.

        Returns:
            The registered corner object.

        Examples:
            ::

                corner = world.add_corner_to_world((2, 3), "nw")
        """
        tile_cls, edge_cls, corner_cls = self._templates()
        corner = corner_cls(position, direction, self)
        corner_pos = corner.position
        if corner_pos not in self.corners:
            self.corners[corner_pos] = corner
        else:
            self.corners[corner_pos].merge(corner)
        return self.corners[corner_pos]

    def add_edge_to_world(self, position, direction):
        """Create and register an edge.

        Existing edges are merged when neighboring tiles describe the same edge.

        Args:
            position: Base tile position as `(column, row)`.
            direction: Edge direction key, for example `"n"` or `"w"`.

        Returns:
            The registered edge object.

        Examples:
            ::

                edge = world.add_edge_to_world((2, 3), "w")
        """
        edge_cls = self.tile_factory.edge_cls
        edge = edge_cls(position, direction, self)
        edge_pos = edge.position
        if edge_pos not in self.edges:
            self.edges[edge_pos] = edge
        else:
            self.edges[edge_pos].merge(edge)
        return self.edges[edge_pos]

    def _setup_tiles(self):
        """Adds Tile to World for each WorldPosition"""
        for x in range(self.world_size_x):
            for y in range(self.world_size_y):
                self.add_tile_to_world((x, y))

    def _setup_corners(self):
        """Add all Corner to World for each Tile.

        Merges identical corners for different Tiles
        """
        tile_cls = self.tile_factory.tile_cls
        for position, tile in self.tiles.items():
            for direction in tile_cls.corner_vectors:
                self.add_corner_to_world(tile.position, direction)

    def _setup_edges(self):
        """Add all Edges to World for each Tile

        Merges identical edges for different tiles
        """
        tile_cls = self.tile_factory.tile_cls
        for position, tile in self.tiles.items():
            for direction in tile_cls.edge_vectors:
                self.add_edge_to_world(tile.position, direction)

    def get_tile(self, position: Tuple[float, float]):
        """Return the tile at a tile position.

        Args:
            position: Tile position as `(column, row)`.

        Returns:
            The tile at the position.

        Raises:
            TileNotFoundError: If no tile exists at the position.

        Examples:
            ::

                tile = world.get_tile(actor.position)
                tile = world.get_tile((1, 1))

                if tile.get_actors():
                    print("Tile is occupied")
        """
        if self.is_tile(position):
            position = position
            return self.tiles[position]
        else:
            raise miniworlds_exception.TileNotFoundError(position)

    def detect_actors(
        self, position: Union[Tuple[float, float], Tuple[float, float]]
    ) -> List["actor_mod.Actor"]:
        return cast(
            List["actor_mod.Actor"],
            [actor for actor in self.actors if actor.position == position],
        )

    def get_actors_from_pixel(
        self, position: Union[Tuple[float, float], Tuple[float, float]]
    ) -> List["actor_mod.Actor"]:
        tile = tile_mod.Tile.from_pixel(position)
        return self.detect_actors(tile.position)

    def get_corner(
        self, position: Tuple[float, float], direction: Optional[str] = None
    ):
        """Return a corner by corner position or tile position plus direction.

        Args:
            position: Corner position, or tile position when `direction` is set.
            direction: Optional corner direction, for example `"nw"`.

        Returns:
            The matching corner.

        Raises:
            CornerNotFoundError: If no corner exists at the resolved position.

        Examples:
            ::

                corner = world.get_corner(actor.position)
                corner = world.get_corner((3, 1), "nw")
        """
        corner_cls = self.tile_factory.corner_cls
        if direction is not None:
            position = corner_cls(position, direction).position
        if self.is_corner(position):
            return self.corners[(position[0], position[1])]
        else:
            raise miniworlds_exception.CornerNotFoundError(position)

    def get_edge(self, position, direction: Optional[str] = None):
        """Return an edge by edge position or tile position plus direction.

        Args:
            position: Edge position, or tile position when `direction` is set.
            direction: Optional edge direction, for example `"n"` or `"w"`.

        Returns:
            The matching edge.

        Examples:
            ::

                edge = world.get_edge(actor.position)
                edge = world.get_edge((5, 1), "w")
        """
        edge_cls = self.tile_factory.edge_cls
        if direction is not None:
            position = edge_cls(position, direction).position
        if self.is_edge(position):
            return self.edges[(position[0], position[1])]
        else:
            raise miniworlds_exception.TileNotFoundError(position)

    @staticmethod
    def _get_world_connector_class():
        return tiled_world_connector.TiledWorldConnector

    def borders(self, value: Union[tuple, Tuple[float, float], pygame.Rect]) -> list:
        """Return borders touched by a position or rectangle.

        Args:
            value: Position or rectangle to check.

        Returns:
            List of border names such as `"left"` or `"top"`.

        Examples:
            ::

                borders = world.borders(actor.position)
        """
        position = value
        return self.get_borders_from_position(position)

    def _update_actor_positions(self):
        """Updates the dynamic_actors_dict.

        All positions of dynamic_actors_dict are updated by reading the dynamic_actors list.

        This method is called very often in self.sensing_actors - The dynamic_actors list should therefore be as small as possible.
        Other actors should be defined as static.
        """
        self._dynamic_actors_dict.clear()
        for actor in self._dynamic_actors:
            # Skip actors that are explicitly marked as static to avoid unnecessary work
            if getattr(actor, "static", False):
                continue
            x, y = actor.position[0], actor.position[1]
            self._dynamic_actors_dict[(x, y)].append(actor)

    def detect_actors_at_position(self, position):
        """Return all actors at a tile position.

        Args:
            position: Tile position as `(column, row)`.

        Returns:
            Actors located at that position.

        Examples:
            ::

                actors = world.detect_actors_at_position((2, 3))
        """
        # Use tiled spatial index if available for better performance
        tiled_spatial_index = getattr(self, "_tiled_spatial_index", None)
        if tiled_spatial_index is not None:
            return list(tiled_spatial_index.query_exact_position(position))

        # Fallback to old method for compatibility
        self._update_actor_positions()  # This method can be a bottleneck!
        actor_list = []
        if self._dynamic_actors_dict[position[0], position[1]]:
            actor_list.extend(self._dynamic_actors_dict[(position[0], position[1])])
        if self.static_actors_dict[position[0], position[1]]:
            actor_list.extend(self.static_actors_dict[(position[0], position[1])])
        actor_list = [actor for actor in actor_list]
        return actor_list

    def detect_actor_at_position(self, position):
        """Return the first actor at a tile position.

        Args:
            position: Tile position as `(column, row)`.

        Returns:
            The first actor at that position, or `None`.

        Examples:
            ::

                actor = world.detect_actor_at_position((2, 3))
        """
        actor_list = self.detect_actors_at_position(position)
        if not actor_list:
            return None
        return actor_list[0]

    def _rebuild_static_tile_layer(self) -> None:
        layer = self.background.image.copy()
        for actor in self.actors:
            if not getattr(actor, "_static", False):
                continue
            if self.event_manager.registry.has_instance_handlers(actor):
                continue
            if not getattr(actor, "visible", True):
                continue
            costume = getattr(actor, "costume", None)
            if costume is None:
                continue
            actor_rect = actor.position_manager.get_global_rect()
            if not self.camera.rect.colliderect(actor_rect):
                continue
            try:
                image = actor.image
            except AttributeError:
                continue
            if image is None:
                continue
            local_rect = actor_rect.move(-self.camera.x, -self.camera.y)
            layer.blit(image, local_rect)
            actor.dirty = 0
        self._static_tile_layer = layer
        self._static_tile_layer_dirty = False

    def _draw_static_tile_layer(self, surface: pygame.Surface) -> bool:
        if not hasattr(self, "actors"):
            return False
        if getattr(self, "background", None) is None:
            return False
        if self._static_tile_layer_dirty or self._static_tile_layer is None:
            self._rebuild_static_tile_layer()
        surface.blit(self._static_tile_layer, (0, 0))
        return True

    def _refresh_static_tile_layer(self) -> tuple[pygame.Surface | None, bool]:
        if not hasattr(self, "actors"):
            return None, False
        if getattr(self, "background", None) is None:
            return None, False
        rebuilt = False
        if self._static_tile_layer_dirty or self._static_tile_layer is None:
            self._rebuild_static_tile_layer()
            rebuilt = True
        return self._static_tile_layer, rebuilt

    @property
    def grid(self):
        """bool: Whether to display the grid overlay.

        Examples:
            ::

                world.grid = True
        """
        return self.background.grid

    @grid.setter
    def grid(self, value):
        self.background.grid = value

    def draw_on_image(self, image, position):
        """Draw an image onto the tiled world background.

        Args:
            image: The image/surface to draw.
            position: Tile position as `(column, row)`.

        Examples:
            ::

                world.draw_on_image(surface, (2, 3))
        """
        position = self.to_pixel(position)
        self.background.draw_on_image(image, position, self.tile_size, self.tile_size)

    def get_from_pixel(self, position):
        """Return the tile position for a screen pixel.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            Tile position, or `None` if the pixel is outside the camera view.

        Examples:
            ::

                tile_position = world.get_from_pixel((80, 120))
        """
        x, y = position
        if x < 0 or y < 0:
            return None
        if x >= self.camera.width or y >= self.camera.height:
            return None
        else:
            return self.get_tile_from_pixel(position).position

    def get_tile_from_pixel(self, position):
        """Return the tile under a screen pixel.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            Tile under the pixel.

        Examples:
            ::

                tile = world.get_tile_from_pixel((80, 120))
        """
        tile_cls = self.tile_factory.tile_cls
        return tile_cls.from_pixel(position, self)

    def get_edge_points(self) -> Dict[Tuple, Tuple[float, float]]:
        edge_points = dict()
        for position, edge in self.edges.items():
            edge_points[position] = edge.to_pixel()
        return edge_points

    def get_corner_points(self) -> Dict[Tuple, Tuple[float, float]]:
        corner_points = dict()
        for position, corner in self.corners.items():
            corner_points[position] = corner.to_pixel()
        return corner_points

    def is_edge(self, position):
        """Return whether a position is an edge position.

        Examples:
            ::

                if world.is_edge(actor.position):
                    actor.hide()
        """
        if position in self.edges:
            return True
        else:
            return False

    def is_corner(self, position):
        """Return whether a position is a corner position.

        Examples:
            ::

                if world.is_corner(actor.position):
                    actor.hide()
        """
        if position in self.corners:
            return True
        else:
            return False

    def is_tile(self, position):
        """Return whether a position is a tile position.

        Examples:
            ::

                if world.is_tile((1, 1)):
                    tile = world.get_tile((1, 1))
        """
        if position in self.tiles:
            return True
        else:
            return False

    def to_pixel(self, position, size=(0, 0), origin=(0, 0)):
        """Convert a tile position to pixel coordinates.

        Args:
            position: Tile position as `(column, row)`.
            size: Reserved for compatibility.
            origin: Pixel offset added to the converted position.

        Returns:
            Pixel position as `(x, y)`.

        Examples:
            ::

                pixel = world.to_pixel((2, 3))
        """
        x = position[0] * self.tile_size + origin[0]
        y = position[1] * self.tile_size + origin[1]
        return x, y

    def set_columns(self, value: int):
        self._columns = value
        self.camera.width = value  # * self.tile_size
        self.world_size_x = value

    def set_rows(self, value: int):
        self._rows = value
        self.camera.height = value  # * self.tile_size
        self.world_size_y = value

    @property
    def columns(self) -> int:
        return self.camera.world_size_x

    @columns.setter
    def columns(self, value: int):
        self.set_columns(value)

    @property
    def rows(self) -> int:
        return self.camera.world_size_y

    @rows.setter
    def rows(self, value: int):
        self.set_rows(value)

    @property
    def tile_size(self) -> int:
        """int: Size of one tile in pixels.

        Examples:
            ::

                world.tile_size = 32
        """
        return self._tile_size

    @tile_size.setter
    def tile_size(self, value: int):
        self.set_tile_size(value)

    def set_tile_size(self, value):
        """Set the tile size in pixels.

        Args:
            value: New tile size in pixels.

        Examples:
            ::

                world.set_tile_size(32)
        """
        self._tile_size = value
        self.camera._reload_camera()
        self.background.set_dirty("all", background_mod.Background.RELOAD_ACTUAL_IMAGE)
