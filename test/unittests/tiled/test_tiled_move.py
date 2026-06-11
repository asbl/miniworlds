from __future__ import annotations

import unittest

from miniworlds import Actor
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


if __name__ == "__main__":
    unittest.main()
