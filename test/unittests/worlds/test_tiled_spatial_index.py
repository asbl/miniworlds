import unittest

from miniworlds import Actor
from miniworlds.base.app import App
from miniworlds.worlds.manager.tiled_spatial_index import TiledSpatialIndex
from miniworlds.worlds.tiled_world.tiled_world import TiledWorld


class TestTiledSpatialIndex(unittest.TestCase):
    def setUp(self):
        self.index = TiledSpatialIndex(chunk_size=4)
        self.actor1 = type("Actor", (), {"position": (1, 1), "size": (1, 1)})()
        self.actor2 = type("Actor", (), {"position": (1, 1), "size": (1, 1)})()
        self.actor3 = type("Actor", (), {"position": (5, 5), "size": (1, 1)})()

    def test_update_and_query_exact_position(self):
        """Test that actors can be added and queried by exact position."""
        self.index.update(self.actor1)

        result = self.index.query_exact_position((1, 1))
        self.assertIn(self.actor1, result)
        self.assertEqual(len(result), 1)

    def test_query_exact_position_filters_by_position(self):
        """Test that query_exact_position only returns actors at the exact position."""
        self.index.update(self.actor1)  # position (1, 1)
        self.index.update(self.actor3)  # position (5, 5)

        result = self.index.query_exact_position((1, 1))
        self.assertIn(self.actor1, result)
        self.assertNotIn(self.actor3, result)

    def test_multiple_actors_at_same_position(self):
        """Test that multiple actors at the same position are all returned."""
        self.index.update(self.actor1)  # position (1, 1)
        self.index.update(self.actor2)  # position (1, 1)

        result = self.index.query_exact_position((1, 1))
        self.assertEqual(len(result), 2)
        self.assertIn(self.actor1, result)
        self.assertIn(self.actor2, result)

    def test_remove_actor(self):
        """Test that removed actors are no longer in the index."""
        self.index.update(self.actor1)
        self.index.remove(self.actor1)

        result = self.index.query_exact_position((1, 1))
        self.assertEqual(len(result), 0)

    def test_update_moves_actor(self):
        """Test that updating an actor's position moves it in the index."""
        # Start at (1, 1)
        self.actor1.position = (1, 1)
        self.index.update(self.actor1)

        # Move to (5, 5)
        self.actor1.position = (5, 5)
        self.index.update(self.actor1)

        result_old = self.index.query_exact_position((1, 1))
        result_new = self.index.query_exact_position((5, 5))

        self.assertNotIn(self.actor1, result_old)
        self.assertIn(self.actor1, result_new)

    def test_update_moves_actor_within_same_chunk(self):
        """Position lookup must update even when the chunk membership is unchanged."""
        self.actor1.position = (1, 1)
        self.index.update(self.actor1)

        self.actor1.position = (2, 2)
        self.index.update(self.actor1)

        self.assertNotIn(self.actor1, self.index.query_exact_position((1, 1)))
        self.assertIn(self.actor1, self.index.query_exact_position((2, 2)))

    def test_query_rect(self):
        """Test rectangular region queries."""
        self.index.update(self.actor1)  # (1, 1)
        self.index.update(self.actor3)  # (5, 5)

        # Query a rect that contains both
        result = self.index.query_rect((0, 0), (10, 10))
        self.assertIn(self.actor1, result)
        self.assertIn(self.actor3, result)

        # Query a rect that contains only actor1
        result = self.index.query_rect((0, 0), (2, 2))
        self.assertIn(self.actor1, result)
        self.assertNotIn(self.actor3, result)

    def test_query_rect_filters_same_chunk_actors_outside_rect(self):
        """Rect queries should not return every actor in an overlapping chunk."""
        actor_inside = type("Actor", (), {"position": (1, 1), "size": (1, 1)})()
        actor_outside = type("Actor", (), {"position": (3, 3), "size": (1, 1)})()
        self.index.update(actor_inside)
        self.index.update(actor_outside)

        result = self.index.query_rect((0, 0), (1, 1))

        self.assertIn(actor_inside, result)
        self.assertNotIn(actor_outside, result)

    def test_query_position_returns_chunk_members(self):
        """Test that query_position returns all actors in the same chunk."""
        self.index.update(self.actor1)  # (1, 1) -> chunk (0, 0) with chunk_size=4
        self.index.update(self.actor3)  # (5, 5) -> chunk (1, 1)

        # Query position (1, 1) should return actors from chunk (0, 0)
        result = self.index.query_position((1, 1))
        self.assertIn(self.actor1, result)
        # Note: actor3 is in a different chunk, so not included
        self.assertNotIn(self.actor3, result)

    def test_clear(self):
        """Test that clear removes all entries."""
        self.index.update(self.actor1)
        self.index.update(self.actor2)
        self.index.update(self.actor3)

        self.index.clear()

        self.assertEqual(len(self.index), 0)
        result = self.index.query_exact_position((1, 1))
        self.assertEqual(len(result), 0)

    def test_contains(self):
        """Test the __contains__ method."""
        self.assertNotIn(self.actor1, self.index)

        self.index.update(self.actor1)
        self.assertIn(self.actor1, self.index)

        self.index.remove(self.actor1)
        self.assertNotIn(self.actor1, self.index)

    def test_len(self):
        """Test the __len__ method."""
        self.assertEqual(len(self.index), 0)

        self.index.update(self.actor1)
        self.assertEqual(len(self.index), 1)

        self.index.update(self.actor2)
        self.assertEqual(len(self.index), 2)

        self.index.remove(self.actor1)
        self.assertEqual(len(self.index), 1)

    def test_invalid_chunk_size(self):
        """Test that invalid chunk size raises ValueError."""
        with self.assertRaises(ValueError):
            TiledSpatialIndex(chunk_size=0)
        with self.assertRaises(ValueError):
            TiledSpatialIndex(chunk_size=-1)

    def test_actor_with_larger_size(self):
        """Test actors that span multiple tiles."""
        large_actor = type("Actor", (), {"position": (1, 1), "size": (3, 3)})()
        self.index.update(large_actor)

        # Actor spans tiles (1,1), (2,1), (3,1), (1,2), (2,2), (3,2), (1,3), (2,3), (3,3)
        # All these positions should find the actor when querying exact position
        result = self.index.query_exact_position((1, 1))
        self.assertIn(large_actor, result)


class TestTiledSpatialIndexIntegration(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = TiledWorld(10, 7)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_tiled_world_actor_is_indexed_at_initial_position(self):
        actor = Actor((2, 3), world=self.world)

        self.assertIn(actor, self.world._tiled_spatial_index)
        self.assertEqual(self.world.detect_actors_at_position((2, 3)), [actor])

    def test_tiled_world_index_tracks_actor_movement(self):
        actor = Actor((1, 1), world=self.world)

        actor.move_to((4, 2))

        self.assertNotIn(actor, self.world.detect_actors_at_position((1, 1)))
        self.assertIn(actor, self.world.detect_actors_at_position((4, 2)))

    def test_tiled_world_actor_uses_tile_footprint_not_pixel_size(self):
        actor = Actor((1, 1), world=self.world)

        self.assertEqual(len(self.world._tiled_spatial_index._chunks), 1)
        self.assertIn(actor, self.world._tiled_spatial_index.query_exact_position((1, 1)))

    def test_tiled_world_index_removes_actor(self):
        actor = Actor((1, 1), world=self.world)

        actor.remove()

        self.assertNotIn(actor, self.world._tiled_spatial_index)
        self.assertEqual(self.world.detect_actors_at_position((1, 1)), [])


if __name__ == "__main__":
    unittest.main()
