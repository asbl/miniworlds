from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from miniworlds import Actor
from miniworlds.worlds.world import World


class TestWorldValidation(unittest.TestCase):
    @staticmethod
    def _bare_world() -> World:
        world = World.__new__(World)
        world._runtime_facade = SimpleNamespace(
            run=MagicMock(),
            send_message=MagicMock(),
            switch_world=MagicMock(),
            load_world_from_db=MagicMock(return_value=None),
            load_actors_from_db=MagicMock(return_value=[]),
            save_to_db=MagicMock(),
            quit=MagicMock(),
        )
        world.sensor_manager = SimpleNamespace(
            contains_position=MagicMock(return_value=True),
            contains_rect_all=MagicMock(return_value=True),
            contains_rect_any_=MagicMock(return_value=True),
        )
        return world

    def test_contains_position_rejects_invalid_shape(self):
        world = self._bare_world()

        with self.assertRaises(TypeError) as ctx:
            World.contains_position(world, (1,))

        self.assertIn("pos must be tuple (x, y)", str(ctx.exception))

    def test_contains_rect_rejects_invalid_shape(self):
        world = self._bare_world()

        with self.assertRaises(TypeError) as ctx:
            World.contains_rect(world, (0, 0, 10))

        self.assertIn("rect must be pygame.Rect or tuple", str(ctx.exception))

    def test_size_setter_rejects_invalid_values(self):
        world = self._bare_world()

        with self.assertRaises(TypeError):
            World.size.__set__(world, "800x600")

        with self.assertRaises(ValueError):
            World.size.__set__(world, (800, 0))

    def test_run_rejects_non_boolean_flags(self):
        world = self._bare_world()

        with self.assertRaises(TypeError) as ctx:
            World.run(world, fullscreen=1)

        self.assertIn("fullscreen must be bool", str(ctx.exception))

    def test_send_message_rejects_empty_or_non_string(self):
        world = self._bare_world()

        with self.assertRaises(TypeError):
            World.send_message(world, 123)

        with self.assertRaises(ValueError):
            World.send_message(world, "")

    def test_switch_world_rejects_invalid_inputs(self):
        world = self._bare_world()

        with self.assertRaises(TypeError):
            World.switch_world(world, object())

        new_world = World.__new__(World)
        with self.assertRaises(TypeError):
            World.switch_world(world, new_world, reset="no")

    def test_load_actors_from_db_rejects_invalid_actor_classes(self):
        world = self._bare_world()

        with self.assertRaises(TypeError):
            World.load_actors_from_db(world, "actors.sqlite", actor_classes=WorldValidationActor)

        with self.assertRaises(TypeError):
            World.load_actors_from_db(world, "actors.sqlite", actor_classes=[object])

    def test_distance_to_rejects_invalid_positions(self):
        with self.assertRaises(TypeError):
            World.distance_to((0,), (1, 1))

    def test_debug_toggle_rejects_non_bool(self):
        world = self._bare_world()

        with self.assertRaises(TypeError) as ctx:
            World.debug.__set__(world, "yes")

        self.assertIn("debug must be bool", str(ctx.exception))


class WorldValidationActor(Actor):
    pass


if __name__ == "__main__":
    unittest.main()
