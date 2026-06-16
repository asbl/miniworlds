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
        world._learning_mode = False
        world._runtime_facade = SimpleNamespace(
            run=MagicMock(),
            send_message=MagicMock(),
            switch_world=MagicMock(),
            quit=MagicMock(),
            is_in_world=MagicMock(return_value=True),
            detect_actors=MagicMock(return_value=[]),
            get_actors_from_pixel=MagicMock(return_value=[]),
            get_from_pixel=MagicMock(return_value=(1, 2)),
            to_pixel=MagicMock(return_value=(1, 2)),
        )
        world.sensor_manager = SimpleNamespace(
            contains_position=MagicMock(return_value=True),
            contains_rect_all=MagicMock(return_value=True),
            contains_rect_any_=MagicMock(return_value=True),
        )
        world.camera = SimpleNamespace(
            width=100,
            height=80,
            world_size_x=100,
            world_size_y=80,
        )
        world._background_facade = SimpleNamespace(
            switch_background=MagicMock(),
            remove_background=MagicMock(),
        )
        return world

    def test_contains_position_rejects_invalid_shape(self):
        world = self._bare_world()

        with self.assertRaises(TypeError) as ctx:
            World.contains_position(world, (1,))

        self.assertIn("pos must be a tuple (x, y)", str(ctx.exception))

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

    def test_dimension_setters_update_camera_runtime_values(self):
        world = self._bare_world()

        World.world_size_x.__set__(world, 200)
        World.world_size_y.__set__(world, 150)
        World.columns.__set__(world, 120)
        World.rows.__set__(world, 90)

        self.assertEqual(world.camera.world_size_x, 120)
        self.assertEqual(world.camera.world_size_y, 90)
        self.assertEqual(world.camera.width, 120)
        self.assertEqual(world.camera.height, 90)

    def test_dimension_setters_reject_invalid_runtime_values(self):
        world = self._bare_world()
        world.app = SimpleNamespace(
            platform=SimpleNamespace(is_web=MagicMock(return_value=False))
        )

        for setter in (
            World.fps,
            World.tick_rate,
            World.world_size_x,
            World.world_size_y,
            World.columns,
            World.rows,
        ):
            with self.assertRaises(TypeError):
                setter.__set__(world, True)
            with self.assertRaises(TypeError):
                setter.__set__(world, "10")
            with self.assertRaises(ValueError):
                setter.__set__(world, 0)

    def test_size_setter_accepts_learning_mode_list_and_rejects_bool_components(self):
        world = self._bare_world()
        world.learning_mode = True

        World.size.__set__(world, [320, 200])

        self.assertEqual(world.size, (320, 200))

        with self.assertRaises(TypeError):
            World.size.__set__(world, (320, True))

    def test_fps_setter_clamps_web_runtime_to_sixty_fps(self):
        world = self._bare_world()
        world.app = SimpleNamespace(platform=SimpleNamespace(is_web=MagicMock(return_value=True)))

        World.fps.__set__(world, 120)

        self.assertEqual(world.fps, 60)

    def test_fps_setter_keeps_high_native_fps(self):
        world = self._bare_world()
        world.app = SimpleNamespace(platform=SimpleNamespace(is_web=MagicMock(return_value=False)))

        World.fps.__set__(world, 120)

        self.assertEqual(world.fps, 120)

    def test_run_rejects_non_boolean_flags(self):
        world = self._bare_world()

        with self.assertRaises(TypeError) as ctx:
            World.run(world, fullscreen=1)

        self.assertIn("fullscreen must be bool", str(ctx.exception))

    def test_run_converts_boolean_like_values_in_learning_mode(self):
        world = self._bare_world()
        world.learning_mode = True

        World.run(world, fullscreen="yes", fit_desktop="no", replit="1")

        world._runtime_facade.run.assert_called_once_with(
            fullscreen=True,
            fit_desktop=False,
            replit=True,
            event=None,
            data=None,
        )

    def test_learning_mode_rejects_non_bool(self):
        world = self._bare_world()

        with self.assertRaises(TypeError) as ctx:
            World.learning_mode.__set__(world, "yes")

        self.assertIn("learning_mode must be bool", str(ctx.exception))

    def test_send_message_rejects_empty_or_non_string(self):
        world = self._bare_world()

        with self.assertRaises(TypeError):
            World.send_message(world, 123)

        with self.assertRaises(ValueError):
            World.send_message(world, "")

    def test_send_message_converts_to_string_in_learning_mode(self):
        world = self._bare_world()
        world.learning_mode = True

        World.send_message(world, 42)

        world._runtime_facade.send_message.assert_called_once_with("42", None)

    def test_contains_position_accepts_list_in_learning_mode(self):
        world = self._bare_world()
        world.learning_mode = True

        result = World.contains_position(world, [10, 20])

        world.sensor_manager.contains_position.assert_called_once_with((10, 20))
        self.assertTrue(result)

    def test_beginner_aliases_delegate_to_existing_methods(self):
        world = self._bare_world()
        world.contains_position = MagicMock(return_value=True)
        world.send_message = MagicMock(return_value=None)
        world.detect_actors = MagicMock(return_value=["actor"])

        self.assertTrue(World.contains(world, (1, 2)))
        world.contains_position.assert_called_once_with((1, 2))

        World.broadcast(world, "hello")
        world.send_message.assert_called_once_with("hello", None)

        self.assertEqual(World.actors_at(world, (3, 4)), ["actor"])
        world.detect_actors.assert_called_once_with((3, 4))

    def test_switch_world_rejects_invalid_inputs(self):
        world = self._bare_world()

        with self.assertRaises(TypeError):
            World.switch_world(world, object())

        new_world = World.__new__(World)
        with self.assertRaises(TypeError):
            World.switch_world(world, new_world, reset="no")

    def test_distance_to_rejects_invalid_positions(self):
        with self.assertRaises(TypeError):
            World.distance_to((0,), (1, 1))

    def test_debug_toggle_rejects_non_bool(self):
        world = self._bare_world()

        with self.assertRaises(TypeError) as ctx:
            World.debug.__set__(world, "yes")

        self.assertIn("debug must be bool", str(ctx.exception))

    def test_background_selection_rejects_bool_index(self):
        world = self._bare_world()

        with self.assertRaises(TypeError):
            World.switch_background(world, True)

        with self.assertRaises(TypeError):
            World.remove_background(world, False)

        world._background_facade.switch_background.assert_not_called()
        world._background_facade.remove_background.assert_not_called()

    def test_world_constructor_accepts_size_tuple(self):
        world = World((120, 80))

        self.assertEqual(world.size, (120, 80))

    def test_world_constructor_rejects_invalid_size_tuple(self):
        with self.assertRaises(TypeError) as ctx:
            World((120,))

        self.assertIn("x must be tuple (width, height)", str(ctx.exception))

    def test_world_constructor_rejects_tuple_with_second_dimension(self):
        with self.assertRaises(TypeError) as ctx:
            World((120, 80), 90)

        self.assertIn("cannot be combined", str(ctx.exception))


class WorldValidationActor(Actor):
    pass


if __name__ == "__main__":
    unittest.main()
