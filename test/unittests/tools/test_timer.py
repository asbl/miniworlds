import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from miniworlds.tools.timer import ActionTimer, LoopActionTimer, Timer, loop, timer


class CountingTimer(Timer):
    def __init__(self, time):
        self.act_calls = []
        super().__init__(time)

    def act(self):
        self.act_calls.append(self.actual_time)


class TestTimer(unittest.TestCase):
    def _create_world(self):
        return SimpleNamespace(_timed_objects=[])

    def test_timer_registers_itself_on_running_world(self):
        world = self._create_world()

        with patch("miniworlds.base.app.App.get_running_world", return_value=world):
            timer_instance = Timer(3)

        self.assertIn(timer_instance, world._timed_objects)

    def test_timer_tick_calls_act_at_requested_interval(self):
        world = self._create_world()

        with patch("miniworlds.base.app.App.get_running_world", return_value=world):
            timer_instance = CountingTimer(2)

        for _ in range(5):
            timer_instance.tick()

        self.assertEqual(timer_instance.act_calls, [2, 4])

    def test_unregister_removes_timer_from_world(self):
        world = self._create_world()

        with patch("miniworlds.base.app.App.get_running_world", return_value=world):
            timer_instance = Timer(4)

        timer_instance.unregister()

        self.assertNotIn(timer_instance, world._timed_objects)

    def test_action_timer_calls_method_and_unregisters(self):
        world = self._create_world()
        values = []

        def record(value):
            values.append(value)

        with patch("miniworlds.base.app.App.get_running_world", return_value=world):
            timer_instance = ActionTimer(2, record, arguments="payload")

        timer_instance.tick()
        timer_instance.tick()

        self.assertEqual(values, ["payload"])
        self.assertNotIn(timer_instance, world._timed_objects)

    def test_action_timer_accepts_zero_as_valid_argument(self):
        world = self._create_world()
        values = []

        def record(value):
            values.append(value)

        with patch("miniworlds.base.app.App.get_running_world", return_value=world):
            timer_instance = ActionTimer(1, record, arguments=0)

        timer_instance.tick()

        self.assertEqual(values, [0])

    def test_loop_action_timer_stays_registered_after_trigger(self):
        world = self._create_world()
        calls = []

        def record():
            calls.append("tick")

        with patch("miniworlds.base.app.App.get_running_world", return_value=world):
            timer_instance = LoopActionTimer(2, record)

        timer_instance.tick()
        timer_instance.tick()

        self.assertEqual(calls, ["tick"])
        self.assertIn(timer_instance, world._timed_objects)

    def test_timer_decorator_creates_one_shot_action_timer(self):
        world = self._create_world()
        calls = []

        with patch("miniworlds.base.app.App.get_running_world", return_value=world):
            decorated_timer = timer(frames=2)(lambda: calls.append("done"))

        decorated_timer.tick()
        decorated_timer.tick()

        self.assertEqual(calls, ["done"])
        self.assertNotIn(decorated_timer, world._timed_objects)

    def test_loop_decorator_creates_repeating_timer(self):
        world = self._create_world()
        calls = []

        with patch("miniworlds.base.app.App.get_running_world", return_value=world):
            decorated_timer = loop(frames=2)(lambda: calls.append("tick"))

        for _ in range(4):
            decorated_timer.tick()

        self.assertEqual(calls, ["tick", "tick"])
        self.assertIn(decorated_timer, world._timed_objects)

    def test_timer_rejects_non_positive_interval(self):
        with self.assertRaises(ValueError):
            Timer(0)
        with self.assertRaises(ValueError):
            Timer(-1)

    def test_timer_rejects_non_integer_interval(self):
        with self.assertRaises(TypeError):
            Timer(1.5)


class TestNotImplementedOrRegisteredError(unittest.TestCase):
    def test_exception_message_is_propagated_to_super(self):
        """Regression: __init__ previously set self.message but never called super(),
        so str(exc) showed the raw method object rather than the intended message."""
        from miniworlds.base.exceptions import NotImplementedOrRegisteredError

        exc = NotImplementedOrRegisteredError("my_method")
        self.assertIn("my_method", str(exc))
        self.assertIn("not overwritten or registered", str(exc))