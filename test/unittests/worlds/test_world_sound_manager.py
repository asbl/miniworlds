import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from miniworlds.worlds.manager.sound_manager import SoundManager


class TestWorldSoundManager(unittest.TestCase):
    def setUp(self):
        self.internal_manager = SimpleNamespace(
            play_sound=Mock(),
            register_sound=Mock(),
            is_sound_registered=Mock(return_value=True),
            stop_sound=Mock(),
            is_sound_playing=Mock(return_value=False),
        )
        self.manager = SoundManager(SimpleNamespace(sound_manager=self.internal_manager))

    def test_play_delegates_to_app_sound_manager(self):
        self.manager.play("sounds/explosion.wav", volume=80)

        self.internal_manager.play_sound.assert_called_once_with("sounds/explosion.wav", volume=80)

    def test_play_rejects_empty_path(self):
        with self.assertRaises(ValueError):
            self.manager.play("")

    def test_play_rejects_out_of_range_volume(self):
        for volume in (-1, 101):
            with self.subTest(volume=volume):
                with self.assertRaises(ValueError):
                    self.manager.play("sounds/explosion.wav", volume=volume)

    def test_register_delegates_and_rejects_empty_path(self):
        self.manager.register("sounds/explosion.wav")

        self.internal_manager.register_sound.assert_called_once_with("sounds/explosion.wav")

        with self.assertRaises(ValueError):
            self.manager.register("")

    def test_is_registered_delegates(self):
        self.assertTrue(self.manager.is_registered("sounds/explosion.wav"))

        self.internal_manager.is_sound_registered.assert_called_once_with("sounds/explosion.wav")

    def test_stop_delegates_and_rejects_empty_path(self):
        self.manager.stop("sounds/explosion.wav")

        self.internal_manager.stop_sound.assert_called_once_with("sounds/explosion.wav")

        with self.assertRaises(ValueError):
            self.manager.stop("")

    def test_is_playing_delegates(self):
        self.assertFalse(self.manager.is_playing("sounds/explosion.wav"))

        self.internal_manager.is_sound_playing.assert_called_once_with("sounds/explosion.wav")