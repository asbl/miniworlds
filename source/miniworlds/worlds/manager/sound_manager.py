from typing import Optional
import logging
import miniworlds.base.app as app_mod

logger = logging.getLogger(__name__)


class SoundManager:
    def __init__(self, app: "app_mod.App"):
        self.app: "app_mod.App" = app
        self.sound_manager = self.app.sound_manager

    def play(self, path: str, volume: int = 100) -> None:
        """Plays a sound from the given path.

        Args:
            path: The path to the sound.
            volume: Volume to play the sound (0 min, 100 max).

        Raises:
            ValueError: If path is empty or volume is out of range.

        Example:
            world.sound.play("sounds/explosion.wav", volume=80)
        """
        if not path:
            raise ValueError("Sound path must not be empty.")
        if not (0 <= volume <= 100):
            raise ValueError("Volume must be between 0 and 100.")

        logger.debug(f"Playing sound: {path} at volume {volume}")
        self.sound_manager.play_sound(path, volume=volume)

    def register(self, path: str) -> None:
        """Registers a sound for later use.

        Args:
            path: The path to the sound.

        Raises:
            ValueError: If path is empty.

        Example:
            world.sound.register("sounds/explosion.wav")
        """
        if not path:
            raise ValueError("Sound path must not be empty.")

        logger.debug(f"Registering sound: {path}")
        self.sound_manager.register_sound(path)

    def is_registered(self, path: str) -> bool:
        """Checks if a sound is already registered.

        Args:
            path: The path to the sound.

        Returns:
            bool: True if the sound is already registered, False otherwise.

        Raises:
            ValueError: If path is empty.

        Example:
            if not world.sound.is_registered("sounds/explosion.wav"):
                world.sound.register("sounds/explosion.wav")
        """
        if not path:
            raise ValueError("Sound path must not be empty.")

        return self.sound_manager.is_sound_registered(path)

    def stop(self, path: str) -> None:
        """Stops a playing sound.

        Args:
            path: The path to the sound to stop.

        Raises:
            ValueError: If path is empty.

        Example:
            world.sound.stop("sounds/explosion.wav")
        """
        if not path:
            raise ValueError("Sound path must not be empty.")

        logger.debug(f"Stopping sound: {path}")
        self.sound_manager.stop_sound(path)

    def is_playing(self, path: str) -> bool:
        """Checks if the given sound is currently playing.

        Args:
            path: The path to the sound.

        Returns:
            bool: True if the sound is currently playing, False otherwise.

        Raises:
            ValueError: If path is empty.

        Example:
            if world.sound.is_playing("sounds/explosion.wav"):
                world.sound.stop("sounds/explosion.wav")
        """
        if not path:
            raise ValueError("Sound path must not be empty.")

        return self.sound_manager.is_sound_playing(path)
