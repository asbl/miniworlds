from collections import defaultdict
from typing import Union, Dict, Tuple, Optional, cast, List
import pygame

import miniworlds.worlds.manager.camera_manager as world_camera_manager

import miniworlds.worlds.world as world
import miniworlds.appearances.background as background_mod
import miniworlds.worlds.tiled_world.tiled_world_camera_manager as tiled_camera_manager
import miniworlds.worlds.tiled_world.corner as corner_mod
import miniworlds.worlds.tiled_world.edge as edge_mod
import miniworlds.worlds.tiled_world.tile as tile_mod
import miniworlds.worlds.tiled_world.tile_factory as tile_factory
import miniworlds.worlds.tiled_world.tiled_world_connector as tiled_world_connector
import miniworlds.actors.actor as actor_mod

import miniworlds.base.exceptions as miniworlds_exception
from miniworlds.base.exceptions import TiledWorldTooBigError


class TiledWorld(world.World):
    """from typing
    A TiledWorld is a World where each Actor is placed in one Tile.

    With Tiled World, you can realize RPGs and Boardgames.

    .. image:: /_images/rpg.jpg
        :alt: TiledWorld

    Each Actor on a TiledWorld can be placed on a Tile, on a Corner between Tiles or on an Edge between Tiles.

    Examples:

        Create Actor on Tile, Corner and Edge:

        .. code-block::

            from miniworlds import *
            world = TiledWorld(6, 3)
            world.grid = True
            last_corner = None

            tile = Tile((1,1))
            t1 = Actor()
            t1.center = tile.position
            t1.fill_color = (255,255,255)

            corner = Corner((3,1), "nw")
            t2 = Actor()
            t2.center = corner.position
            t2.fill_color = (255,0,0)

            edge = Edge((5,1), "w")
            t3 = Actor()
            t3.center = edge.position
            t3.fill_color = (0,0,255)
            t3.size = (0.2,1)
            t3.direction = edge.angle

            world.run()

    """

    def __init__(self, x: int = 20, y: int = 16, tile_size: int = 40, empty=False):
        """Initializes the TiledWorld

        Args:
            view_x: The number of columns
            view_y: The number of rows
            empty: The world has no tiles, edges, and corners. They must be created manually
        """
        self._tile_size: int = tile_size
        "TiledWorld.tile_size Defines the size of a single tile (All Tiles are square)"
        self.default_actor_speed: int = 1
        self.empty = empty
        self.tile_factory = self._get_tile_factory()
        self.tiles: defaultdict = defaultdict()
        self.corners: defaultdict = defaultdict()
        self.edges: defaultdict = defaultdict()
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
        self.actors_fixed_size = True
        self.rotatable_actors = True
        self.is_tiled = True

    def _get_tile_factory(self):
        return tile_factory.TileFactory()

    def clear_tiles(self):
        """Removes all tiles, corners and edges from World

        Instead of clearing the world, you can add the parameter empty to World to create a new World from scratch.

        Examples:

            Clear and re-create world:

            .. code-block:: python

                from miniworlds import *
                world = HexWorld(8, 8)

                @world.register
                def on_setup(self):
                    self.clear_tiles()
                    center = HexTile((4, 4))
                    for x in range(self.columns):
                        for y in range(self.rows):
                            if center.position.distance((x, y)) < 2:
                                tile = self.add_tile_to_world((x, y))
                                tt = Actor()
                                t.center = tile.position


                world.run()


            Create a new world from scratch

            .. note::

                This variant is faster, because Tiles are not created twice

            .. code-block:: python

                from miniworlds import *
                world = HexWorld(8, 8, empty=True)

                @world.register
                def on_setup(self):
                    center = HexTile((4, 4))
                    for x in range(self.columns):
                        for y in range(self.rows):
                            if center.position.distance((x, y)) < 2:
                                tile = self.add_tile_to_world((x, y))
                                tile.create_actor()


                world.run()
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
        tile_cls, edge_cls, corner_cls = self._templates()
        tile_pos = position
        tile = tile_cls(tile_pos, self)
        self.tiles[tile.position] = tile
        return tile

    def add_corner_to_world(self, position, direction):
        tile_cls, edge_cls, corner_cls = self._templates()
        corner = corner_cls(position, direction, self)
        corner_pos = corner.position
        if corner_pos not in self.corners:
            self.corners[corner_pos] = corner
        else:
            self.corners[corner_pos].merge(corner)
        return self.corners[corner_pos]

    def add_edge_to_world(self, position, direction):
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
        """Gets Tile at Position.

        Raises TileNotFoundError, if Tile does not exists.

        Examples:

            Get tile from actor:

            .. code-block:: python

                tile = world.get_tile(actor.position)

            Full example:

            .. code-block:: python

                from miniworlds import *

                world = TiledWorld(6, 3)
                world.grid = True
                last_corner = None

                tile = Tile((1,1))
                t1 = Actor()
                t1.center = tile.position
                t1.fill_color = (255,255,255)

                tile=world.get_tile((1,1))
                assert(tile.get_actors()[0] == t1)

                world.run()

        :param position: Position on World
        :return: Tile on Position, if position exists
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
        """Gets Corner at Position.

        Raises CornerNotFoundError, if Tile does not exists.

        Examples:

            Get corner from actor:

            .. code-block:: python

                corner = world.get_corner(actor.position)

            Get corner from world-position and direction

            .. code-block:: python

                from miniworlds import *

                from miniworlds import *
                world = TiledWorld(6, 3)
                world.grid = True
                last_corner = None

                corner = Corner((3,1), "nw")
                t2 = Actor()
                t1.center = corner.position
                t2.fill_color = (255,0,0)

                corner=world.get_corner((3,1),"nw")
                assert(corner.get_actors()[0] == t2)

                world.run()

        Args:
            position: Position on World
            direction: if direction is not None, position is interpreted as tile-world-position

        Returns
            next corner, if position exists
        """
        corner_cls = self.tile_factory.corner_cls
        if direction is not None:
            position = corner_cls(position, direction).position
        if self.is_corner(position):
            return self.corners[(position[0], position[1])]
        else:
            raise miniworlds_exception.CornerNotFoundError(position)

    def get_edge(self, position, direction: Optional[str] = None):
        """Gets Edge at Position.

        Raises EdgeNotFoundError, if Tile does not exists.

        Examples:

            Get edge from actor:

            .. code-block:: python

                tile = world.get_edge(actor.position)

            Get edge from world-position and direction

            .. code-block:: python

                from miniworlds import *
                world = TiledWorld(6, 3)
                world.grid = True
                last_corner = None

                edge=world.get_edge((5,1),"w")
                assert(edge.get_actors()[0] == t3)

                world.run()

        :param position: Position on World
        :return: Edge on Position, if position exists
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
        """
        Returns the World's borders, if actor is near a Border.
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
            x, y = actor.position[0], actor.position[1]
            self._dynamic_actors_dict[(x, y)].append(actor)

    def detect_actors_at_position(self, position):
        """Sensing actors at same position"""
        self._update_actor_positions()  # This method can be a bottleneck!
        actor_list = []
        if self._dynamic_actors_dict[position[0], position[1]]:
            actor_list.extend(self._dynamic_actors_dict[(position[0], position[1])])
        if self.static_actors_dict[position[1], position[1]]:
            actor_list.extend(self.static_actors_dict[(position[0], position[1])])
        actor_list = [actor for actor in actor_list]
        return actor_list

    def detect_actor_at_position(self, position):
        """Sensing single actor at same position

        Faster than sensing_actors, but only the first found actor is recognized.
        """
        actor_list = self.detect_actors_at_position(position)
        if actor_list is None or actor_list == []:
            return None
        else:
            return actor_list[0]

    @property
    def grid(self):
        """Displays grid overlay on background."""
        return self.background.grid

    @grid.setter
    def grid(self, value):
        self.background.grid = value

    def draw_on_image(self, image, position):
        position = self.to_pixel(position)
        self.background.draw_on_image(image, position, self.tile_size, self.tile_size)

    def get_from_pixel(self, position):
        """Gets world position from pixel coordinates"""
        if position[0] > self.camera.height or position[1] > self.camera.height:
            return None
        else:
            return self.get_tile_from_pixel(position).position

    def get_tile_from_pixel(self, position):
        """Gets nearest Tile from pixel"""
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
        """Returns True, if position is a edge."""
        if position in self.edges:
            return True
        else:
            return False

    def is_corner(self, position):
        """Returns True, if position is a corner."""
        if position in self.corners:
            return True
        else:
            return False

    def is_tile(self, position):
        """Returns True, if position is a tile."""
        if position in self.tiles:
            return True
        else:
            return False

    def to_pixel(self, position, size=(0, 0), origin=(0, 0)):
        """Converts WorldPosition to pixel coordinates"""
        x = position[0] * self.tile_size + origin[0]
        y = position[1] * self.tile_size + origin[1]
        return x, y

    def set_columns(self, value: int):
        self._columns = value
        self.camera.width = value #* self.tile_size
        self.world_size_x = value

    def set_rows(self, value: int):
        self._rows = value
        self.camera.height = value #* self.tile_size
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
        """Tile size of each tile, if world has tiles

        Returns:
            The tile-size in pixels.
        """
        return self._tile_size

    @tile_size.setter
    def tile_size(self, value: int):
        self.set_tile_size(value)

    def set_tile_size(self, value):
        self._tile_size = value
        self.camera._reload_camera()
        self.background.set_dirty("all", background_mod.Background.RELOAD_ACTUAL_IMAGE)