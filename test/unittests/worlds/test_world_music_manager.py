import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from miniworlds.worlds.manager.music_manager import MusicManager


class TestWorldMusicManager(unittest.TestCase):
    def test_get_path_returns_current_music_path(self):
        internal_manager = SimpleNamespace(path="music/theme.mp3")
        app = SimpleNamespace(music_manager=internal_manager)
        manager = MusicManager(app)

        self.assertEqual(manager.get_path(), "music/theme.mp3")

    def test_toggle_pause_resumes_when_not_playing(self):
        internal_manager = SimpleNamespace(path=None, resume=Mock())
        app = SimpleNamespace(music_manager=internal_manager)
        manager = MusicManager(app)
        manager.is_playing = Mock(return_value=False)

        manager.toggle_pause()

        internal_manager.resume.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()