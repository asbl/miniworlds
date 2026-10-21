"""Unit tests for HexWorld: tiles, corners, edges, picking, and queries."""

from __future__ import annotations

import unittest

from miniworlds import Actor, App
from miniworlds.worlds.hex_world.hex_corner import HexCorner
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


if __name__ == "__main__":
    unittest.main()
