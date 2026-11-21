import unittest
from unittest.mock import MagicMock

from miniworlds.base.manager.app_sound_manager import SoundManager


class DummyPlatform:
    def __init__(self):
        self.sound = MagicMock()
        self.channel = MagicMock()

    def ensure_audio(self, reserved_channels=None, channel_count=None):
        return None

    def load_sound(self, path):
        return self.sound

    def find_channel(self):
        return self.channel


class DummyApp:
    def __init__(self):
        self.platform = DummyPlatform()


class TestAppSoundManager(unittest.TestCase):
    def setUp(self):
        self.app = DummyApp()
        self.manager = SoundManager(self.app)

    def test_play_sound_registers_effect_and_tracks_channel(self):
        pygame_channel = MagicMock()
        self.app.platform.sound.play.return_value = pygame_channel

        channel = self.manager.play_sound("laser.wav", volume=25)

        self.assertTrue(self.manager.is_sound_registered("laser.wav"))
        self.assertTrue(self.manager.is_sound_playing("laser.wav"))
        self.assertIs(self.manager.channels["laser.wav"], channel)
        self.app.platform.sound.set_volume.assert_any_call(0.25)

    def test_audio_initializes_only_when_first_sound_is_registered(self):
        app = DummyApp()
        app.platform.ensure_audio = MagicMock()
        manager = SoundManager(app)
        manager.stop()
        self.assertFalse(manager.is_sound_playing("laser.wav"))
        app.platform.ensure_audio.assert_not_called()
        manager.play_sound("laser.wav", prio=True)
        app.platform.ensure_audio.assert_called_once_with(reserved_channels=2, channel_count=64)
        manager.play_sound("laser.wav")
        app.platform.ensure_audio.assert_called_once()

    def test_stop_sound_removes_tracked_channel(self):
        self.app.platform.sound.play.return_value = MagicMock()
        self.manager.play_sound("laser.wav", volume=50)

        self.manager.stop_sound("laser.wav")

        self.assertFalse(self.manager.is_sound_playing("laser.wav"))
        self.app.platform.sound.stop.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
