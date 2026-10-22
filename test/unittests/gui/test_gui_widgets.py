import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, PropertyMock, patch

from miniworlds.base.app import App
from miniworlds import World, Toolbar, Button
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
        widget.has_focus = True
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
        widget.has_focus = False

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

    def test_key_down_delete_deletes_character_right_of_cursor(self):
        widget = self._make_input("ab", cursor_position=1)

        Input.on_key_down(widget, ["DELETE"])

        widget.set_text.assert_called_once_with("a")
        self.assertEqual(widget._cursor_position, 1)

    def test_key_down_delete_at_end_does_nothing(self):
        widget = self._make_input("ab", cursor_position=2)

        Input.on_key_down(widget, ["DELETE"])

        widget.set_text.assert_not_called()
        self.assertEqual(widget._cursor_position, 2)

    def test_key_down_arrow_moves_cursor(self):
        widget = self._make_input("ab", cursor_position=0)

        Input.on_key_down(widget, ["RIGHT"])

        widget.set_text.assert_not_called()
        self.assertEqual(widget._cursor_position, 1)

    def test_key_down_ignores_keys_without_focus(self):
        widget = self._make_input("ab", cursor_position=1)
        widget.has_focus = False

        Input.on_key_down(widget, ["BACKSPACE"])

        widget.set_text.assert_not_called()
        self.assertEqual(widget._cursor_position, 1)


class TestInputWidgetIntegration(unittest.TestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_input_can_be_constructed_and_used(self):
        App.reset(unittest=True, file=__file__)
        world = World(400, 300)
        toolbar = Toolbar()
        world.camera.add_right(toolbar, size=200)

        widget = Input((0, 0))
        toolbar.add(widget)

        self.assertEqual(widget.get_text(), "")
        widget.set_text("hello")
        self.assertEqual(widget.get_text(), "hello")
        widget.cursor_position = 2
        self.assertEqual(widget.cursor_position, 2)

    def test_input_receives_text_when_focused(self):
        App.reset(unittest=True, file=__file__)
        world = World(400, 300)
        toolbar = Toolbar()
        world.camera.add_right(toolbar, size=200)
        widget = Input((0, 0))
        toolbar.add(widget)

        widget.has_focus = True
        widget.on_text_input("a")
        widget.on_text_input("b")

        self.assertEqual(widget.get_text(), "ab")
        self.assertEqual(widget.current_input, "ab")

    def test_input_ignores_text_without_focus(self):
        App.reset(unittest=True, file=__file__)
        world = World(400, 300)
        toolbar = Toolbar()
        world.camera.add_right(toolbar, size=200)
        widget = Input((0, 0))
        toolbar.add(widget)

        widget.has_focus = False
        widget.on_text_input("a")

        self.assertEqual(widget.get_text(), "")


class TestTextAlign(unittest.TestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def _make_button(self):
        App.reset(unittest=True, file=__file__)
        world = World(400, 300)
        toolbar = Toolbar()
        world.camera.add_right(toolbar, size=200)
        button = Button("Text")
        toolbar.add(button)
        return button

    def test_default_alignment_is_left(self):
        button = self._make_button()
        self.assertEqual(button.text_align, "left")
        self.assertEqual(button.text.topleft[0], button.topleft[0] + button.padding_left)

    def test_center_alignment_centers_text_in_widget(self):
        button = self._make_button()
        button.text_align = "center"
        text_width = button.text.costume.font_manager.get_text_width("Text")
        expected_x = button.topleft[0] + max(
            button.padding_left, (button.width - text_width) // 2
        )
        self.assertEqual(button.text_align, "center")
        self.assertEqual(button.text.topleft[0], expected_x)

    def test_right_alignment_aligns_text_to_right_edge(self):
        button = self._make_button()
        button.text_align = "right"
        text_width = button.text.costume.font_manager.get_text_width("Text")
        expected_x = button.topleft[0] + button.width - text_width - button.padding_right
        self.assertEqual(button.text_align, "right")
        self.assertEqual(button.text.topleft[0], expected_x)

    def test_invalid_alignment_raises_value_error(self):
        button = self._make_button()
        with self.assertRaises(ValueError):
            button.text_align = "middle"


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

    def test_resize_distributes_integer_width(self):
        container = ContainerWidget.__new__(ContainerWidget)
        container._resize = True
        container._inner_padding = 5
        container._padding_left = 0
        container._padding_right = 0
        container._padding_top = 0
        container._padding_bottom = 0
        container.children = [
            SimpleNamespace(width=0, height=0, x=0, y=0, update_positions=Mock())
            for _ in range(2)
        ]

        with (
            patch("miniworlds.actors.widgets.widget_base.BaseWidget.resize"),
            patch.object(ContainerWidget, "x", new_callable=PropertyMock) as x_mock,
            patch.object(ContainerWidget, "y", new_callable=PropertyMock) as y_mock,
            patch.object(ContainerWidget, "width", new_callable=PropertyMock) as width_mock,
            patch.object(ContainerWidget, "height", new_callable=PropertyMock) as height_mock,
        ):
            x_mock.return_value = 0
            y_mock.return_value = 0
            width_mock.return_value = 101
            height_mock.return_value = 40
            ContainerWidget.resize(container)

        first, second = container.children
        self.assertEqual(first.width, 48)
        self.assertIsInstance(first.width, int)
        self.assertEqual(second.width, 48)
        self.assertIsInstance(second.width, int)
        self.assertEqual(second.x, 48 + 5)


if __name__ == "__main__":
    unittest.main()
