import pygame
from typing import Dict

import miniworlds.base.app as app_mod
import miniworlds.base.manager.channel as channel_mod


class SoundManager:
    def __init__(self, app: "app_mod.App"):
        self.sound_effects: Dict[str, pygame.mixer.Sound] = {}
        self.channels: Dict[str, channel_mod.Channel] = {}
        self.app: "app_mod.App" = app
        self.audio = self.app.platform
        self.volume = 100
        self._has_music = False
        self.audio.ensure_audio(reserved_channels=2, channel_count=64)

    def register_sound(self, path) -> pygame.mixer.Sound:
        """
        Registers a sound effect to world-sound effects library

        Args:
            path: The path to sound

        Returns:
            the sound

        """
        try:
            effect: pygame.mixer.Sound = self.audio.load_sound(path)
            self.sound_effects[path] = effect
            return effect
        except pygame.error:
            raise FileExistsError("File '{0}' does not exist. Check your path to the sound.".format(path))

    def play_sound(self, path: str, prio=False, volume: float = 100):
        if prio:
            return self._play_high_priority(path, volume)
        else:
            return self._play_low_priority(path, volume)

    def _play_low_priority(self, path: str, volume: float):
        if path in self.sound_effects.keys():
            sound = self.sound_effects[path]
            sound.set_volume(volume / 100)
            pygame_channel = sound.play()
            channel = channel_mod.Channel(pygame_channel, path)
            channel.set_volume(volume)
            self.channels[path] = channel
            return channel
        else:
            sound = self.register_sound(path)
            sound.set_volume(volume / 100)
            pygame_channel = sound.play()
            channel = channel_mod.Channel(pygame_channel, path)
            channel.set_volume(volume)
            self.channels[path] = channel
            return channel

    def _play_high_priority(self, path: str, volume: float):
        if path in self.sound_effects.keys():
            pygame_channel = self.audio.find_channel()
            sound = self.sound_effects[path]
            sound.set_volume(volume / 100)
            pygame_channel.play(sound)
            channel = channel_mod.Channel(pygame_channel, path)
            channel.set_volume(volume)
            self.channels[path] = channel
            return channel
        else:
            sound = self.register_sound(path)
            sound.set_volume(volume / 100)
            pygame_channel = self.audio.find_channel()
            pygame_channel.play(sound)
            channel = channel_mod.Channel(pygame_channel, path)
            channel.set_volume(volume)
            self.channels[path] = channel
            return channel

    def set_volume(self, volume, path: str = ""):
        """Sets volume (max: 100, min: 0)
        """
        if path:
            self.sound_effects[path].set_volume(volume / 100)
        else:
            for key, sound_effect in self.sound_effects.items():
                sound_effect.set_volume(volume / 100)

    def stop(self, path: str = ""):
        """Sets volume (max: 100, min: 0)
        """
        if path:
            self.sound_effects[path].stop()
            self.channels.pop(path, None)
        else:
            for key, sound_effect in self.sound_effects.items():
                sound_effect.stop()
            self.channels.clear()

    def stop_sound(self, path: str):
        self.stop(path)

    def is_sound_registered(self, path: str) -> bool:
        return path in self.sound_effects

    def is_sound_playing(self, path: str) -> bool:
        channel = self.channels.get(path)
        if not channel:
            return False
        return channel.is_playing()
