from __future__ import annotations

import unittest

from miniworlds import Actor, HexWorld
from miniworlds.base.app import App
from miniworlds.worlds.tiled_world.tiled_world import TiledWorld


class TestTiledWorldMove(unittest.TestCase):
    def setUp(self) -> None:
        App.reset(unittest=True, file=__file__)
        self.world = TiledWorld(10, 7)

    def tearDown(self) -> None:
        App.reset(unittest=True, file=__file__)

    def test_move_uses_default_speed_of_one_tile(self):
        actor = Actor((1, 1), world=self.world)
        actor.direction = 90

        actor.move()

        self.assertEqual(actor.position, (2, 1))

    def test_move_updates_direction_when_parameter_is_given(self):
        actor = Actor((1, 1), world=self.world)
        actor.direction = 0

        actor.move(direction=180)

        self.assertEqual(abs(actor.direction), 180)
        self.assertEqual(actor.position, (1, 2))

    def test_move_updates_direction_when_parameter_is_up(self):
        actor = Actor((2, 2), world=self.world)
        actor.direction = 90

        actor.move(direction="up")

        self.assertEqual(actor.direction, 0)
        self.assertEqual(actor.position, (2, 1))

    def test_move_updates_direction_when_parameter_is_zero(self):
        actor = Actor((2, 2), world=self.world)
        actor.direction = 90

        actor.move(direction=0)

        self.assertEqual(actor.direction, 0)
        self.assertEqual(actor.position, (2, 1))

    def test_move_with_explicit_distance_uses_grid_steps(self):
        actor = Actor((4, 4), world=self.world)
        actor.direction = 0

        actor.move(distance=3)

        self.assertEqual(actor.position, (4, 1))

    def test_move_with_negative_distance_moves_backwards(self):
        actor = Actor((3, 3), world=self.world)
        actor.direction = 90

        actor.move(distance=-2)

        self.assertEqual(actor.position, (1, 3))

    def test_undo_move_restores_previous_tile_position(self):
        actor = Actor((5, 5), world=self.world)
        actor.direction = 90

        actor.move(distance=2)
        actor.undo_move()

        self.assertEqual(actor.position, (5, 5))

    def test_blockable_movement_uses_tile_coordinates(self):
        for world_class in (TiledWorld, HexWorld):
            for tile_size in (16, 40, 80):
                with self.subTest(world=world_class.__name__, tile_size=tile_size):
                    world = world_class(5, 5, tile_size=tile_size)
                    player = Actor((1, 1), world=world)
                    player.is_blockable = True
                    wall = Actor((2, 1), world=world)
                    wall.is_blocking = True
                    player.move_in_direction("right")
                    self.assertEqual(player.position, (1, 1))
                    wall.remove()
                    player.move_in_direction("right")
                    self.assertEqual(player.position, (2, 1))

    def test_unrelated_wall_at_origin_does_not_block_free_tiles(self):
        for world_class in (TiledWorld, HexWorld):
            with self.subTest(world=world_class.__name__):
                world = world_class(5, 5, tile_size=40)
                wall = Actor((0, 0), world=world)
                wall.is_blocking = True
                player = Actor((1, 1), world=world)
                player.is_blockable = True
                player.move_in_direction("right")
                self.assertEqual(player.position, (2, 1))

    def test_static_and_dynamic_walls_are_checked_at_grid_positions(self):
        for static in (True, False):
            with self.subTest(static=static):
                wall = Actor((4, 3), world=self.world)
                wall.is_blocking = True
                wall.static = static
                player = Actor((3, 3), world=self.world)
                self.assertIs(player.sensor_manager.get_blocking_actor_at_position((4, 3)), wall)
                self.assertIsNone(player.sensor_manager.get_blocking_actor_at_position((5, 3)))
                self.assertIsNone(player.sensor_manager.get_blocking_actor_at_position(("x", 3)))
                wall.remove()
                player.remove()

    def test_looking_ahead_detects_actors_at_grid_positions(self):
        for world_class in (TiledWorld, HexWorld):
            with self.subTest(world=world_class.__name__):
                world = world_class(5, 5, tile_size=40)
                player = Actor((1, 1), world=world)
                target = Actor((2, 1), world=world)
                unrelated = Actor((0, 0), world=world)
                detected = player.detect_actors_at(direction=90, distance=1)
                self.assertIn(target, detected)
                self.assertNotIn(player, detected)
                self.assertNotIn(unrelated, detected)
                self.assertEqual(player.sensor_manager.get_actors_at_position(("x", 1)), [])


if __name__ == "__main__":
    unittest.main()
