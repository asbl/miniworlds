"""Unit tests for HexWorld: tiles, corners, edges, picking, and queries."""

from __future__ import annotations

import unittest

from miniworlds import Actor, App
from miniworlds.worlds.hex_world.hex_corner import HexCorner
from miniworlds.worlds.hex_world.hex_coords import CUBE_DIRECTIONS, cube_to_offset, offset_to_cube
from miniworlds.worlds.hex_world.hex_edge import HexEdge
from miniworlds.worlds.hex_world.hex_tile import HexTile
from miniworlds.worlds.hex_world.hex_world import HexWorld


class TestHexWorld(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_world_creates_all_tiles(self):
        self.assertEqual(len(self.world.tiles), 49)
        self.assertTrue(self.world.is_tile((0, 0)))
        self.assertTrue(self.world.is_tile((6, 6)))
        self.assertFalse(self.world.is_tile((7, 7)))

    def test_get_tile_returns_hex_tile(self):
        tile = self.world.get_tile((3, 3))
        self.assertIsInstance(tile, HexTile)
        self.assertEqual(tile.position, (3, 3))

    def test_center_tile_has_six_neighbours(self):
        tile = self.world.get_tile((3, 3))
        self.assertEqual(len(tile.get_neighbour_tiles()), 6)

    def test_border_tile_has_fewer_neighbours(self):
        tile = self.world.get_tile((0, 0))
        self.assertEqual(len(tile.get_neighbour_tiles()), 2)

    def test_corners_are_shared_between_hexes(self):
        corner_a = self.world.get_corner((3, 3), "n")
        corner_b = self.world.get_corner((4, 2), "sw")
        corner_c = self.world.get_corner((3, 2), "so")
        self.assertIs(corner_a, corner_b)
        self.assertIs(corner_a, corner_c)
        self.assertIsInstance(corner_a, HexCorner)

    def test_corner_reference_count_is_consistent(self):
        # Each of the 49 hexes references 6 corners: 49 * 6 references,
        # distributed over the merged corner objects.
        total = sum(len(corner.positions) for corner in self.world.corners.values())
        self.assertEqual(total, 49 * 6)

    def test_edges_are_shared_between_hexes(self):
        edge_a = self.world.get_edge((3, 3), "o")
        edge_b = self.world.get_edge((4, 3), "w")
        self.assertIs(edge_a, edge_b)
        self.assertIsInstance(edge_a, HexEdge)

    def test_edge_reference_count_is_consistent(self):
        total = sum(len(edge.positions) for edge in self.world.edges.values())
        self.assertEqual(total, 49 * 6)

    def test_tile_corner_and_edge_accessors(self):
        tile = self.world.get_tile((2, 2))
        self.assertIs(tile.get_corner("no"), self.world.get_corner((2, 2), "no"))
        self.assertIs(tile.get_edge("o"), self.world.get_edge((2, 2), "o"))

    def test_pixel_picking_returns_containing_hex(self):
        center = self.world.to_pixel((2, 2))
        tile = self.world.get_tile_from_pixel(center)
        self.assertEqual(tile.position, (2, 2))

    def test_pixel_picking_near_edge(self):
        center = self.world.to_pixel((2, 2))
        # A quarter hex width east of the center is still inside the hex.
        tile = self.world.get_tile_from_pixel((center[0] + 8, center[1]))
        self.assertEqual(tile.position, (2, 2))

    def test_get_from_pixel(self):
        center = self.world.to_pixel((4, 4))
        self.assertEqual(self.world.get_from_pixel(center), (4, 4))
        self.assertIsNone(self.world.get_from_pixel((-5, -5)))

    def test_pixel_picking_outside_world_returns_none(self):
        # Far outside the world.
        self.assertIsNone(self.world.get_tile_from_pixel((-100, -100)))
        self.assertIsNone(self.world.get_tile_from_pixel((2000, 2000)))
        # Inside the camera view, but rounding beyond the grid
        # (bottom-right corner of a 7x7 world).
        self.assertIsNone(self.world.get_tile_from_pixel((517, 438)))
        self.assertIsNone(self.world.get_from_pixel((517, 438)))

    def test_get_actors_from_pixel_outside_world(self):
        self.assertEqual(self.world.get_actors_from_pixel((-100, -100)), [])
        self.assertEqual(self.world.get_actors_from_pixel((517, 438)), [])

    def _neighbour(self, position, direction):
        cube = offset_to_cube(position)
        vector = CUBE_DIRECTIONS[direction]
        return cube_to_offset(
            (cube[0] + vector[0], cube[1] + vector[1], cube[2] + vector[2])
        )

    def test_diagonal_neighbours_depend_on_row_parity(self):
        # Odd rows are shifted half a hex to the right, so the diagonal
        # neighbors differ between odd and even rows (see HexWorld docs).
        self.assertEqual(self._neighbour((3, 1), "no"), (4, 0))
        self.assertEqual(self._neighbour((3, 1), "so"), (4, 2))
        self.assertEqual(self._neighbour((3, 1), "nw"), (3, 0))
        self.assertEqual(self._neighbour((3, 1), "sw"), (3, 2))
        self.assertEqual(self._neighbour((3, 2), "no"), (3, 1))
        self.assertEqual(self._neighbour((3, 2), "so"), (3, 3))
        self.assertEqual(self._neighbour((3, 2), "nw"), (2, 1))
        self.assertEqual(self._neighbour((3, 2), "sw"), (2, 3))

    def test_tiles_in_radius(self):
        tiles = self.world.get_tiles_in_radius((3, 3), 1)
        self.assertEqual(len(tiles), 7)
        tiles = self.world.get_tiles_in_radius((3, 3), 0)
        self.assertEqual(len(tiles), 1)

    def test_tiles_in_ring(self):
        tiles = self.world.get_tiles_in_ring((3, 3), 1)
        self.assertEqual(len(tiles), 6)
        tiles = self.world.get_tiles_in_ring((3, 3), 2)
        self.assertEqual(len(tiles), 12)

    def test_actor_can_be_placed_on_hex(self):
        actor = Actor((2, 2), world=self.world)
        self.assertEqual(actor.position, (2, 2))
        self.assertTrue(self.world.is_tile(actor.position))

    def test_actor_rect_uses_hex_bounding_box(self):
        actor = Actor((2, 2), world=self.world)
        tile = self.world.get_tile((2, 2))
        rect = actor.position_manager.get_global_rect()
        self.assertEqual(rect.topleft, tuple(int(v) for v in tile.to_pixel()))

    def test_actor_size_matches_hex_bounding_box(self):
        actor = Actor((2, 2), world=self.world)
        width, height = actor.position_manager.get_size()
        self.assertEqual(width, int(40 * 3 ** 0.5))
        self.assertEqual(height, 80)

    def test_camera_pixel_size_matches_hex_geometry(self):
        import math

        expected_width = math.sqrt(3) * 40 * 7.5
        expected_height = 40 * (1.5 * 7 + 0.5)
        self.assertEqual(self.world.camera.width, int(expected_width))
        self.assertEqual(self.world.camera.height, int(expected_height))

    def test_corner_pixel_lies_on_hex_boundary(self):
        corner = self.world.get_corner((3, 3), "n")
        center = self.world.to_pixel((3, 3))
        corner_pixel = corner.to_pixel()
        distance = (
            (corner_pixel[0] - center[0]) ** 2 + (corner_pixel[1] - center[1]) ** 2
        ) ** 0.5
        self.assertAlmostEqual(distance, 40)

    def test_actor_on_hex_world_gets_hex_costume(self):
        from miniworlds.worlds.hex_world.hex_costume import HexCostume

        actor = Actor((2, 2), world=self.world)
        self.assertIsInstance(actor.costume, HexCostume)

    def test_click_detection_on_tile_actor(self):
        actor = Actor((2, 2), world=self.world)
        center = self.world.to_pixel((2, 2))
        self.assertTrue(actor.detect_pixel(center))
        self.assertFalse(actor.detect_pixel(self.world.to_pixel((5, 5))))

    def test_colored_hex_costume_has_transparent_corners(self):
        actor = Actor((2, 2), world=self.world)
        actor.border = 1
        actor.fill_color = (0, 120, 0)
        image = actor.costume.get_image()
        width, height = image.get_size()
        self.assertEqual(image.get_at((width // 2, height // 2)), (0, 120, 0, 255))
        for position in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
            self.assertEqual(image.get_at(position).a, 0)

    def test_hex_costume_recoloring_keeps_corners_transparent(self):
        actor = Actor((2, 2), world=self.world)
        actor.fill_color = (0, 120, 0)
        actor.costume.get_image()
        actor.fill_color = (220, 180, 60)
        image = actor.costume.get_image()
        self.assertEqual(image.get_at((0, 0)).a, 0)
        self.assertEqual(image.get_at(image.get_rect().center), (220, 180, 60, 255))

    def test_unfilled_hex_costume_has_transparent_center(self):
        actor = Actor((2, 2), world=self.world)
        actor.border = 2
        actor.fill = False
        image = actor.costume.get_image()
        self.assertEqual(image.get_at(image.get_rect().center).a, 0)
        self.assertEqual(image.get_at((0, 0)).a, 0)

    def test_hex_image_costume_keeps_image_corners(self):
        import pygame

        actor = Actor((2, 2), world=self.world)
        surface = pygame.Surface((20, 20), pygame.SRCALPHA)
        surface.fill((10, 20, 30, 255))
        actor.add_costume(surface)
        image = actor.costume.get_image()
        self.assertEqual(image.get_at((0, 0)), (10, 20, 30, 255))

    def test_click_detection_on_corner_actor(self):
        corner = self.world.get_corner((3, 3), "n")
        actor = Actor(corner.position, world=self.world)
        corner_pixel = corner.to_pixel()
        self.assertTrue(actor.detect_pixel(corner_pixel))
        # Within the detection radius around the corner.
        self.assertTrue(actor.detect_pixel((corner_pixel[0] + 5, corner_pixel[1])))
        # A distant pixel does not hit the corner actor.
        self.assertFalse(actor.detect_pixel(self.world.to_pixel((0, 0))))

    def test_click_detection_on_edge_actor(self):
        edge = self.world.get_edge((3, 3), "o")
        actor = Actor(edge.position, world=self.world)
        self.assertTrue(actor.detect_pixel(edge.to_pixel()))
        self.assertFalse(actor.detect_pixel(self.world.to_pixel((0, 0))))

    def test_corner_actor_can_be_placed_and_found(self):
        corner = self.world.get_corner((2, 2), "no")
        actor = Actor(corner.position, world=self.world)
        self.assertTrue(self.world.is_corner(actor.position))
        self.assertEqual(actor.position, corner.position)

    def test_get_corner_from_pixel_finds_nearest_corner(self):
        corner = self.world.get_corner((3, 3), "n")
        found = self.world.get_corner_from_pixel(corner.to_pixel())
        self.assertIs(found, corner)
        # A pixel slightly below the corner still resolves to it.
        found = self.world.get_corner_from_pixel(
            (corner.to_pixel()[0] + 3, corner.to_pixel()[1] + 3)
        )
        self.assertIs(found, corner)

    def test_get_edge_from_pixel_finds_nearest_edge(self):
        edge = self.world.get_edge((3, 3), "o")
        found = self.world.get_edge_from_pixel(edge.to_pixel())
        self.assertIs(found, edge)

    def test_get_actors_from_pixel_uses_hex_picking(self):
        actor = Actor((2, 2), world=self.world)
        center = self.world.to_pixel((2, 2))
        self.assertIn(actor, self.world.get_actors_from_pixel(center))
        self.assertEqual(
            self.world.get_actors_from_pixel(self.world.to_pixel((5, 5))), []
        )

    def test_get_distance_to_uses_hex_distance(self):
        actor = Actor((0, 0), world=self.world)
        self.assertEqual(actor.get_distance_to((1, 0)), 1.0)
        # (0, 0) -> (1, 1) is two hexes apart, not sqrt(2).
        self.assertEqual(actor.get_distance_to((1, 1)), 2.0)

    def test_get_distance_to_actor_uses_hex_distance(self):
        first = Actor((0, 0), world=self.world)
        second = Actor((2, 0), world=self.world)
        self.assertEqual(first.get_distance_to(second), 2.0)

    def test_get_distance_to_corner_actor(self):
        corner = self.world.get_corner((3, 3), "n")
        actor = Actor(corner.position, world=self.world)
        south = self.world.get_corner((3, 3), "s")
        self.assertAlmostEqual(actor.get_distance_to(south.position), 80.0)
        self.assertAlmostEqual(actor.get_distance_to((3, 3)), 40.0)

    def test_get_distance_to_edge_actor(self):
        edge = self.world.get_edge((3, 3), "o")
        actor = Actor(edge.position, world=self.world)
        self.assertAlmostEqual(actor.get_distance_to((3, 3)), 20.0 * 3 ** 0.5)

    def test_picking_outside_world_returns_none(self):
        self.assertIsNone(self.world.get_corner_from_pixel((900, 900)))
        self.assertIsNone(self.world.get_edge_from_pixel((900, 900)))
        self.assertIsNone(self.world.get_corner_from_pixel((-10, -10)))
        self.assertIsNone(self.world.get_edge_from_pixel((-10, -10)))

    def test_corner_neighbour_tiles(self):
        corner = self.world.get_corner((3, 3), "n")
        tiles = corner.get_neighbour_tiles()
        self.assertEqual(
            sorted(tile.position for tile in tiles), [(3, 2), (3, 3), (4, 2)]
        )

    def test_border_corner_neighbour_tiles(self):
        corner = self.world.get_corner((0, 0), "n")
        tiles = corner.get_neighbour_tiles()
        self.assertEqual([tile.position for tile in tiles], [(0, 0)])

    def test_edge_neighbour_tiles(self):
        edge = self.world.get_edge((3, 3), "o")
        tiles = edge.get_neighbour_tiles()
        self.assertEqual(sorted(tile.position for tile in tiles), [(3, 3), (4, 3)])

    def test_border_edge_neighbour_tiles(self):
        edge = self.world.get_edge((0, 0), "w")
        tiles = edge.get_neighbour_tiles()
        self.assertEqual([tile.position for tile in tiles], [(0, 0)])

    def test_get_corner_and_edge_raise_correct_error_types(self):
        from miniworlds.base.exceptions import (
            CornerNotFoundError,
            EdgeNotFoundError,
        )

        with self.assertRaises(CornerNotFoundError):
            self.world.get_corner((20, 20), "n")
        with self.assertRaises(CornerNotFoundError):
            self.world.get_corner((20, 20))
        with self.assertRaises(EdgeNotFoundError):
            self.world.get_edge((20, 20), "o")
        with self.assertRaises(EdgeNotFoundError):
            self.world.get_edge((20, 20))

    def test_invalid_direction_raises_helpful_error(self):
        from miniworlds.base.exceptions import DirectionNotFoundError

        with self.assertRaises(DirectionNotFoundError) as context:
            self.world.get_corner((3, 3), "nord")
        self.assertIn("not a valid direction", str(context.exception))
        self.assertIn("Did you mean", str(context.exception))
        with self.assertRaises(DirectionNotFoundError):
            self.world.get_edge((3, 3), "ost")
        with self.assertRaises(DirectionNotFoundError):
            self.world.get_tile((3, 3)).get_corner("nord")

    def test_ring_tiles_have_exact_distance(self):
        from miniworlds.worlds.hex_world import hex_coords

        center = hex_coords.offset_to_cube((3, 3))
        for tile in self.world.get_tiles_in_ring((3, 3), 2):
            distance = hex_coords.cube_distance(
                center, hex_coords.offset_to_cube(tile.position)
            )
            self.assertEqual(distance, 2)

    def test_ring_at_world_border_is_clipped(self):
        tiles = self.world.get_tiles_in_ring((0, 0), 1)
        self.assertEqual(sorted(tile.position for tile in tiles), [(0, 1), (1, 0)])

    def test_negative_radius_returns_empty_list(self):
        self.assertEqual(self.world.get_tiles_in_radius((3, 3), -1), [])
        self.assertEqual(self.world.get_tiles_in_ring((3, 3), -1), [])

    def test_radius_is_ordered_from_center_outwards(self):
        tiles = self.world.get_tiles_in_radius((3, 3), 1)
        self.assertEqual(tiles[0].position, (3, 3))
        self.assertEqual(len(tiles), 7)

    def test_move_in_direction_with_hex_direction_names(self):
        expected = {
            "o": (4, 3),
            "so": (4, 4),
            "sw": (3, 4),
            "w": (2, 3),
            "nw": (3, 2),
            "no": (4, 2),
        }
        for direction, destination in expected.items():
            actor = Actor((3, 3), world=self.world)
            actor.move_in_direction(direction)
            self.assertEqual(actor.position, destination, direction)

    def test_hex_direction_name_sets_direction_degrees(self):
        actor = Actor((3, 3), world=self.world)
        actor.direction = "no"
        self.assertEqual(actor.direction, 30)
        actor.move_in_direction("nw")
        # get_direction normalizes 330 degrees to -30
        self.assertEqual(actor.direction, -30)
        self.assertEqual(actor.position, (3, 2))

    def test_move_along_hex_axis_degrees(self):
        actor = Actor((3, 3), world=self.world)
        actor.direction = 30
        actor.move(1)
        self.assertEqual(actor.position, (4, 2))

    def test_move_in_direction_with_hex_distance(self):
        actor = Actor((3, 3), world=self.world)
        actor.move_in_direction("no", 2)
        self.assertEqual(actor.position, (4, 1))

    def test_square_directions_still_work(self):
        actor = Actor((3, 3), world=self.world)
        actor.move_in_direction("right")
        self.assertEqual(actor.position, (4, 3))
        actor.move_in_direction("down")
        self.assertEqual(actor.position, (4, 4))

    def test_edge_from_pixel_cache_invalidated_on_tile_changes(self):
        from miniworlds.worlds.hex_world.hex_edge import HexEdge

        world = HexWorld(4, 4, tile_size=40, empty=True)
        world.add_tile_to_world((2, 2))
        edge = world.add_edge_to_world((2, 2), "o")
        self.assertEqual(HexEdge.from_pixel(edge.to_pixel(), world).position, edge.position)
        world.clear_tiles()
        world.add_tile_to_world((1, 1))
        new_edge = world.add_edge_to_world((1, 1), "o")
        self.assertEqual(
            HexEdge.from_pixel(new_edge.to_pixel(), world).position, new_edge.position
        )

    def test_camera_view_setters_work_on_hex_world(self):
        import math

        world = HexWorld(10, 10, tile_size=40)
        world.camera.width = 5
        world.camera.height = 5
        self.assertEqual(world.camera.view, (5, 5))
        world.camera.topleft = (2, 2)
        self.assertEqual(world.camera._topleft, (2, 2))
        world.camera.x = 1
        world.camera.y = 3
        self.assertEqual(world.camera._topleft, (1, 3))
        # the getter still reports the pixel position
        self.assertEqual(
            world.camera.topleft,
            (int(1 * math.sqrt(3) * 40), int(3 * 1.5 * 40)),
        )

    def test_camera_from_actor_centers_on_actor(self):
        world = HexWorld(10, 10, tile_size=40)
        world.camera.width = 5
        world.camera.height = 5
        actor = Actor((5, 5), world=world)
        actor.center = (5, 5)
        world.camera.from_actor(actor)
        self.assertEqual(world.camera._topleft, (3, 3))

    def test_columns_and_rows_setters_work_on_hex_world(self):
        world = HexWorld(10, 10, tile_size=40)
        world.columns = 8
        world.rows = 6
        self.assertEqual(world.columns, 8)
        self.assertEqual(world.rows, 6)
        self.assertEqual(world.camera.view, (8, 6))

    def test_set_tile_size_invalidates_edge_pixel_cache(self):
        world = HexWorld(6, 6, tile_size=40)
        edge = world.get_edge((3, 3), "o")
        # warm the from_pixel cache with the old tile size
        self.assertIs(HexEdge.from_pixel(edge.to_pixel(), world), edge)
        world.set_tile_size(80)
        self.assertIs(HexEdge.from_pixel(edge.to_pixel(), world), edge)

    def test_neighbour_cache_invalidated_when_tile_added(self):
        world = HexWorld(4, 4, tile_size=40, empty=True)
        world.add_tile_to_world((1, 1))
        tile = world.get_tile((1, 1))
        self.assertEqual(tile.get_neighbour_tiles(), [])
        world.add_tile_to_world((2, 1))
        self.assertEqual([t.position for t in tile.get_neighbour_tiles()], [(2, 1)])
        world.clear_tiles()
        world.add_tile_to_world((1, 1))
        self.assertEqual(world.get_tile((1, 1)).get_neighbour_tiles(), [])

    def test_corner_neighbour_cache_invalidated_on_merge(self):
        world = HexWorld(4, 4, tile_size=40, empty=True)
        world.add_tile_to_world((1, 1))
        world.add_tile_to_world((2, 0))
        world.add_corner_to_world((1, 1), "no")
        corner = world.get_corner((1, 1), "no")
        self.assertEqual([t.position for t in corner.get_neighbour_tiles()], [(1, 1)])
        # the "s" corner of (2, 0) is the same physical corner
        world.add_corner_to_world((2, 0), "s")
        self.assertEqual(
            sorted(t.position for t in corner.get_neighbour_tiles()), [(1, 1), (2, 0)]
        )

    def test_get_tile_from_pixel_returns_registered_tile(self):
        center = self.world.to_pixel((3, 3))
        self.assertIs(self.world.get_tile_from_pixel(center), self.world.get_tile((3, 3)))

    def test_get_actors_from_pixel_includes_corner_and_edge_actors(self):
        corner = self.world.get_corner((3, 3), "n")
        edge = self.world.get_edge((3, 3), "o")
        tile_actor = Actor((3, 3), world=self.world)
        corner_actor = Actor(corner.position, world=self.world)
        edge_actor = Actor(edge.position, world=self.world)
        self.assertIn(corner_actor, self.world.get_actors_from_pixel(corner.to_pixel()))
        self.assertIn(edge_actor, self.world.get_actors_from_pixel(edge.to_pixel()))
        found = self.world.get_actors_from_pixel(self.world.to_pixel((3, 3)))
        self.assertIn(tile_actor, found)
        # corner and edge centers are one tile_size away from the hex
        # center, beyond the detection radius of tile_size / 3
        self.assertNotIn(corner_actor, found)
        self.assertNotIn(edge_actor, found)
        self.assertEqual(self.world.get_actors_from_pixel((-100, -100)), [])

    def test_get_from_pixel_respects_camera_view(self):
        world = HexWorld(10, 10, tile_size=40)
        world.camera.width = 5
        world.camera.height = 5
        self.assertIsNone(world.get_from_pixel((1000, 10)))
        self.assertIsNone(world.get_from_pixel((-1, 5)))
        self.assertEqual(world.get_from_pixel(world.to_pixel((0, 0))), (0, 0))

    def test_move_snaps_any_degree_to_a_hex_axis(self):
        from miniworlds.worlds.hex_world import hex_coords
        from miniworlds.worlds.hex_world.hex_world_sensor_manager import (
            HexWorldSensorManager,
        )

        start = (3, 2)
        start_cube = hex_coords.offset_to_cube(start)
        for degrees in range(360):
            destination = HexWorldSensorManager.get_destination(start, degrees, 1)
            distance = hex_coords.cube_distance(
                start_cube, hex_coords.offset_to_cube(destination)
            )
            self.assertEqual(distance, 1, degrees)
        actor = Actor((3, 3), world=self.world)
        actor.move_in_direction(45)
        self.assertEqual(actor.position, (4, 2))

    def test_invalid_direction_error_mentions_hex_directions(self):
        actor = Actor((3, 3), world=self.world)
        with self.assertRaises(TypeError) as context:
            actor.direction = "xyzzy"
        self.assertIn("'no'", str(context.exception))
        self.assertIn("HexWorld", str(context.exception))
        with self.assertRaises(TypeError):
            actor.move_in_direction("xyzzy")

    def test_console_and_toolbar_widgets_on_hex_world_do_not_crash(self):
        from miniworlds.actors.widgets.button import Button
        from miniworlds.worlds.gui.console import Console
        from miniworlds.worlds.gui.toolbar import Toolbar
        from miniworlds.worlds.hex_world.hex_costume import HexCostume

        console = Console()
        self.world.camera.add_bottom(console)
        line = console.newline("hello")

        toolbar = Toolbar()
        self.world.camera.add_right(toolbar)
        toolbar.add(Button("Restart"))

        # The widgets were created while the hex world was the running world,
        # so they keep a HexCostume after being re-parented to the GUI worlds.
        # Drawing must fall back to the rectangular shape instead of calling
        # is_tile() on the console or toolbar world.
        self.assertIsInstance(line.costume, HexCostume)
        self.assertFalse(line.costume._is_on_tile())

        self.world.app._unittest = True

        @self.world.register
        def act(world):
            if world.frame >= 3:
                world.quit()

        self.world.run()


class TestHexPixelPicking(unittest.TestCase):
    """Pixel picking translates screen pixels into world pixels.

    Mouse events deliver window coordinates: the camera view is scrolled
    by `camera.topleft` and docked worlds are drawn at
    `camera.screen_topleft`, while hexes, corners, and edges are laid
    out in world pixels. All picking queries and corner/edge actor
    detection must therefore translate the pixel first.
    """

    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def _scrolled_world(self):
        world = HexWorld(20, 16, tile_size=40)
        world.camera._strict = False
        world.camera.width = 8   # view size in hexes
        world.camera.height = 6
        world.camera.topleft = (5, 4)  # scroll position in hexes
        return world

    def _screen_pixel(self, world, world_pixel):
        """Window pixel at which the given world pixel is drawn."""
        topleft = world.camera.topleft
        return (world_pixel[0] - topleft[0], world_pixel[1] - topleft[1])

    def test_tile_picking_with_scrolled_camera(self):
        world = self._scrolled_world()
        tile = world.get_tile((7, 5))
        screen_pixel = self._screen_pixel(world, world.to_pixel((7, 5)))
        self.assertIs(world.get_tile_from_pixel(screen_pixel), tile)
        self.assertEqual(world.get_from_pixel(screen_pixel), (7, 5))

    def test_edge_picking_with_scrolled_camera(self):
        world = self._scrolled_world()
        edge = world.get_edge((7, 5), "o")
        screen_pixel = self._screen_pixel(world, edge.to_pixel())
        found = world.get_edge_from_pixel(screen_pixel)
        self.assertIs(found, edge)
        found_edge_pixel = found.to_pixel()
        self.assertAlmostEqual(found_edge_pixel[0], edge.to_pixel()[0], places=2)
        self.assertAlmostEqual(found_edge_pixel[1], edge.to_pixel()[1], places=2)

    def test_corner_picking_with_scrolled_camera(self):
        world = self._scrolled_world()
        corner = world.get_corner((7, 5), "n")
        screen_pixel = self._screen_pixel(world, corner.to_pixel())
        self.assertIs(world.get_corner_from_pixel(screen_pixel), corner)

    def test_picking_outside_camera_view_returns_none(self):
        world = self._scrolled_world()
        # World pixel below the visible view, but inside the world:
        # the screen pixel would map back into the world, yet it lies
        # outside the camera view and is not clickable.
        outside_pixel = world.to_pixel((17, 14))
        screen_pixel = self._screen_pixel(world, outside_pixel)
        # The pixel is scrolled out of the view; window coordinates for
        # it cannot exist, but a raw call must still not pick anything.
        self.assertIsNone(world.get_corner_from_pixel(screen_pixel))
        self.assertIsNone(world.get_edge_from_pixel(screen_pixel))

    def test_edge_picking_in_docked_window(self):
        world = HexWorld(7, 7, tile_size=40)
        world.camera.screen_topleft = (120, 40)
        edge = world.get_edge((3, 4), "no")
        screen_pixel = (
            edge.to_pixel()[0] + 120,
            edge.to_pixel()[1] + 40,
        )
        self.assertIs(world.get_edge_from_pixel(screen_pixel), edge)

    def test_rim_edge_click_returns_nearest_edge(self):
        world = HexWorld(7, 7, tile_size=40)
        edge = world.get_edge((3, 0), "no")
        # A pixel directly above the top rim edges rounds to a position
        # outside the world, although the edge is visibly under it.
        screen_pixel = (edge.to_pixel()[0], 2)
        self.assertIs(world.get_edge_from_pixel(screen_pixel), edge)

    def test_rim_corner_click_returns_nearest_corner(self):
        world = HexWorld(7, 7, tile_size=40)
        corner = world.get_corner((2, 0), "n")
        # The top tip corner of hex (2, 0) lies at the world border.
        screen_pixel = (corner.to_pixel()[0], 3)
        self.assertIs(world.get_corner_from_pixel(screen_pixel), corner)

    def test_picking_far_outside_world_returns_none(self):
        world = HexWorld(7, 7, tile_size=40)
        self.assertIsNone(world.get_edge_from_pixel((900, 900)))
        self.assertIsNone(world.get_corner_from_pixel((900, 900)))
        self.assertIsNone(world.get_edge_from_pixel((-10, -10)))
        self.assertIsNone(world.get_corner_from_pixel((-10, -10)))

    def test_edge_actor_detect_pixel_with_scrolled_camera(self):
        world = self._scrolled_world()
        edge = world.get_edge((7, 5), "o")
        road = Actor(edge.position, world=world)
        screen_pixel = self._screen_pixel(world, edge.to_pixel())
        self.assertTrue(road.detect_pixel(screen_pixel))
        other_pixel = self._screen_pixel(world, world.to_pixel((10, 9)))
        self.assertFalse(road.detect_pixel(other_pixel))

    def test_tile_actor_detect_pixel_with_scrolled_camera(self):
        world = self._scrolled_world()
        actor = Actor((7, 5), world=world)
        screen_pixel = self._screen_pixel(world, world.to_pixel((7, 5)))
        self.assertTrue(actor.detect_pixel(screen_pixel))
        other_pixel = self._screen_pixel(world, world.to_pixel((10, 9)))
        self.assertFalse(actor.detect_pixel(other_pixel))

    def test_get_actors_from_pixel_with_scrolled_camera(self):
        world = self._scrolled_world()
        corner = world.get_corner((7, 5), "n")
        settlement = Actor(corner.position, world=world)
        screen_pixel = self._screen_pixel(world, corner.to_pixel())
        self.assertIn(settlement, world.get_actors_from_pixel(screen_pixel))

    def test_mouse_event_picks_clicked_edge_with_scrolled_camera(self):
        world = self._scrolled_world()
        edge = world.get_edge((7, 5), "o")
        screen_pixel = self._screen_pixel(world, edge.to_pixel())
        clicked = {}

        @world.register
        def on_mouse_left(self, mouse_pos):
            clicked["edge"] = world.get_edge_from_pixel(mouse_pos)

        world.event_manager.handler.handle_event("mouse_left", screen_pixel)
        self.assertIs(clicked.get("edge"), edge)

    def test_picking_returns_true_nearest_edge(self):
        world = HexWorld(7, 7, tile_size=40)
        edge_centers = [
            (edge, edge.to_pixel()) for edge in world.edges.values()
        ]
        for screen_pixel in [
            world.to_pixel((0, 0)),
            world.to_pixel((6, 6)),
            world.get_edge((0, 0), "w").to_pixel(),
            (world.get_edge((3, 0), "no").to_pixel()[0], 2),
        ] + [
            (x, y)
            for y in range(0, 460, 53)
            for x in range(0, 520, 67)
        ]:
            found = world.get_edge_from_pixel(screen_pixel)
            self.assertIsNotNone(found, screen_pixel)
            best_distance = min(
                (center[0] - screen_pixel[0]) ** 2 + (center[1] - screen_pixel[1]) ** 2
                for _edge, center in edge_centers
            )
            found_distance = (
                (found.to_pixel()[0] - screen_pixel[0]) ** 2
                + (found.to_pixel()[1] - screen_pixel[1]) ** 2
            )
            self.assertLessEqual(found_distance, best_distance, screen_pixel)


if __name__ == "__main__":
    unittest.main()
