"""Unit tests for find_nearest, has_line_of_sight, and get_path_cost on HexWorld."""

from __future__ import annotations

import unittest

from miniworlds import Actor, App
from miniworlds.worlds.hex_world import hex_coords
from miniworlds.worlds.hex_world.hex_world import HexWorld


def _hex_distance(first, second) -> int:
    return hex_coords.cube_distance(
        hex_coords.offset_to_cube(first), hex_coords.offset_to_cube(second)
    )


class TestFindNearest(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(9, 9, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def _mark(self, *positions):
        for position in positions:
            self.world.get_tile(position).terrain = "forest"

    def _is_forest(self, tile):
        return tile.terrain == "forest"

    def test_returns_path_to_the_nearest_target(self):
        self._mark((7, 4), (2, 4))
        path = self.world.find_nearest((0, 4), self._is_forest)
        self.assertEqual(path[0].position, (0, 4))
        self.assertEqual(path[-1].position, (2, 4))
        for first, second in zip(path, path[1:]):
            self.assertIn(second, first.get_neighbour_tiles())

    def test_nearest_means_cheapest_not_closest(self):
        self._mark((2, 4), (0, 7))
        # (2, 4) is two hexes away but behind the expensive column 1;
        # (0, 7) is three hexes away along the cheap column 0.
        path = self.world.find_nearest(
            (0, 4), self._is_forest, cost=lambda tile: 10 if tile.position[0] == 1 else 1
        )
        self.assertEqual(path[-1].position, (0, 7))
        self.assertEqual(
            self.world.get_path_cost(path, cost=lambda tile: 10 if tile.position[0] == 1 else 1),
            3,
        )

    def test_no_target_returns_empty_list(self):
        self.assertEqual(self.world.find_nearest((0, 0), self._is_forest), [])

    def test_start_is_ignored_unless_requested(self):
        self._mark((4, 4), (6, 4))
        self.assertEqual(
            self.world.find_nearest((4, 4), self._is_forest)[-1].position, (6, 4)
        )
        path = self.world.find_nearest((4, 4), self._is_forest, include_start=True)
        self.assertEqual([tile.position for tile in path], [(4, 4)])

    def test_blocked_target_can_be_reached(self):
        enemy = Actor((5, 4), world=self.world)
        enemy.is_blocking = True
        path = self.world.find_nearest(
            (1, 4), lambda tile: (5, 4) == tile.position
        )
        self.assertEqual(path[-1].position, (5, 4))

    def test_blocked_hexes_are_not_walked_through(self):
        self._mark((6, 4))
        for tile in self.world.get_tiles_in_ring((6, 4), 1):
            tile.is_blocking = True
        # The target itself is free, but fully enclosed.
        self.assertEqual(self.world.find_nearest((0, 4), self._is_forest), [])

    def test_blocked_target_is_not_a_passage_to_a_second_target(self):
        self._mark((4, 4), (8, 4))
        enclosing = [t for t in self.world.get_tiles_in_ring((8, 4), 1)]
        for tile in enclosing:
            tile.is_blocking = True
        self.world.get_tile((4, 4)).is_blocking = True
        path = self.world.find_nearest((0, 4), self._is_forest)
        self.assertEqual(path[-1].position, (4, 4))

    def test_max_cost_limits_the_search(self):
        self._mark((6, 4))
        self.assertTrue(self.world.find_nearest((0, 4), self._is_forest, max_cost=6))
        self.assertEqual(
            self.world.find_nearest((0, 4), self._is_forest, max_cost=5), []
        )

    def test_custom_cost_is_used(self):
        self._mark((3, 4), (3, 0))
        path = self.world.find_nearest(
            (0, 4), self._is_forest, cost=lambda tile: 10 if tile.position[1] == 4 else 1
        )
        self.assertTrue(path)

    def test_accepts_actor_as_start(self):
        self._mark((4, 4))
        robot = Actor((1, 4), world=self.world)
        self.assertEqual(
            self.world.find_nearest(robot, self._is_forest)[-1].position, (4, 4)
        )


class TestLineOfSight(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(9, 9, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_clear_line_is_visible(self):
        self.assertTrue(self.world.has_line_of_sight((0, 4), (8, 4)))

    def test_blocked_hex_in_between_hides_the_goal(self):
        line = self.world.get_tiles_in_line((0, 4), (8, 4))
        line[4].is_blocking = True
        self.assertFalse(self.world.has_line_of_sight((0, 4), (8, 4)))

    def test_blocked_goal_and_start_do_not_count(self):
        self.world.get_tile((8, 4)).is_blocking = True
        self.world.get_tile((0, 4)).is_blocking = True
        self.assertTrue(self.world.has_line_of_sight((0, 4), (8, 4)))

    def test_neighbours_and_same_hex_are_visible(self):
        self.assertTrue(self.world.has_line_of_sight((3, 3), (4, 3)))
        self.assertTrue(self.world.has_line_of_sight((3, 3), (3, 3)))

    def test_blocking_actor_hides_the_goal(self):
        line = self.world.get_tiles_in_line((1, 1), (7, 5))
        wall = Actor(line[3].position, world=self.world)
        wall.is_blocking = True
        self.assertFalse(self.world.has_line_of_sight((1, 1), (7, 5)))

    def test_custom_blocked_callback(self):
        line = self.world.get_tiles_in_line((0, 4), (8, 4))
        middle = line[4].position
        self.assertFalse(
            self.world.has_line_of_sight(
                (0, 4), (8, 4), blocked=lambda tile: tile.position == middle
            )
        )

    def test_symmetric_for_straight_row(self):
        line = self.world.get_tiles_in_line((0, 4), (8, 4))
        line[3].is_blocking = True
        self.assertEqual(
            self.world.has_line_of_sight((0, 4), (8, 4)),
            self.world.has_line_of_sight((8, 4), (0, 4)),
        )


class TestPathCost(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_cost_excludes_the_first_tile(self):
        path = self.world.find_path((0, 0), (4, 0))
        self.assertEqual(self.world.get_path_cost(path), 4)

    def test_single_tile_and_empty_path_cost_nothing(self):
        self.assertEqual(self.world.get_path_cost([self.world.get_tile((1, 1))]), 0)
        self.assertEqual(self.world.get_path_cost([]), 0)

    def test_uses_tile_costs_and_custom_function(self):
        self.world.get_tile((1, 0)).cost = 3
        path = [self.world.get_tile((0, 0)), self.world.get_tile((1, 0)),
                self.world.get_tile((2, 0))]
        self.assertEqual(self.world.get_path_cost(path), 4)
        self.assertEqual(self.world.get_path_cost(path, cost=lambda tile: 10), 20)

    def test_matches_find_path_with_max_cost(self):
        self.world.get_tile((2, 0)).cost = 2.5
        path = self.world.find_path((0, 0), (4, 0))
        total = self.world.get_path_cost(path)
        self.assertTrue(self.world.find_path((0, 0), (4, 0), max_cost=total))
        self.assertEqual(self.world.find_path((0, 0), (4, 0), max_cost=total - 0.01), [])

    def test_negative_custom_cost_raises(self):
        path = self.world.find_path((0, 0), (2, 0))
        with self.assertRaises(ValueError):
            self.world.get_path_cost(path, cost=lambda tile: -1)


if __name__ == "__main__":
    unittest.main()
