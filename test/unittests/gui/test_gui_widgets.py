import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, PropertyMock, patch

from miniworlds.actors.widgets import fps as fps_module
from miniworlds.actors.widgets import time as time_module
from miniworlds.actors.widgets.container_widget import ContainerWidget
from miniworlds.actors.widgets.input import Input


class TestFPSLabel(unittest.TestCase):
    def test_module_is_importable(self):
        self.assertTrue(hasattr(fps_module, "FPSLabel"))

    def test_first_update_shows_zero(self):
        widget = fps_module.FPSLabel.__new__(fps_module.FPSLabel)
        widget._base_text = "FPS"
        widget._last_update = None
        widget.value = 0
        widget.set_text = Mock()

        fps_module.FPSLabel.update(widget)

        widget.set_text.assert_called_once_with("FPS : 0")

    def test_update_measures_time_since_last_update(self):
        widget = fps_module.FPSLabel.__new__(fps_module.FPSLabel)
        widget._base_text = "FPS"
        widget._last_update = time.perf_counter() - 0.5
        widget.value = 0
        widget.set_text = Mock()

        fps_module.FPSLabel.update(widget)

        self.assertEqual(widget.value, 2)
        widget.set_text.assert_called_once_with("FPS : 2")


class TestTimeLabel(unittest.TestCase):
    def test_module_is_importable(self):
        self.assertTrue(hasattr(time_module, "TimeLabel"))

    def test_update_shows_observed_world_frame(self):
        widget = time_module.TimeLabel.__new__(time_module.TimeLabel)
        widget._base_text = "Time"
        widget._observed_world = SimpleNamespace(frame=42)
        widget.set_text = Mock()

        time_module.TimeLabel.update(widget)

        widget.set_text.assert_called_once_with("Time : 42")

    def test_update_falls_back_to_own_world(self):
        widget = time_module.TimeLabel.__new__(time_module.TimeLabel)
        widget._base_text = "Time"
        widget._observed_world = None
        widget.set_text = Mock()

        with patch.object(
            time_module.TimeLabel, "world", new_callable=PropertyMock
        ) as world_property:
            world_property.return_value = SimpleNamespace(frame=7)
            time_module.TimeLabel.update(widget)

        widget.set_text.assert_called_once_with("Time : 7")


class TestInputWidget(unittest.TestCase):
    def _make_input(self, current_input="", cursor_position=None, max_chars=10):
        widget = Input.__new__(Input)
        widget.current_input = current_input
        widget._cursor_position = (
            len(current_input) if cursor_position is None else cursor_position
        )
        widget._max_chars = max_chars
        widget.has_focus = Mock(return_value=True)
        widget.set_text = Mock()
        widget.update_cursor = Mock()
        return widget

    def test_text_input_inserts_character_at_cursor(self):
        widget = self._make_input("ab", cursor_position=1)

        Input.on_text_input(widget, "X")

        widget.set_text.assert_called_once_with("aXb")
        self.assertEqual(widget._cursor_position, 2)

    def test_text_input_ignores_input_without_focus(self):
        widget = self._make_input("ab")
        widget.has_focus = Mock(return_value=False)

        Input.on_text_input(widget, "X")

        widget.set_text.assert_not_called()

    def test_text_input_respects_max_chars(self):
        widget = self._make_input("1234567890", max_chars=10)

        Input.on_text_input(widget, "X")

        widget.set_text.assert_not_called()

    def test_key_down_does_not_insert_key_names(self):
        widget = self._make_input("ab")

        Input.on_key_down(widget, ["SPACE"])

        widget.set_text.assert_not_called()

    def test_key_down_backspace_deletes_character(self):
        widget = self._make_input("ab", cursor_position=2)

        Input.on_key_down(widget, ["BACKSPACE"])

        widget.set_text.assert_called_once_with("a")
        self.assertEqual(widget._cursor_position, 1)

    def test_key_down_arrow_moves_cursor(self):
        widget = self._make_input("ab", cursor_position=0)

        Input.on_key_down(widget, ["RIGHT"])

        widget.set_text.assert_not_called()
        self.assertEqual(widget._cursor_position, 1)


class TestContainerWidget(unittest.TestCase):
    def test_get_widget_uses_child_width_consistently(self):
        container = ContainerWidget.__new__(ContainerWidget)
        container._inner_padding = 5
        container.get_local_pos = lambda pos: tuple(pos)
        container.children = [
            SimpleNamespace(width=50),
            SimpleNamespace(width=50),
        ]

        self.assertIs(container.get_widget((60, 5)), container.children[1])
        self.assertIs(container.get_widget((10, 5)), container.children[0])
        self.assertIsNone(container.get_widget((200, 5)))


if __name__ == "__main__":
    unittest.main()
