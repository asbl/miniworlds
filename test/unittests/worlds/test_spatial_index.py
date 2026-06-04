import unittest

import pygame

from miniworlds.worlds.manager.spatial_index import SpatialIndex


class TestSpatialIndex(unittest.TestCase):
    def setUp(self):
        self.index = SpatialIndex(cell_size=32)
        self.actor = object()

    def test_rect_crossing_cells_is_found_from_each_cell(self):
        self.index.update(self.actor, pygame.Rect(20, 20, 30, 30))

        self.assertIn(self.actor, self.index.query_point((20, 20)))
        self.assertIn(self.actor, self.index.query_point((49, 49)))

    def test_update_removes_actor_from_old_cells(self):
        self.index.update(self.actor, pygame.Rect(0, 0, 10, 10))
        self.index.update(self.actor, pygame.Rect(96, 0, 10, 10))

        self.assertNotIn(self.actor, self.index.query_point((5, 5)))
        self.assertIn(self.actor, self.index.query_point((100, 5)))

    def test_remove_clears_actor_registration(self):
        self.index.update(self.actor, pygame.Rect(0, 0, 80, 80))

        self.index.remove(self.actor)

        self.assertEqual(len(self.index), 0)
        self.assertNotIn(self.actor, self.index.query_rect(pygame.Rect(0, 0, 80, 80)))

    def test_negative_coordinates_use_negative_cells(self):
        self.index.update(self.actor, pygame.Rect(-40, -40, 20, 20))

        self.assertIn(self.actor, self.index.query_point((-32, -32)))
        self.assertNotIn(self.actor, self.index.query_point((0, 0)))

    def test_query_rect_returns_candidates_from_all_covered_cells(self):
        first = object()
        second = object()
        self.index.update(first, pygame.Rect(0, 0, 10, 10))
        self.index.update(second, pygame.Rect(64, 64, 10, 10))

        self.assertEqual(
            self.index.query_rect(pygame.Rect(0, 0, 96, 96)),
            {first, second},
        )


if __name__ == "__main__":
    unittest.main()
