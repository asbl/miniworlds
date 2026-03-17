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

        Toolbar.remove(toolbar, first)

        self.assertNotIn(0, toolbar.widgets)
        self.assertIn(1, toolbar.widgets)
        first.remove.assert_called_once_with()
        second.remove.assert_not_called()


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


if __name__ == "__main__":
    unittest.main()