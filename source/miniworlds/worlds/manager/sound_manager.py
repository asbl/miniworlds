from typing import Optional

import miniworlds.base.app as app_mod



class SoundManager:
    def __init__(self, app: "app_mod.App"):
        self.app: "app_mod.App" = app
        self.sound_manager = self.app.sound_manager

    def play(self, path: Optional[str] = None, volume: int = 100):
        """plays a sound from path

        Args:
            path: The path to the sound
            volume: The volume, the sound should be played (0 min, 100 max)

        Returns:

        """
        self.sound_manager.play_sound(path, volume = volume)

    def register(self, path: Optional[str] = None):
        """Registers a sound. It can slow down the performance, if sounds are loaded on the fly and it can be
        faster to register all sounds at program start.

        Args:
            path: The path to the sound
        """
        self.sound_manager.register_sound(path)
