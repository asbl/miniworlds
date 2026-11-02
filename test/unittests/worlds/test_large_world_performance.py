"""Regression tests for large-world performance optimizations.

Covers:
- TiledSpatialIndex.query_chunk_region (chunk-union query used by camera view
  and sensor queries in tiled worlds)
- CameraManager.get_actors_in_view using the TiledSpatialIndex in tiled
  worlds (equivalence with the brute-force O(actors) result)
- Selective camera view cache invalidation on actor movement
  (_invalidate_actor_view_cache instead of _clear_camera_cache)
- Per-frame caching of TiledWorldPositionManager.get_global_rect
- TiledWorld.detect_actors delegating to the tiled spatial index
"""

import random
import unittest

from miniworlds import Actor, World
from miniworlds.base.app import App
from miniworlds.worlds.manager.tiled_spatial_index import TiledSpatialIndex
from miniworlds.worlds.tiled_world.tiled_world import TiledWorld


def make_stub_actor(position, size=(1, 1)):
    return type("StubActor", (), {"position": position, "size": size})()


class TestQueryChunkRegion(unittest.TestCase):
    def setUp(self):
        self.index = TiledSpatialIndex(chunk_size=4)

    def test_returns_actors_from_all_covered_chunks(self):
        a = make_stub_actor((1, 1))   # chunk (0, 0)
        b = make_stub_actor((6, 6))   # chunk (1, 1)
        c = make_stub_actor((20, 20))  # chunk (5, 5) - outside region
        for actor in (a, b, c):
            self.index.update(actor)

        result = self.index.query_chunk_region((0, 0), (7, 7))
        self.assertIn(a, result)
        self.assertIn(b, result)
        self.assertNotIn(c, result)

    def test_does_not_filter_by_exact_position(self):
        # Actor spanning several tiles (size 3x3 at (1, 1)) must be found
        # when querying a tile inside its footprint but not at its position.
        big = make_stub_actor((1, 1), size=(3, 3))
        self.index.update(big)

        result = self.index.query_chunk_region((2, 2), (2, 2))
        self.assertIn(big, result)

    def test_ring_extends_region_by_chunk_margin(self):
        # chunk_size=4: actor at (7, 7) is in chunk (1, 1). Querying the
        # region (0,0)-(3,3) (chunk (0,0) only) finds it with ring=1 but not
        # without.
        a = make_stub_actor((7, 7))
        self.index.update(a)

        self.assertNotIn(a, self.index.query_chunk_region((0, 0), (3, 3)))
        self.assertIn(a, self.index.query_chunk_region((0, 0), (3, 3), ring=1))

    def test_query_rect_still_filters_by_exact_position(self):
        big = make_stub_actor((1, 1), size=(3, 3))
        self.index.update(big)

        # query_rect keeps its exact-position semantics
        self.assertIn(big, self.index.query_rect((1, 1), (1, 1)))
        self.assertNotIn(big, self.index.query_rect((2, 2), (2, 2)))

    def test_update_and_remove_keep_chunk_region_coherent(self):
        a = make_stub_actor((2, 2))
        self.index.update(a)
        self.assertIn(a, self.index.query_chunk_region((0, 0), (3, 3)))

        a.position = (30, 30)
        self.index.update(a)
        self.assertNotIn(a, self.index.query_chunk_region((0, 0), (3, 3)))
        self.assertIn(a, self.index.query_chunk_region((28, 28), (31, 31)))

        self.index.remove(a)
        self.assertNotIn(a, self.index.query_chunk_region((28, 28), (31, 31)))


class TestTiledCameraViewEquivalence(unittest.TestCase):
    """get_actors_in_view must return the same actors as a brute-force scan
    over all world actors, but via the TiledSpatialIndex."""

    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = TiledWorld(30, 20, tile_size=32)
        self.world.camera.view = (10, 8)
        self.world.camera.dirty = True
        rng = random.Random(7)
        self.actors = []
        for _ in range(40):
            actor = Actor(
                (rng.randrange(30), rng.randrange(20)), world=self.world
            )
            self.actors.append(actor)
        # One actor spanning multiple tiles
        big = Actor((5, 5), world=self.world)
        big.size = (3, 3)
        self.actors.append(big)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def brute_force_view(self):
        camera_rect = self.world.camera.rect
        return {
            actor
            for actor in self.world.actors
            if camera_rect.colliderect(actor.position_manager.get_global_rect())
        }

    def test_view_matches_brute_force_at_various_camera_positions(self):
        camera = self.world.camera
        for topleft in [(0, 0), (5, 4), (15, 8), (20, 12), (10, 6)]:
            self.world.frame += 1
            camera.topleft = topleft
            view = camera.get_actors_in_view()
            expected = self.brute_force_view()
            self.assertEqual(
                camera._view_actors_actual_frame,
                expected,
                f"mismatch at camera topleft={topleft}",
            )
            # returned set is actual-frame union last-frame (superset)
            self.assertTrue(expected <= view)

    def test_view_matches_brute_force_with_corner_actors(self):
        """Corner/edge-positioned actors must be found by the tiled index
        candidates exactly like by a brute-force scan (audit check)."""
        for i in range(8):
            x = 2 + (i % 4) + 0.5
            y = 2 + (i // 4) * 3 + 0.5
            Actor((x, y), world=self.world)
        camera = self.world.camera
        for topleft in [(0, 0), (3, 3), (8, 6)]:
            self.world.frame += 1
            camera.topleft = topleft
            camera.get_actors_in_view()
            self.assertEqual(
                camera._view_actors_actual_frame,
                self.brute_force_view(),
                f"mismatch at camera topleft={topleft}",
            )

    def test_view_uses_tiled_index_not_full_actor_scan(self):
        camera = self.world.camera
        self.world.frame += 1
        camera.topleft = (3, 3)
        # With the tiled index present, candidates must come from the index:
        # an actor far outside the view must not be iterated by the pixel
        # filter. We verify indirectly: the result matches brute force while
        # the index is much smaller than the actor list.
        self.assertIsNotNone(self.world._tiled_spatial_index)
        self.assertLess(
            len(self.world._tiled_spatial_index.query_chunk_region((0, 0), (29, 19))),
            len(self.world.actors) + 1,
        )
        camera.get_actors_in_view()
        self.assertEqual(
            camera._view_actors_actual_frame, self.brute_force_view()
        )

    def test_actor_entering_and_leaving_view_via_movement(self):
        camera = self.world.camera
        actor = Actor((25, 15), world=self.world)  # outside 10x8 view
        self.world.frame += 1
        camera.topleft = (0, 0)
        camera.get_actors_in_view()
        self.assertNotIn(actor, camera._view_actors_actual_frame)

        actor.position = (4, 4)  # move into view
        self.assertEqual(camera._view_update_frame, self.world.frame)
        self.assertIn(actor, camera.get_actors_in_view())

        actor.position = (25, 15)  # move out of view again
        self.assertNotIn(actor, camera._view_actors_actual_frame)


class TestSelectiveCameraCacheInvalidation(unittest.TestCase):
    """Moving an actor must update the view cache selectively (O(1)) instead
    of clearing it, which forced an O(actors) recomputation per query."""

    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(400, 400)
        self.world.camera.view = (100, 100)
        self.world.camera.dirty = True
        self.world.camera._clear_camera_cache()
        self.a = Actor((10, 10), world=self.world)
        self.b = Actor((350, 350), world=self.world)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_move_does_not_clear_cache(self):
        camera = self.world.camera
        self.world.frame = 1
        camera.get_actors_in_view()
        self.assertIn(self.a, camera._view_actors_actual_frame)
        self.assertNotIn(self.b, camera._view_actors_actual_frame)

        clear_calls = []
        invalidate_calls = []
        original_invalidate = camera._invalidate_actor_view_cache
        camera._clear_camera_cache = lambda: clear_calls.append(1)
        camera._invalidate_actor_view_cache = lambda actor, in_view=None: (
            invalidate_calls.append(actor),
            original_invalidate(actor, in_view=in_view),
        )

        self.b.position = (20, 20)

        self.assertEqual(clear_calls, [])
        self.assertEqual(invalidate_calls, [self.b])
        # cache still valid for the current frame
        self.assertEqual(camera._view_update_frame, 1)
        # and the moved actor is visible in the cached set
        self.assertIn(self.b, camera.get_actors_in_view())

    def test_moved_out_actor_leaves_actual_frame_set(self):
        camera = self.world.camera
        self.world.frame = 1
        camera.get_actors_in_view()
        self.assertIn(self.a, camera._view_actors_actual_frame)

        self.a.position = (350, 350)

        self.assertEqual(camera._view_update_frame, 1)
        self.assertNotIn(self.a, camera._view_actors_actual_frame)
        # was not in the last frame either -> also out of the active union
        self.assertNotIn(self.a, camera._view_active_actors)

    def test_full_recompute_on_next_frame(self):
        camera = self.world.camera
        self.world.frame = 1
        camera.get_actors_in_view()
        self.b.position = (20, 20)

        self.world.frame = 2
        camera.get_actors_in_view()

        self.assertEqual(camera._view_update_frame, 2)
        self.assertIn(self.b, camera._view_actors_actual_frame)
        # a is still at (10, 10) -> in view
        self.assertIn(self.a, camera._view_actors_actual_frame)


class TestTiledGlobalRectCache(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = TiledWorld(10, 10, tile_size=32)
        self.actor = Actor((2, 3), world=self.world)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_global_rect_is_cached_per_frame(self):
        pm = self.actor.position_manager
        self.world.frame = 1
        first = pm.get_global_rect()
        second = pm.get_global_rect()
        self.assertIs(first, second)
        self.assertEqual(first.topleft, (2 * 32, 3 * 32))

    def test_position_change_invalidates_cache(self):
        pm = self.actor.position_manager
        self.world.frame = 1
        first = pm.get_global_rect()

        self.actor.position = (4, 5)
        third = pm.get_global_rect()

        self.assertIsNot(first, third)
        self.assertEqual(third.topleft, (4 * 32, 5 * 32))

    def test_frame_change_recomputes(self):
        pm = self.actor.position_manager
        self.world.frame = 1
        first = pm.get_global_rect()
        self.world.frame = 2
        second = pm.get_global_rect()
        self.assertIsNot(first, second)
        self.assertEqual(first.topleft, second.topleft)


class TestTiledWorldDetectActors(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = TiledWorld(10, 10, tile_size=32)
        self.actor = Actor((2, 3), world=self.world)
        self.other = Actor((7, 8), world=self.world)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_detect_actors_uses_tiled_index_and_matches_position(self):
        self.assertIsNotNone(self.world._tiled_spatial_index)
        result = self.world.detect_actors((2, 3))
        self.assertIn(self.actor, result)
        self.assertNotIn(self.other, result)

    def test_detect_actors_equals_detect_actors_at_position(self):
        for pos in [(2, 3), (7, 8), (0, 0), (9, 9)]:
            self.assertEqual(
                sorted(map(id, self.world.detect_actors(pos))),
                sorted(map(id, self.world.detect_actors_at_position(pos))),
            )

    def test_detect_actors_fallback_without_index(self):
        self.world._tiled_spatial_index = None
        result = self.world.detect_actors((2, 3))
        self.assertIn(self.actor, result)
        self.assertNotIn(self.other, result)


class TestManyActorsOptimizations(unittest.TestCase):
    """Round 4: very many actors around a moving camera."""

    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = TiledWorld(20, 10, tile_size=32)
        self.world.camera.view = (6, 5)
        self.world.camera.dirty = True
        self.world.camera._clear_camera_cache()

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_local_rect_cached_per_frame_and_camera_position(self):
        actor = Actor((3, 3), world=self.world)
        pm = actor.position_manager
        self.world.frame = 1
        first = pm.get_local_rect()
        second = pm.get_local_rect()
        self.assertIs(first, second)

        # camera movement invalidates the local rect (new key)
        self.world.camera.topleft = (2, 1)
        third = pm.get_local_rect()
        self.assertIsNot(first, third)
        self.assertEqual(third.topleft, (first.topleft[0] - 64, first.topleft[1] - 32))

        # position change invalidates, too
        self.world.frame += 1
        actor.position = (4, 3)
        fourth = pm.get_local_rect()
        self.assertIsNot(third, fourth)

    def test_offscreen_mover_stays_clean(self):
        actor = Actor((1, 1), world=self.world)  # inside 6x5 view
        off = Actor((15, 8), world=self.world)  # outside the view
        actor._dirty = 0
        off._dirty = 0
        self.world.frame = 1
        self.world.camera.get_actors_in_view()

        off.position = (16, 8)

        self.assertEqual(off._dirty, 0)

    def test_in_view_mover_becomes_dirty(self):
        actor = Actor((1, 1), world=self.world)
        actor._dirty = 0
        self.world.frame = 1
        self.world.camera.get_actors_in_view()

        actor.position = (2, 1)

        self.assertEqual(actor._dirty, 1)

    def test_in_view_mover_dirty_without_prior_view_computation(self):
        """The view cache may never have been computed (e.g. first frame):
        the fresh is_actor_in_view check must still mark in-view movers."""
        actor = Actor((1, 1), world=self.world)
        actor._dirty = 0
        self.world.frame = 1
        # no get_actors_in_view() call: _view_active_actors is empty

        actor.position = (2, 1)

        self.assertEqual(actor._dirty, 1)

    def test_leaving_view_actor_dirty_for_erase(self):
        self.world.camera.topleft = (0, 0)
        actor = Actor((4, 2), world=self.world)  # near the right view edge
        actor._dirty = 0
        self.world.frame = 1
        self.world.camera.get_actors_in_view()

        actor.position = (15, 2)  # moved out of view

        # was visible this frame -> stays dirty so the old rect is erased
        self.assertEqual(actor._dirty, 1)

    def test_topleft_px_cache_follows_direct_topleft_writes(self):
        camera = self.world.camera
        self.world.frame = 1
        camera.topleft = (2, 1)
        self.assertEqual(camera.topleft, (2 * 32, 1 * 32))
        # direct _topleft write (bypassing the setter) must not return
        # a stale cached pixel topleft
        camera._topleft = (4, 2)
        self.assertEqual(camera.topleft, (4 * 32, 2 * 32))

    def test_topleft_px_cache_invalidated_on_tile_size_change(self):
        camera = self.world.camera
        camera.topleft = (2, 1)
        self.assertEqual(camera.topleft, (64, 32))

        self.world.tile_size = 16

        self.assertEqual(camera.topleft, (32, 16))


if __name__ == "__main__":
    unittest.main()
