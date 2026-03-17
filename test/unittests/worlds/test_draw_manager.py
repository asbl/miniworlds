import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from miniworlds.worlds.manager.draw_manager import DrawManager


class TestDrawManager(unittest.TestCase):
    def setUp(self):
        self.background = SimpleNamespace(
            fill_color=(10, 20, 30, 255),
            fill=Mock(),
            image=SimpleNamespace(get_at=Mock(return_value=(1, 2, 3, 4))),
        )
        self.world = SimpleNamespace(background=self.background)
        self.manager = DrawManager(self.world)

    def test_default_fill_color_converts_to_float_tuple(self):
        self.manager.default_fill_color = (255, 0, 128)

        self.assertEqual(self.manager.default_fill_color, (255.0, 0.0, 128.0))

    def test_fill_updates_default_fill_color(self):
        self.manager.fill((5, 6, 7, 8))

        self.assertEqual(self.manager.default_fill_color, (5.0, 6.0, 7.0, 8.0))

    def test_stroke_updates_default_border_color(self):
        self.manager.stroke((9, 8, 7))

        self.assertEqual(self.manager.default_border_color, (9, 8, 7))

    def test_fill_color_property_delegates_to_background(self):
        self.assertEqual(self.manager.fill_color, (10, 20, 30, 255))

        self.manager.fill_color = (40, 50, 60)

        self.background.fill.assert_called_once_with((40, 50, 60))

    def test_get_color_from_pixel_casts_coordinates_to_int(self):
        color = self.manager.get_color_from_pixel((3.9, 4.2))

        self.background.image.get_at.assert_called_once_with((3, 4))
        self.assertEqual(color, (1, 2, 3, 4))

    def test_default_border_property_round_trips_value(self):
        self.manager.default_border = 3

        self.assertEqual(self.manager.default_border, 3)