"""Robustness tests for HexWorld: invalid input must fail with clear errors.

These tests pin the behavior that previously produced silent wrong results
(corner/edge keys truncated to tile positions), obscure low-level errors
(ZeroDivisionError, "not iterable"), or unbounded caches.
"""

from __future__ import annotations

import gc
import math
import unittest

from miniworlds import Actor, App
from miniworlds.base.exceptions import (
    CornerNotFoundError,
    EdgeNotFoundError,
    TiledWorldTooBigError,
    WorldArgumentsError,
)
from miniworlds.worlds.hex_world import hex_coords
from miniworlds.worlds.hex_world.hex_edge import HexEdge
from miniworlds.worlds.hex_world.hex_world import HexWorld
from miniworlds.worlds.tiled_world.tile_elements import TileBase


class TestToOffsetValidation(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_accepts_tuple_list_actor_and_integral_float(self):
        self.assertEqual(hex_coords.to_offset((1, 2)), (1, 2))
        self.assertEqual(hex_coords.to_offset([1, 2]), (1, 2))
        self.assertEqual(hex_coords.to_offset((3.0, 2.0)), (3, 2))

        class Thing:
            position = (4, 5)

        self.assertEqual(hex_coords.to_offset(Thing()), (4, 5))

    def test_corner_edge_key_raises_with_hint(self):
        with self.assertRaises(TypeError) as ctx:
            hex_coords.to_offset((7, 7, -14))
        self.assertIn("3-tuple", str(ctx.exception))

    def test_garbage_raises_type_error(self):
        for bad in ("abc", None, 5, (1,), (1, 2, 3, 4), (1.5, 2), (True, 2), ("1", "2")):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                hex_coords.to_offset(bad)


class TestPositionQueriesRejectCornerKeys(unittest.TestCase):
    """Corner/edge keys must not be silently truncated to tile positions."""

    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)
        self.corner_key = self.world.get_corner((3, 3), "n").position

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_get_distance_with_corner_key_raises(self):
        with self.assertRaises(TypeError):
            self.world.get_distance(self.corner_key, (3, 3))

    def test_get_distance_with_corner_actor_raises(self):
        actor = Actor(self.corner_key)
        with self.assertRaises(TypeError):
            self.world.get_distance(actor, (3, 3))

    def test_radius_and_ring_with_corner_key_raise(self):
        with self.assertRaises(TypeError):
            self.world.get_tiles_in_radius(self.corner_key, 1)
        with self.assertRaises(TypeError):
            self.world.get_tiles_in_ring(self.corner_key, 1)

    def test_line_and_path_with_corner_key_raise(self):
        with self.assertRaises(TypeError):
            self.world.get_tiles_in_line((0, 0), self.corner_key)
        with self.assertRaises(TypeError):
            self.world.find_path(self.corner_key, (5, 5))
        with self.assertRaises(TypeError):
            self.world.find_path((0, 0, 0), (5, 5))

    def test_valid_queries_still_work(self):
        self.assertEqual(self.world.get_distance((0, 0), (3, 0)), 3)
        self.assertEqual(len(self.world.get_tiles_in_radius((3, 3), 1)), 7)
        path = self.world.find_path((0, 0), (2, 2))
        self.assertEqual(path[0].position, (0, 0))
        self.assertEqual(path[-1].position, (2, 2))
        self.assertEqual(len(path), self.world.get_distance((0, 0), (2, 2)) + 1)


class TestToPixel(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_tile_position_maps_to_center(self):
        tile = self.world.get_tile((2, 3))
        self.assertEqual(self.world.to_pixel((2, 3)), tile.to_center())

    def test_corner_key_maps_to_corner_pixel(self):
        corner = self.world.get_corner((3, 3), "n")
        self.assertEqual(self.world.to_pixel(corner.position), corner.to_pixel())

    def test_edge_key_maps_to_edge_pixel(self):
        edge = self.world.get_edge((3, 3), "o")
        self.assertEqual(self.world.to_pixel(edge.position), edge.to_pixel())

    def test_actor_on_corner_to_pixel(self):
        corner = self.world.get_corner((3, 3), "n")
        actor = Actor(corner.position)
        self.assertEqual(self.world.to_pixel(actor.position), corner.to_pixel())

    def test_unknown_three_tuple_raises(self):
        with self.assertRaises(TypeError):
            self.world.to_pixel((1, 2, 3))

    def test_garbage_raises_type_error(self):
        for bad in ("foo", 5, None, (1,), (1, 2, 3, 4), ("a", 2)):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                self.world.to_pixel(bad)


class TestPixelQueryValidation(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_pixel_queries_reject_garbage(self):
        for bad in (5, "x", None, (1,), (1, 2, 3), ("a", 2)):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    self.world.get_tile_from_pixel(bad)
                with self.assertRaises(TypeError):
                    self.world.get_from_pixel(bad)
                with self.assertRaises(TypeError):
                    self.world.get_corner_from_pixel(bad)
                with self.assertRaises(TypeError):
                    self.world.get_edge_from_pixel(bad)
                with self.assertRaises(TypeError):
                    self.world.get_actors_from_pixel(bad)

    def test_valid_pixels_still_work(self):
        tile = self.world.get_tile((3, 3))
        self.assertIs(self.world.get_tile_from_pixel(tile.to_center()), tile)
        self.assertEqual(self.world.get_from_pixel(tile.to_center()), (3, 3))
        corner = self.world.get_corner((3, 3), "n")
        self.assertIs(self.world.get_corner_from_pixel(corner.to_pixel()), corner)

    def test_xy_objects_like_vector2_are_accepted(self):
        import pygame

        tile = self.world.get_tile((3, 3))
        center = pygame.Vector2(tile.to_center())
        self.assertIs(self.world.get_tile_from_pixel(center), tile)
        self.assertEqual(self.world.to_pixel(pygame.Vector2(2, 3)), self.world.to_pixel((2, 3)))


class TestConstructorAndSetterValidation(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_non_int_dimensions_raise_world_arguments_error(self):
        for x, y in ((10.5, 5), ("7", 5), (True, 5), ((7, 5), 5)):
            with self.subTest(x=x, y=y), self.assertRaises(WorldArgumentsError):
                HexWorld(x, y)

    def test_non_positive_dimensions_raise_value_error(self):
        with self.assertRaises(ValueError):
            HexWorld(0, 5)
        with self.assertRaises(ValueError):
            HexWorld(-3, 5)

    def test_too_big_world_error_uses_actual_tile_size(self):
        with self.assertRaises(TiledWorldTooBigError) as ctx:
            HexWorld(2000, 2000, tile_size=50)
        # 2000 / 50 = 40; with the old hardcoded 40 the hint would say (50, 50)
        self.assertIn("(40, 40)", str(ctx.exception))

    def test_invalid_tile_size_raises_at_construction(self):
        for bad in (0, -40, "40", None, True):
            with self.subTest(bad=bad):
                with self.assertRaises((TypeError, ValueError)):
                    HexWorld(5, 5, tile_size=bad)

    def test_set_tile_size_rejects_invalid_values(self):
        world = HexWorld(5, 5, tile_size=40)
        for bad in (0, -40, "40"):
            with self.subTest(bad=bad):
                with self.assertRaises((TypeError, ValueError)):
                    world.tile_size = bad
                with self.assertRaises((TypeError, ValueError)):
                    world.set_tile_size(bad)
        self.assertEqual(world.tile_size, 40)

    def test_set_tile_size_keeps_picking_working(self):
        world = HexWorld(5, 5, tile_size=40)
        world.set_tile_size(80)
        tile = world.get_tile((2, 2))
        self.assertIs(world.get_tile_from_pixel(tile.to_center()), tile)

    def test_columns_rows_setters_validate(self):
        world = HexWorld(7, 7, tile_size=40)
        with self.assertRaises(TypeError):
            world.columns = 2.5
        with self.assertRaises(ValueError):
            world.columns = 0
        with self.assertRaises(ValueError):
            world.rows = -1
        world.columns = 8
        world.rows = 9
        self.assertEqual(world.world_size_x, 8)
        self.assertEqual(world.world_size_y, 9)


class TestHexCoordsGuards(unittest.TestCase):
    def test_nearest_axis_degrees_rejects_non_finite(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                hex_coords.nearest_axis_degrees(bad)

    def test_nearest_axis_degrees_still_snaps(self):
        self.assertEqual(hex_coords.nearest_axis_degrees(45), 30)
        self.assertEqual(hex_coords.nearest_axis_degrees(-720), hex_coords.nearest_axis_degrees(0))
        for degrees in range(360):
            snapped = hex_coords.nearest_axis_degrees(degrees)
            self.assertIn(snapped, (30, 90, 150, 210, 270, 330))

    def test_pixel_to_cube_rejects_non_positive_tile_size(self):
        with self.assertRaises(ValueError):
            hex_coords.pixel_to_cube((10, 10), 0)
        with self.assertRaises(ValueError):
            hex_coords.pixel_to_cube((10, 10), -40)

    def test_geometry_cache_is_bounded(self):
        for tile_size in range(1, 500):
            hex_coords.corner_pixel_offsets(tile_size)
            hex_coords.edge_pixel_offsets(tile_size)
        self.assertLessEqual(len(hex_coords._CORNER_OFFSETS_CACHE), 128)
        self.assertLessEqual(len(hex_coords._EDGE_OFFSETS_CACHE), 128)
        # Still correct after the cache was cleared internally.
        offsets = hex_coords.corner_pixel_offsets(40)
        self.assertEqual(offsets["n"], (0.0, -40))
        self.assertAlmostEqual(offsets["no"][0], hex_coords.hex_width(40) / 2.0)


class TestPathfindingValidation(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_cost_callback_returning_non_number_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.world.find_path((0, 0), (5, 5), cost=lambda tile: None)

    def test_negative_cost_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.world.find_path((0, 0), (5, 5), cost=lambda tile: -1)

    def test_get_path_cost_rejects_garbage(self):
        with self.assertRaises(TypeError):
            self.world.get_path_cost(None)
        with self.assertRaises(TypeError):
            self.world.get_path_cost([(1, 2)])
        with self.assertRaises(TypeError):
            self.world.get_path_cost("path")

    def test_get_path_cost_sums_all_but_first(self):
        self.world.get_tile((1, 0)).cost = 3
        path = self.world.find_path((0, 0), (2, 0))
        expected = sum(tile.cost for tile in path[1:])
        self.assertEqual(self.world.get_path_cost(path), expected)
        self.assertEqual(
            self.world.get_path_cost(path, cost=lambda tile: 2), 2 * (len(path) - 1)
        )


class TestHighlightRobustness(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_single_tile_and_single_position_are_accepted(self):
        tile = self.world.get_tile((2, 2))
        self.world.highlight_tiles(tile)
        self.assertTrue(tile.is_highlighted)
        self.world.highlight_tiles((4, 4))
        self.assertTrue(self.world.get_tile((4, 4)).is_highlighted)
        self.world.clear_highlights(tile)
        self.assertFalse(tile.is_highlighted)
        self.world.clear_highlights((4, 4))
        self.assertFalse(self.world.get_tile((4, 4)).is_highlighted)

    def test_invalid_colors_raise_clear_errors(self):
        tile = self.world.get_tile((2, 2))
        with self.assertRaises(ValueError):
            self.world.highlight_tiles([tile], (1, 2))
        with self.assertRaises(TypeError):
            self.world.highlight_tiles([tile], 5)
        with self.assertRaises(ValueError):
            self.world.highlight_tiles([tile], (300, -5, 0))
        with self.assertRaises(TypeError):
            self.world.highlight_tiles([tile], ("a", 1, 2))

    def test_invalid_tile_entries_raise_type_error(self):
        with self.assertRaises(TypeError):
            self.world.highlight_tiles(["foo"])
        with self.assertRaises(TypeError):
            self.world.clear_highlights([None])

    def test_valid_colors_still_work(self):
        tile = self.world.get_tile((2, 2))
        self.world.highlight_tiles([tile], (255, 0, 0))
        self.assertEqual(self.world._tile_highlights[(2, 2)], (255, 0, 0, 90))
        self.world.highlight_tiles([tile], (0, 255, 0, 128))
        self.assertEqual(self.world._tile_highlights[(2, 2)], (0, 255, 0, 128))


class TestAddTileValidation(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(5, 5, tile_size=40, empty=True)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_garbage_positions_raise_type_error(self):
        for bad in ("foo", None, (1, 2, 3), (1.5, 2), (1,)):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                self.world.add_tile_to_world(bad)

    def test_valid_position_works(self):
        tile = self.world.add_tile_to_world((2, 1))
        self.assertTrue(self.world.is_tile((2, 1)))
        self.assertIs(self.world.get_tile((2, 1)), tile)


class TestCornerEdgeHints(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_tile_position_without_direction_gets_hint(self):
        with self.assertRaises(CornerNotFoundError) as ctx:
            self.world.get_corner((3, 3))
        self.assertIn("direction", str(ctx.exception))
        with self.assertRaises(EdgeNotFoundError) as ctx:
            self.world.get_edge((3, 3))
        self.assertIn("direction", str(ctx.exception))


class TestPositionPixelCacheLifetime(unittest.TestCase):
    """The pixel cache must die with its world (no leak, no id() reuse)."""

    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_cache_entry_is_dropped_when_world_is_collected(self):
        import weakref

        world = HexWorld(4, 4, tile_size=40)
        HexEdge.from_pixel((10, 10), world)
        self.assertIn(world, TileBase._position_pixel_cache)
        ref = weakref.ref(world)
        App.reset(unittest=True, file=__file__)  # drop the app's reference
        del world
        gc.collect()
        self.assertIsNone(ref())
        self.assertEqual(len(TileBase._position_pixel_cache), 0)

    def test_new_world_gets_fresh_cache(self):
        world_a = HexWorld(4, 4, tile_size=40)
        HexEdge.from_pixel((10, 10), world_a)
        del world_a
        gc.collect()
        App.reset(unittest=True, file=__file__)
        world_b = HexWorld(4, 4, tile_size=80)
        self.addCleanup(App.reset, unittest=True)
        edge = HexEdge.from_pixel((10, 10), world_b)
        # The cache of world_b holds tile_size-80 pixels, not stale 40s.
        cached = TileBase._position_pixel_cache[world_b]
        self.assertEqual(set(cached), set(world_b.get_edge_points()))
        for position, pixel in world_b.get_edge_points().items():
            self.assertEqual(cached[position], pixel)
        self.assertIsInstance(edge, HexEdge)


class TestEmptyWorldQueries(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(5, 5, tile_size=40, empty=True)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_picking_returns_none_or_empty(self):
        self.assertIsNone(self.world.get_tile_from_pixel((100, 100)))
        self.assertIsNone(self.world.get_from_pixel((100, 100)))
        self.assertIsNone(self.world.get_corner_from_pixel((100, 100)))
        self.assertIsNone(self.world.get_edge_from_pixel((100, 100)))
        self.assertEqual(self.world.get_actors_from_pixel((100, 100)), [])

    def test_radius_queries_return_empty(self):
        self.assertEqual(self.world.get_tiles_in_radius((0, 0), 2), [])
        self.assertEqual(self.world.get_tiles_in_ring((0, 0), 1), [])


if __name__ == "__main__":
    unittest.main()
