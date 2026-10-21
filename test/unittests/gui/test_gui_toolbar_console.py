import unittest
from collections import OrderedDict
from types import SimpleNamespace
from unittest.mock import Mock, patch

from miniworlds.actors.widgets import widget_base
from miniworlds.worlds.gui.console import Console
from miniworlds.worlds.gui.toolbar import Toolbar


class DummyWidget(widget_base.BaseWidget):
    def __init__(self):
        pass


class LayoutWidget:
    def __init__(self, margin_top, margin_left, margin_right, margin_bottom, height):
        self.margin_top = margin_top
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom
        self.height = height
        self.width = None
        self.topleft = None


class TestToolbar(unittest.TestCase):
    def test_set_widget_width_respects_padding_and_margins(self):
        toolbar = Toolbar.__new__(Toolbar)
        toolbar.camera = SimpleNamespace(width=200)
        toolbar._padding_left = 20
        toolbar._padding_right = 10
        widget = SimpleNamespace(margin_left=5, margin_right=15, width=None)

        Toolbar._set_widget_width(toolbar, widget)

        self.assertEqual(widget.width, 150)

    def test_reorder_positions_widgets_vertically(self):
        toolbar = Toolbar.__new__(Toolbar)
        toolbar.camera = SimpleNamespace(width=200)
        toolbar._padding_top = 10
        toolbar._padding_left = 20
        toolbar._padding_right = 10
        toolbar.max_row_height = 0
        first = LayoutWidget(margin_top=3, margin_left=5, margin_right=15, margin_bottom=7, height=30)
        second = LayoutWidget(margin_top=4, margin_left=10, margin_right=5, margin_bottom=6, height=40)
        toolbar.widgets = OrderedDict([(0, first), (1, second)])

        Toolbar.reorder(toolbar)

        self.assertEqual(first.width, 150)
        self.assertEqual(first.topleft, (25, 13))
        self.assertEqual(second.width, 155)
        self.assertEqual(second.topleft, (30, 54))

    def test_remove_widget_by_instance_uses_matched_key(self):
        toolbar = Toolbar.__new__(Toolbar)
        first = object.__new__(DummyWidget)
        second = object.__new__(DummyWidget)
        first.remove = Mock()
        second.remove = Mock()
        toolbar.widgets = OrderedDict([(0, first), (1, second)])
        toolbar.timed_widgets = {}

        with patch.object(Toolbar, "reorder") as reorder_mock:
            Toolbar.remove(toolbar, first)

        self.assertNotIn(0, toolbar.widgets)
        self.assertIn(1, toolbar.widgets)
        first.remove.assert_called_once_with()
        second.remove.assert_not_called()
        reorder_mock.assert_called_once_with()


class TestConsole(unittest.TestCase):
    def test_newline_adds_label_and_returns_it(self):
        console = Console.__new__(Console)
        fake_label = object()
        console.add = Mock(side_effect=lambda widget: widget)

        with patch("miniworlds.worlds.gui.console.label.Label", return_value=fake_label) as label_mock:
            result = Console.newline(console, "hello")

        label_mock.assert_called_once_with("hello")
        console.add.assert_called_once_with(fake_label)
        self.assertIs(result, fake_label)

    def test_add_widget_applies_console_spacing(self):
        console = Console.__new__(Console)
        console.row_margin = 7
        console.max_lines = 2
        console.widgets = OrderedDict()
        console.timed_widgets = {}
        widget = Mock()

        with patch(
            "miniworlds.worlds.gui.console.toolbar.Toolbar._add_widget",
            return_value=widget,
        ) as add_widget_mock:
            result = Console._add_widget(console, widget)

        self.assertIs(result, widget)
        self.assertEqual(widget.margin_top, 0)
        self.assertEqual(widget.margin_bottom, 7)
        add_widget_mock.assert_called_once_with(widget, None)


class TestToolbarWidgetKeys(unittest.TestCase):
    def _make_toolbar(self):
        toolbar = Toolbar.__new__(Toolbar)
        toolbar.widgets = OrderedDict()
        toolbar.timed_widgets = {}
        toolbar.fixed_camera = True
        toolbar._padding_top = 0
        toolbar._padding_left = 0
        toolbar._padding_right = 0
        toolbar.max_row_height = 0
        toolbar.row_height = 20
        toolbar.camera = SimpleNamespace(width=200, y=0, height=100, world_size_y=100)
        return toolbar

    def _make_widget(self, timed=False):
        widget = LayoutWidget(0, 0, 0, 0, 20)
        widget.timed = timed
        return widget

    def test_add_widget_honors_custom_key(self):
        toolbar = self._make_toolbar()
        widget = self._make_widget()

        toolbar._add_widget(widget, key="start")

        self.assertIs(toolbar.widgets["start"], widget)
        self.assertTrue(toolbar.has_widget("start"))
        self.assertIs(toolbar.get_widget("start"), widget)

    def test_add_widget_auto_key_is_int_and_increments(self):
        toolbar = self._make_toolbar()
        first = self._make_widget()
        second = self._make_widget()

        toolbar._add_widget(first)
        toolbar._add_widget(second)

        self.assertEqual(list(toolbar.widgets.keys()), [0, 1])

    def test_add_widget_auto_key_works_with_string_keys_present(self):
        toolbar = self._make_toolbar()
        named = self._make_widget()
        auto = self._make_widget()

        toolbar._add_widget(named, key="start")
        toolbar._add_widget(auto)

        self.assertIs(toolbar.widgets["start"], named)
        self.assertIs(toolbar.widgets[0], auto)

    def test_add_widget_replaces_existing_key_and_removes_old_widget(self):
        toolbar = self._make_toolbar()
        old_widget = self._make_widget()
        old_widget.remove = Mock()
        new_widget = self._make_widget()

        toolbar._add_widget(old_widget, key="start")
        toolbar._add_widget(new_widget, key="start")

        self.assertIs(toolbar.widgets["start"], new_widget)
        old_widget.remove.assert_called_once_with()

    def test_get_widget_raises_keyerror_for_missing_key(self):
        toolbar = self._make_toolbar()

        with self.assertRaises(KeyError):
            toolbar.get_widget("missing")

    def test_remove_unknown_widget_returns_false(self):
        toolbar = self._make_toolbar()
        stranger = object.__new__(DummyWidget)

        self.assertFalse(toolbar.remove(stranger))

    def test_timed_widget_is_registered_by_id(self):
        toolbar = self._make_toolbar()
        widget = self._make_widget(timed=True)

        toolbar._add_widget(widget)

        self.assertIs(toolbar.timed_widgets[id(widget)], widget)

    def test_remove_by_key_removes_widget_from_world(self):
        toolbar = self._make_toolbar()
        widget = self._make_widget(timed=True)
        widget.remove = Mock()
        toolbar._add_widget(widget)

        Toolbar.remove(toolbar, 0)

        self.assertNotIn(0, toolbar.widgets)
        self.assertNotIn(id(widget), toolbar.timed_widgets)
        widget.remove.assert_called_once_with()

    def test_remove_by_key_reorders_remaining_widgets(self):
        toolbar = self._make_toolbar()
        first = self._make_widget()
        second = self._make_widget()
        first.remove = Mock()
        second.remove = Mock()
        toolbar._add_widget(first)
        toolbar._add_widget(second)
        first_topleft = first.topleft

        Toolbar.remove(toolbar, 0)

        self.assertEqual(list(toolbar.widgets.keys()), [1])
        self.assertEqual(second.topleft, first_topleft)

    def test_remove_by_missing_key_returns_false(self):
        toolbar = self._make_toolbar()

        self.assertFalse(Toolbar.remove(toolbar, "missing"))

    def test_on_remove_actor_removes_widget_from_toolbar(self):
        toolbar = self._make_toolbar()
        widget = object.__new__(DummyWidget)
        widget.timed = True
        widget.remove = Mock()

        with patch.object(Toolbar, "reorder"):
            toolbar._add_widget(widget)
            Toolbar.on_remove_actor(toolbar, widget)

        self.assertNotIn(0, toolbar.widgets)
        self.assertNotIn(id(widget), toolbar.timed_widgets)

    def test_on_remove_actor_ignores_unknown_actor(self):
        toolbar = self._make_toolbar()
        widget = object.__new__(DummyWidget)
        widget.timed = False
        widget.remove = Mock()
        unknown = object.__new__(DummyWidget)

        with patch.object(Toolbar, "reorder"):
            toolbar._add_widget(widget)
            Toolbar.on_remove_actor(toolbar, unknown)

        self.assertIn(0, toolbar.widgets)

    def test_remove_all_widgets_removes_every_actor(self):
        toolbar = self._make_toolbar()
        first = self._make_widget(timed=True)
        second = self._make_widget()
        first.remove = Mock()
        second.remove = Mock()
        toolbar._add_widget(first)
        toolbar._add_widget(second)

        toolbar.remove_all_widgets()

        self.assertEqual(len(toolbar.widgets), 0)
        self.assertEqual(len(toolbar.timed_widgets), 0)
        first.remove.assert_called_once_with()
        second.remove.assert_called_once_with()


class TestConsoleTrimming(unittest.TestCase):
    def _make_console(self, max_lines=2):
        console = Console.__new__(Console)
        console.max_lines = max_lines
        console.row_margin = 5
        console.widgets = OrderedDict()
        console.timed_widgets = {}
        console.fixed_camera = True
        console._padding_top = 0
        console._padding_left = 0
        console._padding_right = 0
        console.max_row_height = 0
        console.row_height = 20
        console.camera = SimpleNamespace(width=200, y=0, height=50, world_size_y=50)
        return console

    def _add_line(self, console, name):
        widget = LayoutWidget(0, 0, 0, 5, 20)
        widget.name = name
        widget.remove = Mock()
        widget.timed = False
        console.widgets[len(console.widgets)] = widget
        return widget

    def test_old_lines_are_trimmed_to_max_lines(self):
        console = self._make_console(max_lines=2)
        first = self._add_line(console, "first")
        second = self._add_line(console, "second")
        third = self._add_line(console, "third")

        console._trim_old_lines()

        self.assertEqual(list(console.widgets.values()), [second, third])
        first.remove.assert_called_once_with()
        second.remove.assert_not_called()
        third.remove.assert_not_called()

    def test_trim_clamps_camera_to_content_height(self):
        console = self._make_console(max_lines=2)
        self._add_line(console, "first")
        self._add_line(console, "second")
        self._add_line(console, "third")
        console.camera.y = 500

        console._trim_old_lines()

        # Zwei Zeilen: 2 * (20 + 5) = 50 Pixel Inhaltshoehe
        self.assertEqual(console.camera.world_size_y, 50)
        self.assertEqual(console.camera.y, 0)

    def test_trim_without_overflow_changes_nothing(self):
        console = self._make_console(max_lines=5)
        first = self._add_line(console, "first")
        console.camera.y = 7

        console._trim_old_lines()

        self.assertEqual(len(console.widgets), 1)
        first.remove.assert_not_called()
        self.assertEqual(console.camera.y, 7)


if __name__ == "__main__":
    unittest.main()