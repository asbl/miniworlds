import os
import unittest
from unittest.mock import patch

import pygame

from miniworlds.base.platform import PlatformAdapter


class TestPlatformAdapter(unittest.TestCase):
    def test_ensure_audio_prefers_dummy_backend_in_test_mode(self):
        adapter = PlatformAdapter()

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SDL_AUDIODRIVER", None)
            os.environ["MINIWORLDS_TEST_FAST"] = "1"
            with patch("pygame.mixer.init") as init_mock:
                adapter.ensure_audio()

                self.assertEqual(os.environ["SDL_AUDIODRIVER"], "dummy")
                init_mock.assert_called_once_with()

    def test_ensure_audio_falls_back_to_dummy_backend_after_init_error(self):
        adapter = PlatformAdapter()

        with patch.dict(os.environ, {}, clear=True):
            with patch("pygame.mixer.init", side_effect=[pygame.error("boom"), None]) as init_mock:
                with patch("pygame.mixer.quit") as quit_mock:
                    adapter.ensure_audio()

                    self.assertEqual(os.environ["SDL_AUDIODRIVER"], "dummy")
                    self.assertEqual(init_mock.call_count, 2)
                    quit_mock.assert_called_once_with()

    def test_get_package_version_returns_unknown_for_missing_distribution(self):
        adapter = PlatformAdapter()

        self.assertEqual(
            adapter.get_package_version("__missing_miniworlds_test_package__"),
            "unknown",
        )

    def test_get_package_version_returns_unknown_without_importlib_metadata(self):
        adapter = PlatformAdapter()

        with patch.dict("sys.modules", {"importlib.metadata": None}):
            self.assertEqual(adapter.get_package_version("miniworlds"), "unknown")


if __name__ == "__main__":
    unittest.main()
