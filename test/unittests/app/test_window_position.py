from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from miniworlds.base.window import Window


class TestWindowPosition(unittest.TestCase):
    def test_window_position_centers_when_window_fits_screen(self):
        window = Window.__new__(Window)
        window.app = SimpleNamespace(
            platform=SimpleNamespace(
                display_info=Mock(return_value=SimpleNamespace(current_w=1000, current_h=800))
            )
        )

        self.assertEqual(window._window_position_within_screen(400, 300), (300, 250))

    def test_window_position_uses_top_left_when_window_is_larger_than_screen(self):
        window = Window.__new__(Window)
        window.app = SimpleNamespace(
            platform=SimpleNamespace(
                display_info=Mock(return_value=SimpleNamespace(current_w=1000, current_h=800))
            )
        )

        self.assertEqual(window._window_position_within_screen(1200, 900), (0, 0))

    def test_initial_placeholder_uses_real_window_position(self):
        surface = Mock()
        platform = SimpleNamespace(
            display_info=Mock(return_value=SimpleNamespace(current_w=1000, current_h=800)),
            set_mode=Mock(return_value=surface),
            set_window_position=Mock(),
        )
        window = Window.__new__(Window)
        window.app = SimpleNamespace(init=False, platform=platform)
        window.worlds_manager = SimpleNamespace(worlds_total_width=400, worlds_total_height=300)
        window._fullscreen = False
        window._fit_desktop = False
        window._replit = False
        window.mode = False

        with patch.dict(os.environ, {}, clear=False):
            window._update_surface()
            self.assertEqual(os.environ["SDL_VIDEO_WINDOW_POS"], "300,250")

        platform.set_mode.assert_called_once_with((1, 1))
        platform.set_window_position.assert_called_once_with((300, 250))
        surface.set_alpha.assert_called_once_with(None)


if __name__ == "__main__":
    unittest.main()
