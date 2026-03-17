import unittest
from unittest.mock import patch, MagicMock
import pygame

# Importiere App und MusicManager direkt aus deinem Projekt
from miniworlds.base.app import App
from miniworlds.base.manager.app_music_manager import MusicManager


class DummyWorld:
    """
    Minimal mock for a World object used in App constructor.
    """
    def __init__(self):
        self.dirty = 0
        self.background = MagicMock()
        self.background.set_dirty = MagicMock()


class DummyApp(App):
    """
    App subclass that bypasses real init by injecting dummy values.
    """
    def __init__(self):
        super().__init__(title="TestApp", world=DummyWorld())


class TestMusicManager(unittest.TestCase):

    def setUp(self):
        # Patch pygame.mixer.music globally
        patcher_music = patch("pygame.mixer.music", autospec=True)
        self.mock_music = patcher_music.start()
        self.addCleanup(patcher_music.stop)

        # Patch pygame.mixer.init to prevent actual audio init
        patcher_init = patch("pygame.mixer.init", autospec=True)
        patcher_init.start()
        self.addCleanup(patcher_init.stop)

        self.app = DummyApp()
        self.manager = MusicManager(self.app)

    def test_play_music_with_path(self):
        self.manager.play_music("test.mp3", loop=1)
        self.mock_music.load.assert_called_with("test.mp3")
        self.mock_music.play.assert_called_with(1)
        self.assertFalse(self.manager._paused)

    def test_play_music_without_path(self):
        self.manager.path = "existing.mp3"
        self.manager.play_music()
        self.mock_music.play.assert_called()
        self.assertFalse(self.manager._paused)

    def test_pause_and_resume(self):
        self.manager.pause()
        self.mock_music.pause.assert_called_once()
        self.assertTrue(self.manager._paused)

        self.manager.resume()
        self.mock_music.unpause.assert_called_once()
        self.assertFalse(self.manager._paused)

    def test_stop_music(self):
        self.manager.stop_music()
        self.mock_music.stop.assert_called_once()
        self.assertFalse(self.manager._paused)

    def test_fade_in_and_out(self):
        self.manager.fade_in(1000)
        self.mock_music.play.assert_called_with(-1, 0, 1000)
        self.assertFalse(self.manager._paused)

        self.manager.fade_out(500)
        self.mock_music.fadeout.assert_called_with(500)
        self.assertFalse(self.manager._paused)

    def test_set_and_get_volume(self):
        self.mock_music.get_volume.return_value = 0.75
        vol = self.manager.get_volume()
        self.assertEqual(vol, 75.0)

        self.manager.set_volume(50.0)
        self.mock_music.set_volume.assert_called_with(0.5)

        self.manager.volume = 25.0
        self.mock_music.set_volume.assert_called_with(0.25)

        self.mock_music.get_volume.return_value = 0.9
        self.assertEqual(self.manager.volume, 90.0)

    def test_get_state_playing(self):
        self.mock_music.get_busy.return_value = True
        self.manager._paused = False
        self.assertEqual(self.manager.get_state(), "playing")

    def test_get_state_paused(self):
        self.mock_music.get_busy.return_value = True
        self.manager._paused = True
        self.assertEqual(self.manager.get_state(), "paused")

    def test_get_state_stopped(self):
        self.mock_music.get_busy.return_value = False
        self.manager._paused = False
        self.assertEqual(self.manager.get_state(), "stopped")


if __name__ == "__main__":
    unittest.main()
