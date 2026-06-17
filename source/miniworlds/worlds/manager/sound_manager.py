from typing import Optional
import logging
import miniworlds.base.app as app_mod

logger = logging.getLogger(__name__)


class SoundManager:
    """Manages short sound-effect playback for a world.

    Access via `world.sound`.

    Unlike `world.music`, sounds can overlap and are designed for short
    in-game effects.

    Examples:
        ::

            world.sound.play("assets/explosion.wav")
            world.sound.play("assets/jump.wav", volume=80)
    """

    def __init__(self, app: "app_mod.App"):
        self.app: "app_mod.App" = app
        self.sound_manager = self.app.sound_manager

    def play(self, path: str, volume: int = 100) -> None:
        """Play a sound.

        Args:
            path: Path to the sound.
            volume: Volume between `0` and `100`.

        Raises:
            ValueError: If path is empty or volume is out of range.

        Examples:
            ::

                world.sound.play("sounds/explosion.wav", volume=80)
        """
        if not path:
            raise ValueError("Sound path must not be empty.")
        if not (0 <= volume <= 100):
            raise ValueError("Volume must be between 0 and 100.")

        logger.debug(f"Playing sound: {path} at volume {volume}")
        self.sound_manager.play_sound(path, volume=volume)

    def register(self, path: str) -> None:
        """Register a sound for later use.

        Args:
            path: Path to the sound.

        Raises:
            ValueError: If path is empty.

        Examples:
            ::

                world.sound.register("sounds/explosion.wav")
        """
        if not path:
            raise ValueError("Sound path must not be empty.")

        logger.debug(f"Registering sound: {path}")
        self.sound_manager.register_sound(path)

    def is_registered(self, path: str) -> bool:
        """Return whether a sound is already registered.

        Args:
            path: Path to the sound.

        Returns:
            `True` if the sound is registered.

        Raises:
            ValueError: If path is empty.

        Examples:
            ::

                if not world.sound.is_registered("sounds/explosion.wav"):
                    world.sound.register("sounds/explosion.wav")
        """
        if not path:
            raise ValueError("Sound path must not be empty.")

        return self.sound_manager.is_sound_registered(path)

    def stop(self, path: str) -> None:
        """Stop a playing sound.

        Args:
            path: Path to the sound to stop.

        Raises:
            ValueError: If path is empty.

        Examples:
            ::

                world.sound.stop("sounds/explosion.wav")
        """
        if not path:
            raise ValueError("Sound path must not be empty.")

        logger.debug(f"Stopping sound: {path}")
        self.sound_manager.stop_sound(path)

    def is_playing(self, path: str) -> bool:
        """Return whether the given sound is currently playing.

        Args:
            path: Path to the sound.

        Returns:
            `True` if the sound is playing.

        Raises:
            ValueError: If path is empty.

        Examples:
            ::

                if world.sound.is_playing("sounds/explosion.wav"):
                    world.sound.stop("sounds/explosion.wav")
        """
        if not path:
            raise ValueError("Sound path must not be empty.")

        return self.sound_manager.is_sound_playing(path)
