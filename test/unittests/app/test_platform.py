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


if __name__ == "__main__":
    unittest.main()