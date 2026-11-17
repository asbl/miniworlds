"""Unit tests for HexWorld game features: adjacency, tile data, path finding, hover."""

from __future__ import annotations

import math
import random
import unittest
from unittest.mock import Mock

from miniworlds import Actor, App
from miniworlds.base.exceptions import DirectionNotFoundError, TileNotFoundError
from miniworlds.worlds.hex_world import hex_coords
from miniworlds.worlds.hex_world.hex_world import HexWorld


def _distance(first, second) -> float:
    return math.hypot(first[0] - second[0], first[1] - second[1])


def _path_cost(path) -> float:
    return sum(tile.cost for tile in path[1:])


class TestCornerEdgeAdjacency(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_interior_corner_has_three_corner_and_three_edge_neighbours(self):
        corner = self.world.get_corner((3, 3), "n")
        self.assertEqual(len(corner.get_neighbour_corners()), 3)
        self.assertEqual(len(corner.get_neighbour_edges()), 3)

    def test_corner_neighbours_are_one_hex_side_away(self):
        corner = self.world.get_corner((3, 3), "n")
        for neighbour in corner.get_neighbour_corners():
            self.assertAlmostEqual(
                _distance(corner.to_pixel(), neighbour.to_pixel()), 40, places=6
            )

    def test_corner_edges_start_at_the_corner(self):
        corner = self.world.get_corner((3, 3), "so")
        for edge in corner.get_neighbour_edges():
            self.assertIn(corner, edge.get_neighbour_corners())
            self.assertAlmostEqual(
                _distance(corner.to_pixel(), edge.to_pixel()), 20, places=6
            )

    def test_edge_has_two_end_corners(self):
        edge = self.world.get_edge((3, 3), "o")
        corners = edge.get_neighbour_corners()
        self.assertEqual(len(corners), 2)
        for corner in corners:
            self.assertAlmostEqual(
                _distance(edge.to_pixel(), corner.to_pixel()), 20, places=6
            )

    def test_edge_end_corners_are_the_corners_of_the_edge_direction(self):
        edge = self.world.get_edge((3, 3), "o")
        expected = {
            self.world.get_corner((3, 3), direction)
            for direction in hex_coords.EDGE_CORNERS["o"]
        }
        self.assertEqual(set(edge.get_neighbour_corners()), expected)

    def test_interior_edge_has_four_edge_neighbours(self):
        edge = self.world.get_edge((3, 3), "o")
        neighbours = edge.get_neighbour_edges()
        self.assertEqual(len(neighbours), 4)
        self.assertNotIn(edge, neighbours)
        for neighbour in neighbours:
            self.assertIn(edge, neighbour.get_neighbour_edges())

    def test_corner_relations_are_symmetric(self):
        for corner in self.world.corners.values():
            for neighbour in corner.get_neighbour_corners():
                self.assertIn(corner, neighbour.get_neighbour_corners())
            for edge in corner.get_neighbour_edges():
                self.assertIn(corner, edge.get_neighbour_corners())

    def test_border_corner_skips_missing_neighbours(self):
        corner = self.world.get_corner((0, 0), "n")
        self.assertLess(len(corner.get_neighbour_corners()), 3)
        self.assertLess(len(corner.get_neighbour_edges()), 3)
        for neighbour in corner.get_neighbour_corners():
            self.assertIn(neighbour, self.world.corners.values())

    def test_every_corner_and_edge_has_at_least_one_relation(self):
        for corner in self.world.corners.values():
            self.assertGreaterEqual(len(corner.get_neighbour_corners()), 2)
            self.assertGreaterEqual(len(corner.get_neighbour_edges()), 2)
        for edge in self.world.edges.values():
            self.assertGreaterEqual(len(edge.get_neighbour_corners()), 1)
            self.assertGreaterEqual(len(edge.get_neighbour_edges()), 2)

    def test_tile_returns_its_six_corners_and_edges(self):
        tile = self.world.get_tile((3, 3))
        corners = tile.get_neighbour_corners()
        edges = tile.get_neighbour_edges()
        self.assertEqual(len(set(corners)), 6)
        self.assertEqual(len(set(edges)), 6)
        for corner in corners:
            self.assertIn(tile, corner.get_neighbour_tiles())
        for edge in edges:
            self.assertIn(tile, edge.get_neighbour_tiles())

    def test_tile_corner_ring_is_connected_by_corner_neighbours(self):
        corners = self.world.get_tile((3, 3)).get_neighbour_corners()
        for index, corner in enumerate(corners):
            following = corners[(index + 1) % 6]
            self.assertIn(following, corner.get_neighbour_corners())


class TestTileData(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(5, 5, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_defaults(self):
        tile = self.world.get_tile((1, 1))
        self.assertEqual(tile.data, {})
        self.assertIsNone(tile.terrain)
        self.assertEqual(tile.cost, 1)
        self.assertFalse(tile.is_blocking)

    def test_data_persists_on_the_tile_object(self):
        self.world.get_tile((1, 1)).data["dice_number"] = 8
        self.assertEqual(self.world.get_tile((1, 1)).data["dice_number"], 8)
        self.assertEqual(self.world.get_tile((2, 1)).data, {})

    def test_terrain_is_stored_in_data(self):
        tile = self.world.get_tile((1, 1))
        tile.terrain = "forest"
        self.assertEqual(tile.data["terrain"], "forest")
        self.assertEqual(tile.terrain, "forest")

    def test_cost_validation(self):
        tile = self.world.get_tile((1, 1))
        tile.cost = 0
        tile.cost = 2.5
        for invalid in (-1, "high", None, True):
            with self.assertRaises(ValueError):
                tile.cost = invalid
        self.assertEqual(tile.cost, 2.5)


class TestPathfinding(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(9, 9, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def _assert_connected(self, path):
        for first, second in zip(path, path[1:]):
            self.assertIn(second, first.get_neighbour_tiles())

    def test_free_path_is_a_shortest_hex_path(self):
        path = self.world.find_path((0, 0), (6, 5))
        distance = hex_coords.cube_distance(
            hex_coords.offset_to_cube((0, 0)), hex_coords.offset_to_cube((6, 5))
        )
        self.assertEqual(len(path), distance + 1)
        self.assertEqual(path[0].position, (0, 0))
        self.assertEqual(path[-1].position, (6, 5))
        self._assert_connected(path)

    def test_start_equals_goal(self):
        path = self.world.find_path((3, 3), (3, 3))
        self.assertEqual([tile.position for tile in path], [(3, 3)])

    def test_accepts_tiles_and_actors(self):
        actor = Actor((1, 1), world=self.world)
        path = self.world.find_path(actor, self.world.get_tile((4, 1)))
        self.assertEqual(path[0].position, (1, 1))
        self.assertEqual(path[-1].position, (4, 1))

    def test_unknown_positions_raise(self):
        with self.assertRaises(TileNotFoundError):
            self.world.find_path((0, 0), (20, 20))

    def test_blocked_tiles_are_walked_around(self):
        blocked = {(2, 2), (3, 2), (2, 3)}
        for position in blocked:
            self.world.get_tile(position).is_blocking = True
        path = self.world.find_path((1, 2), (4, 3))
        self.assertTrue(path)
        self._assert_connected(path)
        self.assertFalse(blocked & {tile.position for tile in path})

    def test_blocking_actor_blocks_its_tile(self):
        direct = [tile.position for tile in self.world.find_path((0, 4), (6, 4))]
        wall = Actor(direct[3], world=self.world)
        wall.is_blocking = True
        path = self.world.find_path((0, 4), (6, 4))
        self.assertTrue(path)
        self.assertNotIn(direct[3], [tile.position for tile in path])

    def test_blocked_goal_or_closed_off_goal_has_no_path(self):
        self.world.get_tile((5, 5)).is_blocking = True
        self.assertEqual(self.world.find_path((0, 0), (5, 5)), [])
        for tile in self.world.get_tiles_in_ring((7, 7), 1):
            tile.is_blocking = True
        self.assertEqual(self.world.find_path((0, 0), (7, 7)), [])

    def test_blocked_start_still_finds_a_path(self):
        self.world.get_tile((0, 0)).is_blocking = True
        self.assertTrue(self.world.find_path((0, 0), (3, 0)))

    def test_cheap_detour_is_preferred_over_expensive_direct_route(self):
        for tile in self.world.tiles.values():
            tile.cost = 1
        for position in [(2, 4), (3, 4), (4, 4)]:
            self.world.get_tile(position).cost = 10
        path = self.world.find_path((1, 4), (5, 4))
        self.assertLessEqual(_path_cost(path), 6)

    def test_max_cost_limits_the_path(self):
        self.assertTrue(self.world.find_path((0, 0), (4, 0), max_cost=4))
        self.assertEqual(self.world.find_path((0, 0), (4, 0), max_cost=3), [])

    def test_custom_blocked_replaces_default_rule(self):
        self.world.get_tile((2, 0)).is_blocking = True
        path = self.world.find_path(
            (0, 0), (4, 0), blocked=lambda tile: tile.position == (1, 0)
        )
        self.assertNotIn((1, 0), [tile.position for tile in path])

    def test_custom_cost_function(self):
        path = self.world.find_path(
            (0, 4), (6, 4), cost=lambda tile: 5 if tile.position[1] == 4 else 1
        )
        self.assertTrue(path)
        self.assertLess(
            sum(5 if tile.position[1] == 4 else 1 for tile in path[1:]), 5 * 6
        )

    def test_negative_custom_cost_raises(self):
        with self.assertRaises(ValueError):
            self.world.find_path((0, 0), (2, 0), cost=lambda tile: -1)

    def test_astar_matches_dijkstra_on_random_costs(self):
        rng = random.Random(7)
        for tile in self.world.tiles.values():
            tile.cost = rng.choice([0.5, 1, 1, 2, 3])
            if rng.random() < 0.1:
                tile.is_blocking = True
        pairs = [((0, 0), (8, 8)), ((0, 8), (8, 0)), ((4, 0), (4, 8)), ((1, 1), (7, 3))]
        for start, goal in pairs:
            if self.world.get_tile(goal).is_blocking:
                continue
            fast = self.world.find_path(start, goal)
            # A custom cost function disables the heuristic: plain Dijkstra.
            exact = self.world.find_path(start, goal, cost=lambda tile: tile.cost)
            self.assertEqual(bool(fast), bool(exact))
            if fast:
                self.assertAlmostEqual(_path_cost(fast), _path_cost(exact))

    def test_reachable_without_obstacles_matches_radius(self):
        reachable = self.world.get_reachable_tiles((4, 4), 2)
        radius = self.world.get_tiles_in_radius((4, 4), 2)
        self.assertEqual({t.position for t in reachable}, {t.position for t in radius})
        self.assertEqual(reachable[0].position, (4, 4))

    def test_reachable_respects_blocked_tiles_and_costs(self):
        for tile in self.world.get_tiles_in_ring((4, 4), 1):
            tile.is_blocking = True
        self.assertEqual(
            [t.position for t in self.world.get_reachable_tiles((4, 4), 3)], [(4, 4)]
        )
        for tile in self.world.get_tiles_in_ring((4, 4), 1):
            tile.is_blocking = False
            tile.cost = 2
        reachable = self.world.get_reachable_tiles((4, 4), 2)
        self.assertEqual(len(reachable), 7)

    def test_reachable_is_ordered_by_cost(self):
        costs = {}
        reachable = self.world.get_reachable_tiles((4, 4), 3)
        for tile in reachable:
            costs[tile.position] = hex_coords.cube_distance(
                hex_coords.offset_to_cube((4, 4)), hex_coords.offset_to_cube(tile.position)
            )
        ordered = [costs[tile.position] for tile in reachable]
        self.assertEqual(ordered, sorted(ordered))


class TestHighlightsAndHover(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 7, tile_size=40)
        self.world.camera.is_in_screen = Mock(return_value=True)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def _pixel_at(self, position):
        center = self.world.get_tile(position).to_center()
        return tuple(self.world.background.image.get_at((int(center[0]), int(center[1]))))[:3]

    def test_highlight_changes_the_background_pixels(self):
        before = self._pixel_at((3, 3))
        self.world.get_tile((3, 3)).highlight((255, 0, 0, 255))
        self.assertEqual(self._pixel_at((3, 3)), (255, 0, 0))
        self.assertNotEqual(before, (255, 0, 0))
        self.assertEqual(self._pixel_at((1, 1)), before)

    def test_clear_highlight_restores_the_background(self):
        before = self._pixel_at((3, 3))
        tile = self.world.get_tile((3, 3))
        tile.highlight((255, 0, 0, 255))
        self.assertTrue(tile.is_highlighted)
        tile.clear_highlight()
        self.assertFalse(tile.is_highlighted)
        self.assertEqual(self._pixel_at((3, 3)), before)

    def test_translucent_highlight_blends_with_the_background(self):
        before = self._pixel_at((3, 3))
        self.world.get_tile((3, 3)).highlight((0, 0, 0, 128))
        after = self._pixel_at((3, 3))
        self.assertLess(sum(after), sum(before))
        self.assertGreater(sum(after), 0)

    def test_highlight_follows_a_scrolled_camera(self):
        world = HexWorld(20, 16, tile_size=40)
        world.camera._strict = False
        world.camera.width = 8
        world.camera.height = 6
        world.camera.topleft = (5, 4)
        tile = world.get_tile((7, 5))
        tile.highlight((255, 0, 0, 255))
        center = tile.to_center()
        topleft = world.camera.topleft
        local = (int(center[0] - topleft[0]), int(center[1] - topleft[1]))
        self.assertEqual(tuple(world.background.image.get_at(local))[:3], (255, 0, 0))

    def test_highlight_tiles_and_clear_all(self):
        tiles = self.world.get_tiles_in_radius((3, 3), 1)
        self.world.highlight_tiles(tiles, (255, 0, 0))
        self.assertTrue(all(tile.is_highlighted for tile in tiles))
        self.world.clear_highlights()
        self.assertFalse(any(tile.is_highlighted for tile in tiles))

    def test_invalid_highlight_color_raises(self):
        with self.assertRaises(ValueError):
            self.world.get_tile((3, 3)).highlight((1, 2))

    def test_tile_events_fire_when_the_hovered_tile_changes(self):
        events = []

        @self.world.register
        def on_tile_enter(self, tile):
            events.append(("enter", tile.position))

        @self.world.register
        def on_tile_leave(self, tile):
            events.append(("leave", tile.position))

        handler = self.world.event_manager.handler
        first = self.world.get_tile((1, 1)).to_center()
        second = self.world.get_tile((4, 4)).to_center()

        handler.handle_event("mouse_motion", first)
        handler.executed_events.clear()
        handler.handle_event("mouse_motion", first)  # same tile: no event
        handler.executed_events.clear()
        handler.handle_event("mouse_motion", second)

        self.assertEqual(
            events,
            [("enter", (1, 1)), ("leave", (1, 1)), ("enter", (4, 4))],
        )
        self.assertEqual(self.world.hovered_tile.position, (4, 4))

    def test_leaving_the_world_fires_tile_leave(self):
        events = []

        @self.world.register
        def on_tile_leave(self, tile):
            events.append(tile.position)

        handler = self.world.event_manager.handler
        handler.handle_event("mouse_motion", self.world.get_tile((2, 2)).to_center())
        handler.executed_events.clear()
        self.world.camera.is_in_screen = Mock(return_value=False)
        handler.handle_event("mouse_motion", (9999, 9999))

        self.assertEqual(events, [(2, 2)])
        self.assertIsNone(self.world.hovered_tile)

    def test_hover_highlight_pattern(self):
        @self.world.register
        def on_tile_enter(self, tile):
            tile.highlight((255, 0, 0, 255))

        @self.world.register
        def on_tile_leave(self, tile):
            tile.clear_highlight()

        handler = self.world.event_manager.handler
        handler.handle_event("mouse_motion", self.world.get_tile((3, 3)).to_center())
        self.assertTrue(self.world.get_tile((3, 3)).is_highlighted)
        handler.executed_events.clear()
        handler.handle_event("mouse_motion", self.world.get_tile((1, 1)).to_center())
        self.assertFalse(self.world.get_tile((3, 3)).is_highlighted)
        self.assertTrue(self.world.get_tile((1, 1)).is_highlighted)


if __name__ == "__main__":
    unittest.main()


class TestRadiusAndRingQueries(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = HexWorld(7, 6, tile_size=40)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def _cube_distance(self, first, second) -> int:
        return hex_coords.cube_distance(
            hex_coords.offset_to_cube(first), hex_coords.offset_to_cube(second)
        )

    def test_radius_equals_all_tiles_within_distance_for_every_center(self):
        for center in self.world.tiles:
            for radius in range(0, 5):
                expected = {
                    position
                    for position in self.world.tiles
                    if self._cube_distance(center, position) <= radius
                }
                found = self.world.get_tiles_in_radius(center, radius)
                assert {tile.position for tile in found} == expected
                assert len(found) == len(expected)

    def test_ring_equals_all_tiles_at_exact_distance_for_every_center(self):
        for center in self.world.tiles:
            for radius in range(0, 5):
                expected = {
                    position
                    for position in self.world.tiles
                    if self._cube_distance(center, position) == radius
                }
                found = self.world.get_tiles_in_ring(center, radius)
                assert {tile.position for tile in found} == expected
                assert len(found) == len(expected)

    def test_radius_starts_with_the_center(self):
        assert self.world.get_tiles_in_radius((3, 2), 2)[0].position == (3, 2)

    def test_center_outside_the_world_still_finds_inner_tiles(self):
        # (-1, 1) lies in an odd row: its eastern neighbours are column 0.
        found = self.world.get_tiles_in_radius((-1, 1), 1)
        assert {tile.position for tile in found} == {(0, 0), (0, 1), (0, 2)}
        # (-1, 0) lies in an even row: only (0, 0) is adjacent.
        found = self.world.get_tiles_in_radius((-1, 0), 1)
        assert {tile.position for tile in found} == {(0, 0)}

    def test_huge_radius_returns_the_whole_world_quickly(self):
        assert len(self.world.get_tiles_in_radius((3, 2), 10**9)) == 7 * 6
        assert self.world.get_tiles_in_ring((3, 2), 10**9) == []

    def test_negative_radius_returns_nothing(self):
        assert self.world.get_tiles_in_radius((3, 2), -1) == []
        assert self.world.get_tiles_in_ring((3, 2), -1) == []

    def test_neighbour_queries_return_independent_lists(self):
        corner = self.world.get_corner((3, 3), "n")
        edges = self.world.get_edge((3, 3), "o").get_neighbour_edges()
        edges.clear()
        corner.get_neighbour_corners().clear()
        assert len(self.world.get_edge((3, 3), "o").get_neighbour_edges()) == 4
        assert len(corner.get_neighbour_corners()) == 3
        assert len(self.world.get_tile((3, 3)).get_neighbour_edges()) == 6

    def test_cached_neighbours_follow_structure_changes(self):
        tile = self.world.get_tile((3, 3))
        assert len(tile.get_neighbour_edges()) == 6
        edge = self.world.get_edge((3, 3), "o")
        assert len(edge.get_neighbour_corners()) == 2
        del self.world.corners[edge.get_neighbour_corners()[0].position]
        self.world._tile_structure_version += 1
        assert len(edge.get_neighbour_corners()) == 1

    def test_include_center_false_leaves_out_the_center(self):
        found = self.world.get_tiles_in_radius((3, 2), 1, include_center=False)
        assert (3, 2) not in [tile.position for tile in found]
        assert len(found) == 6
        outside = self.world.get_tiles_in_radius((-1, 1), 1, include_center=False)
        assert {tile.position for tile in outside} == {(0, 0), (0, 1), (0, 2)}

    def test_position_can_be_a_tile_or_an_actor(self):
        actor = Actor((3, 2))
        by_tuple = self.world.get_tiles_in_radius((3, 2), 2)
        assert self.world.get_tiles_in_radius(actor, 2) == by_tuple
        assert self.world.get_tiles_in_radius(self.world.get_tile((3, 2)), 2) == by_tuple
        assert self.world.get_tiles_in_ring(actor, 1) == self.world.get_tiles_in_ring((3, 2), 1)

    def test_invalid_arguments_raise_helpful_type_errors(self):
        for radius in (1.5, "2", None, True):
            with self.assertRaises(TypeError):
                self.world.get_tiles_in_radius((3, 2), radius)
            with self.assertRaises(TypeError):
                self.world.get_tiles_in_ring((3, 2), radius)
        with self.assertRaises(TypeError):
            self.world.get_tiles_in_radius("center", 1)

    def test_get_distance_is_the_hex_distance(self):
        assert self.world.get_distance((0, 0), (0, 0)) == 0
        assert self.world.get_distance((2, 2), (3, 2)) == 1
        assert self.world.get_distance(Actor((0, 0)), self.world.get_tile((6, 0))) == 6
        for center in self.world.tiles:
            for tile in self.world.tiles.values():
                assert self.world.get_distance(center, tile) == self._cube_distance(
                    center, tile.position
                )

    def test_tile_distance_to_uses_hex_distance_not_offset_euclid(self):
        first = self.world.get_tile((0, 1))
        second = self.world.get_tile((1, 0))
        # Offset coordinates differ diagonally, but the hexes are adjacent.
        assert first.distance_to(second) == 1
        assert first.get_distance_to((3, 3)) == self.world.get_distance((0, 1), (3, 3))

    def test_tile_radius_and_ring_helpers(self):
        tile = self.world.get_tile((3, 2))
        assert set(tile.get_tiles_in_radius(1)) == set(tile.get_neighbour_tiles())
        assert len(tile.get_tiles_in_radius(1)) == 6
        assert tile.get_tiles_in_radius(1, include_center=True)[0] is tile
        assert tile.get_tiles_in_ring(2) == self.world.get_tiles_in_ring((3, 2), 2)

    def test_get_neighbour_by_direction(self):
        tile = self.world.get_tile((3, 3))   # odd row
        assert tile.get_neighbour("o").position == (4, 3)
        assert tile.get_neighbour("w").position == (2, 3)
        assert tile.get_neighbour("no").position == (4, 2)
        assert tile.get_neighbour("nw").position == (3, 2)
        assert tile.get_neighbour("so").position == (4, 4)
        assert tile.get_neighbour("sw").position == (3, 4)
        even = self.world.get_tile((3, 2))
        assert even.get_neighbour("no").position == (3, 1)
        assert even.get_neighbour("sw").position == (2, 3)
        assert self.world.get_tile((0, 0)).get_neighbour("w") is None
        assert self.world.get_tile((0, 0)).get_neighbour("nw") is None
        with self.assertRaises(DirectionNotFoundError):
            tile.get_neighbour("north")

    def test_get_neighbour_tiles_returns_a_copy(self):
        tile = self.world.get_tile((3, 3))
        tile.get_neighbour_tiles().clear()
        assert len(tile.get_neighbour_tiles()) == 6
        assert len(self.world.find_path((0, 0), (6, 5))) > 0

    def test_tiles_in_line(self):
        line = self.world.get_tiles_in_line((0, 0), (6, 0))
        assert [tile.position for tile in line] == [(column, 0) for column in range(7)]
        line = self.world.get_tiles_in_line(Actor((1, 1)), (5, 4))
        assert len(line) == self._cube_distance((1, 1), (5, 4)) + 1
        for first, second in zip(line, line[1:]):
            assert self._cube_distance(first.position, second.position) == 1
        assert self.world.get_tiles_in_line((3, 3), (3, 3)) == [self.world.get_tile((3, 3))]

    def test_line_of_sight_with_blocking_tile(self):
        self.world.get_tile((3, 0)).is_blocking = True
        line = self.world.get_tiles_in_line((0, 0), (6, 0))
        assert any(tile.is_blocking for tile in line)
        clear = self.world.get_tiles_in_line((0, 3), (6, 3))
        assert not any(tile.is_blocking for tile in clear)
