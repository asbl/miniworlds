"""Regression tests for HexWorld camera scrolling and setup optimization.

Covers:
- `HexWorld.view_position_range`: candidate lookup must cover visible
  tile, corner, and edge actors for any scrolled camera position (the
  square-tile pixel division underestimates hex position spaces).
- `TiledWorld._static_layer_candidates`: static actors must be part of
  the static layer rebuild while the hex camera is scrolled.
- The hex grid overlay: pixel-identical at camera topleft (0, 0), drawn
  for the visible window (and world-anchored) when the camera is scrolled.
- The setup fast paths (`_setup_tiles` / `_setup_corners` /
  `_setup_edges`): the world model must be identical to the state built
  via the public `add_*_to_world` API.
- `get_tile_from_pixel`: returns the registered tile object.
"""

from __future__ import annotations

import unittest

import pygame

from miniworlds import Actor, App
from miniworlds.worlds.hex_world.hex_world import HexWorld
from miniworlds.worlds.hex_world import hex_coords


class HexScrollTestBase(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(20, 20, tile_size=40)
        self.world.camera._strict = False

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def set_view(self, width, height) -> None:
        self.world.camera.width = width
        self.world.camera.height = height


class TestHexCameraViewCandidates(HexScrollTestBase):
    """get_actors_in_view must find tile, corner, and edge actors."""

    def brute_force_view(self):
        camera_rect = self.world.camera.get_rect()
        return {
            actor
            for actor in self.world.actors
            if camera_rect.colliderect(actor.position_manager.get_global_rect())
        }

    def test_view_matches_brute_force_when_scrolled(self):
        world = self.world
        # Tile actors over the whole map.
        for x in range(0, 20, 2):
            for y in range(0, 20, 2):
                Actor((x, y), world=world)
        # Corner and edge actors in the region the camera will scroll to.
        for x in range(6, 16):
            for y in range(6, 16):
                Actor(world.get_corner((x, y), "no").position, world=world)
                Actor(world.get_edge((x, y), "o").position, world=world)
        self.set_view(6, 4)
        camera = world.camera
        for topleft in [(0, 0), (5, 4), (10, 8), (14, 11), (13, 5)]:
            with self.subTest(topleft=topleft):
                world.frame += 1
                camera.topleft = topleft
                camera.get_actors_in_view()
                self.assertEqual(
                    camera._view_actors_actual_frame,
                    self.brute_force_view(),
                    "view set mismatch at camera topleft "
                    f"{topleft}; hex candidates miss or overshoot",
                )

    def test_view_ranges_cover_all_position_spaces(self):
        # A rect deep inside a large world, where a plain tile-size division
        # runs out of sync with hex coordinates.
        big = HexWorld(80, 80, tile_size=40)
        self.addCleanup(App.reset, unittest=True)
        big.camera._strict = False
        big.camera.width = 8
        big.camera.height = 6
        big.camera.topleft = (40, 40)
        rect = big.camera.get_rect()
        ranges = big.view_position_ranges(rect)
        self.assertEqual(len(ranges), 3)
        (tile_min, tile_max), (corner_min, corner_max), (edge_min, edge_max) = (ranges)

        # Visible tiles around (40, 40) must be inside the tile range: the
        # old square-tile division computed (69, 60) instead and missed them.
        for position in ((39, 39), (47, 45)):
            self.assertLessEqual(tile_min[0], position[0])
            self.assertGreaterEqual(tile_max[0], position[0])
            self.assertLessEqual(tile_min[1], position[1])
            self.assertGreaterEqual(tile_max[1], position[1])

        # Corner (3 * cube) and edge (2 * cube) positions of those tiles
        # must be inside their own ranges; a distant corner must not be.
        for position in ((39, 39), (47, 45)):
            q, r, _s = hex_coords.offset_to_cube(position)
            self.assertLessEqual(corner_min[0], 3 * q)
            self.assertGreaterEqual(corner_max[0], 3 * q)
            self.assertLessEqual(corner_min[1], 3 * r)
            self.assertGreaterEqual(corner_max[1], 3 * r)
            self.assertLessEqual(edge_min[0], 2 * q)
            self.assertGreaterEqual(edge_max[0], 2 * q)
            self.assertLessEqual(edge_min[1], 2 * r)
            self.assertGreaterEqual(edge_max[1], 2 * r)

        # Ranges must be view-bounded, not world-bounded: a far corner
        # position (e.g. from tile (60, 70)) must be outside the range.
        far_q, far_r, _s = hex_coords.offset_to_cube((60, 70))
        outside_corner = 3 * far_q < corner_min[0] - 8 or 3 * far_q > corner_max[0] + 8
        outside_corner = outside_corner or (
            3 * far_r < corner_min[1] - 8 or 3 * far_r > corner_max[1] + 8
        )
        self.assertTrue(
            outside_corner,
            "corner range must stay bounded by the visible window",
        )


class TestHexStaticLayerWhenScrolled(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(80, 80, tile_size=40)
        self.world.camera._strict = False

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def set_view(self, width, height) -> None:
        self.world.camera.width = width
        self.world.camera.height = height

    def test_visible_static_actor_is_a_layer_candidate(self):
        world = self.world
        actor = Actor((44, 42), world=world)
        actor.add_costume((220, 20, 20, 255))
        actor.static = True
        # A static actor far away from the scrolled view: candidates must
        # stay view-bounded (this was a full-world scan before the index
        # candidates existed).
        far_actor = Actor((2, 2), world=world)
        far_actor.add_costume((20, 20, 220, 255))
        far_actor.static = True
        self.set_view(6, 4)
        world.camera.topleft = (40, 40)
        actor_rect = actor.position_manager.get_global_rect()
        self.assertTrue(
            world.camera.get_rect().colliderect(actor_rect),
            "precondition: actor must be visible for the scrolled camera",
        )
        self.assertFalse(
            world.camera.get_rect().colliderect(
                far_actor.position_manager.get_global_rect()
            ),
            "precondition: far actor must be outside the camera view",
        )
        candidates = list(world._static_layer_candidates())
        # The regression this guards against: the pixel->position conversion
        # for the chunk query used square-tile math and the visible actor
        # dropped out of the candidates, so it vanished from the layer.
        self.assertIn(actor, candidates)
        self.assertNotIn(far_actor, candidates)
        # The rebuild must run through with the scrolled camera and produce
        # a camera-sized layer.
        world._static_tile_layer_dirty = True
        layer, rebuilt = world._refresh_static_tile_layer()
        self.assertIsInstance(layer, pygame.Surface)
        self.assertTrue(rebuilt)
        self.assertEqual(layer.get_size(), world.camera.get_rect().size)


class TestHexGridOverlay(HexScrollTestBase):
    def draw_grid(self):
        surface = pygame.Surface(
            (self.world.camera.width, self.world.camera.height), pygame.SRCALPHA
        )
        manager = self.world.background.transformations_manager
        manager._transformation_grid_hex(surface, self.world.background)
        return surface

    def reference_grid(self, origin=(0, 0)):
        """Draw all tiles at world coordinates minus `origin` (old code)."""
        surface = pygame.Surface(
            (self.world.camera.width, self.world.camera.height), pygame.SRCALPHA
        )
        color = self.world.background._grid_color
        for position in self.world.tiles:
            points = hex_coords.corner_pixel_points(
                position, self.world.tile_size
            )
            points = [(x - origin[0], y - origin[1]) for x, y in points]
            pygame.draw.polygon(surface, color, points, 1)
        return surface

    def test_grid_is_pixel_identical_at_origin(self):
        self.set_view(6, 4)
        self.assertEqual(
            pygame.image.tobytes(self.draw_grid(), "RGBA"),
            pygame.image.tobytes(self.reference_grid(), "RGBA"),
        )

    def test_grid_follows_scrolled_camera(self):
        world = self.world
        self.set_view(6, 4)
        world.camera.topleft = (7, 9)
        surface = self.draw_grid()
        # The grid must be drawn for the world window the camera looks at
        # (world pixels minus the camera topleft), pixel-identical to a
        # reference that draws every tile at its world position shifted
        # by the camera topleft.
        reference = self.reference_grid(origin=world.camera.topleft)
        self.assertGreater(
            pygame.mask.from_surface(surface, 1).count(), 0,
            "the scrolled grid must contain outlines at all",
        )
        self.assertEqual(
            pygame.image.tobytes(surface, "RGBA"),
            pygame.image.tobytes(reference, "RGBA"),
            "the scrolled grid must match the world window, not the "
            "unshifted origin grid",
        )

    def test_grid_skips_missing_tiles_on_irregular_maps(self):
        world = HexWorld(10, 10, tile_size=40, empty=True)
        self.addCleanup(App.reset, unittest=True)
        for position in [(4, 4), (5, 4), (4, 5), (5, 5)]:
            world.add_tile_to_world(position)
        world.camera._strict = False
        world.camera.width = 10
        world.camera.height = 6
        surface = pygame.Surface(
            (world.camera.width, world.camera.height), pygame.SRCALPHA
        )
        manager = world.background.transformations_manager
        manager._transformation_grid_hex(surface, world.background)
        self.assertGreater(
            pygame.mask.from_surface(surface, 1).count(), 0,
            "the existing tiles must have grid outlines",
        )
        # The reference draws outlines exactly for the registered tiles:
        # matching it means positions without tiles show no outlines.
        reference = pygame.Surface(
            (world.camera.width, world.camera.height), pygame.SRCALPHA
        )
        color = world.background._grid_color
        for position in world.tiles:
            points = hex_coords.corner_pixel_points(position, world.tile_size)
            pygame.draw.polygon(reference, color, points, 1)
        self.assertEqual(
            pygame.image.tobytes(surface, "RGBA"),
            pygame.image.tobytes(reference, "RGBA"),
        )


class TestHexSetupFastPathParity(unittest.TestCase):
    """The optimized setup must build the same world model as the public API."""

    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def build_reference_world(self, size):
        world = HexWorld(size, size, tile_size=40, empty=True)
        tile_cls, edge_cls, corner_cls = world._templates()
        for x in range(size):
            for y in range(size):
                world.add_tile_to_world((x, y))
        for tile_position in list(world.tiles):
            for direction in tile_cls.corner_vectors:
                world.add_corner_to_world(tile_position, direction)
        for tile_position in list(world.tiles):
            for direction in tile_cls.edge_vectors:
                world.add_edge_to_world(tile_position, direction)
        return world

    def test_setup_builds_same_model_as_public_api(self):
        size = 6
        fast_world = HexWorld(size, size, tile_size=40)
        world = self.build_reference_world(size)

        self.assertEqual(len(fast_world.tiles), len(world.tiles))
        self.assertEqual(len(fast_world.corners), len(world.corners))
        self.assertEqual(len(fast_world.edges), len(world.edges))
        self.assertEqual(set(fast_world.tiles), set(world.tiles))
        self.assertEqual(set(fast_world.corners), set(world.corners))
        self.assertEqual(set(fast_world.edges), set(world.edges))

        # Merged references (order included) must match.
        for position, corner in world.corners.items():
            self.assertEqual(
                fast_world.corners[position].positions,
                corner.positions,
                f"corner reference mismatch at {position}",
            )
        for position, edge in world.edges.items():
            self.assertEqual(
                fast_world.edges[position].positions,
                edge.positions,
                f"edge reference mismatch at {position}",
            )

        # Neighbour queries must return identical tiles.
        for position in [(0, 0), (3, 2), (5, 5), (2, 3)]:
            fast_neighbours = [
                tile.position
                for tile in fast_world.get_tile(position).get_neighbour_tiles()
            ]
            reference_neighbours = [
                tile.position
                for tile in world.get_tile(position).get_neighbour_tiles()
            ]
            self.assertEqual(fast_neighbours, reference_neighbours)

        # Corner and edge neighbour reconstruction must work identically.
        corner = fast_world.get_corner((3, 3), "no")
        reference_corner = world.get_corner((3, 3), "no")
        self.assertEqual(
            [tile.position for tile in corner.get_neighbour_tiles()],
            [tile.position for tile in reference_corner.get_neighbour_tiles()],
        )
        edge = fast_world.get_edge((3, 3), "o")
        reference_edge = world.get_edge((3, 3), "o")
        self.assertEqual(
            [tile.position for tile in edge.get_neighbour_tiles()],
            [tile.position for tile in reference_edge.get_neighbour_tiles()],
        )


class TestHexTilePickingIdentity(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_get_tile_from_pixel_returns_registered_tile(self):
        for position in [(0, 0), (3, 3), (6, 6), (4, 1)]:
            with self.subTest(position=position):
                pixel = self.world.to_pixel(position)
                tile = self.world.get_tile_from_pixel(pixel)
                self.assertIsNotNone(tile)
                self.assertIs(tile, self.world.get_tile(position))

    def test_get_tile_from_pixel_outside_returns_none(self):
        self.assertIsNone(self.world.get_tile_from_pixel((-5, -5)))
        self.assertIsNone(self.world.get_tile_from_pixel((5000, 5000)))


if __name__ == "__main__":
    unittest.main()


class TestStaticLayerBackground(HexScrollTestBase):
    def test_scrolled_layer_preserves_camera_local_background(self):
        world = self.world
        self.set_view(5, 4)
        world.add_background((35, 55, 75, 255))
        world.background.grid = True
        for position in [(0, 0), (4, 3), (10, 8)]:
            with self.subTest(position=position):
                world.camera.topleft = position
                world.background.set_dirty("all", world.background.LOAD_NEW_IMAGE)
                expected = world.background.image.copy()
                world._rebuild_static_tile_layer()
                self.assertEqual(
                    pygame.image.tostring(world._static_tile_layer, "RGBA"),
                    pygame.image.tostring(expected, "RGBA"),
                )
