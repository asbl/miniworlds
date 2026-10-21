"""Unit tests for the student-friendly fixes (audit P1-P7).

Covers: run()-exit hint, direction validation and synonyms, event
handler signature checks, setup() typo warning, color validation,
learning-mode warnings, and error message wording.
"""

from __future__ import annotations

import unittest
import warnings

from miniworlds import Actor, Rectangle, World
from miniworlds.base.app import App
from miniworlds.base.exceptions import WrongArgumentsError
from miniworlds.tools import method_caller


class StudentFriendlyFixesTest(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    # P1: run() exit hint

    def test_warn_if_never_run_warns_when_run_not_started(self):
        App._run_started = False
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            App._warn_if_never_run()
        self.assertTrue(any("run() was never called" in str(w.message) for w in caught))

    def test_warn_if_never_run_silent_when_run_started(self):
        App._run_started = True
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                App._warn_if_never_run()
        finally:
            App._run_started = False
        self.assertEqual(caught, [])

    # P2: direction validation and synonyms

    def test_gerian_compass_direction_synonyms(self):
        world = World(100, 100)
        actor = Actor((10, 10), world=world)
        for synonym, canonical in [
            ("nord", "up"),
            ("ost", "right"),
            ("süd", "down"),
            ("west", "left"),
        ]:
            actor.direction = canonical
            expected = actor.direction
            actor.direction = synonym
            self.assertEqual(
                actor.direction,
                expected,
                f"'{synonym}' should behave like '{canonical}'",
            )

    def test_invalid_direction_string_raises_clear_error(self):
        world = World(100, 100)
        actor = Actor((10, 10), world=world)
        with self.assertRaises(TypeError) as ctx:
            actor.direction = "diag"
        self.assertIn("must be a number (degrees)", str(ctx.exception))
        self.assertIn("'up', 'right', 'left', 'down', 'forward'", str(ctx.exception))

    # P3: event handler signature checks

    def test_handler_with_too_few_parameters_raises_wrong_arguments_error(self):
        class Handler:
            def on_key_down(self):
                pass

        with self.assertRaises(WrongArgumentsError):
            method_caller.check_signature(Handler().on_key_down, (["space"],))

    def test_handler_with_correct_parameters_passes_check(self):
        class Handler:
            def on_key_down(self, key):
                pass

        method_caller.check_signature(Handler().on_key_down, (["space"],))

    def test_handler_with_varargs_passes_check(self):
        class Handler:
            def on_key_down(self, *args):
                pass

        method_caller.check_signature(Handler().on_key_down, (["space"], "extra"))

    def test_dispatch_reports_missing_key_parameter(self):
        world = World(100, 100)
        actor = Actor((10, 10), world=world)

        @actor.register
        def on_key_down(self):
            pass

        world.app.event_manager.to_event_queue("key_down", ["space"])
        with self.assertRaises(WrongArgumentsError) as ctx:
            world.app.event_manager.handle_event_queue()
        self.assertIn("def on_key_down(self, key):", str(ctx.exception))

    # P4: setup() typo warning

    def test_setup_typo_warns_with_on_setup_suggestion(self):
        class MyWorld(World):
            def setup(self):
                self.foo = 1

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            MyWorld(50, 50)
        self.assertTrue(
            any(
                "Did you mean 'on_setup'" in str(w.message)
                and "looks like an event handler" in str(w.message)
                for w in caught
            )
        )

    # P5: color validation

    def test_invalid_fill_color_raises_clear_error(self):
        world = World(100, 100)
        actor = Actor((10, 10), world=world)
        with self.assertRaises(ValueError) as ctx:
            actor.costume.fill_color = "notacolor"
        self.assertIn("fill_color must be a color like (255, 0, 0) or 'red'", str(ctx.exception))

    def test_invalid_border_color_raises_clear_error(self):
        world = World(100, 100)
        actor = Actor((10, 10), world=world)
        with self.assertRaises(ValueError) as ctx:
            actor.costume.border_color = "notacolor"
        self.assertIn("border_color must be a color like (255, 0, 0) or 'red'", str(ctx.exception))

    def test_invalid_fill_method_raises_clear_error(self):
        world = World(100, 100)
        rectangle = Rectangle((10, 10), 40, 40, world=world)
        with self.assertRaises(ValueError) as ctx:
            rectangle.costume.fill("notacolor")
        self.assertIn("fill_color must be a color like (255, 0, 0) or 'red'", str(ctx.exception))

    def test_valid_colors_are_accepted(self):
        world = World(100, 100)
        rectangle = Rectangle((10, 10), 40, 40, world=world)
        rectangle.costume.fill_color = "red"
        rectangle.costume.fill_color = (255, 0, 0)
        rectangle.costume.border_color = (0, 255, 0)
        rectangle.costume.fill("blue")
        rectangle.costume.color = "red"
        self.assertEqual(rectangle.costume.fill_color, "red")

    # P6: learning mode warnings

    def test_actor_outside_world_warns_in_learning_mode(self):
        world = World(100, 100)
        world.learning_mode = True
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Actor((500, 500), world=world)
        self.assertTrue(
            any("outside the world" in str(w.message) for w in caught)
        )

    def test_actor_outside_world_is_silent_by_default(self):
        world = World(100, 100)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Actor((500, 500), world=world)
        self.assertFalse(any("outside the world" in str(w.message) for w in caught))

    # P7: error message wording

    def test_actor_without_world_has_clean_message(self):
        try:
            Actor()
        except AttributeError as error:
            self.assertIn("Did you create a world instance", str(error))
        else:
            self.fail("Expected AttributeError")


if __name__ == "__main__":
    unittest.main()
