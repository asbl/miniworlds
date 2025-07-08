import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import miniworlds.base.app as app_mod

class MusicManager:
    """
    Handles background music playback using pygame.mixer.

    This class provides methods to load, play, pause, stop, fade, and control volume
    of music files. It is designed to be accessed via `world.music` in user code.
    """

    def __init__(self, app: "app_mod.App"):
        """
        Initializes the music system and binds it to the app.

        Args:
            app: Reference to the main App instance.
        """
        self.app: "app_mod.App" = app
        self.path: str | None = None
        self._paused: bool = False  # Tracks pause state manually
        pygame.mixer.init()

    def change_music(self, path: str) -> None:
        """
        Stops current music and loads a new music file.

        Args:
            path: Path to the new music file.
        """
        self.stop_music()
        self.path = path
        pygame.mixer.music.load(self.path)

    def load_music(self, path: str) -> None:
        """
        Loads a music file without starting playback.

        Args:
            path: Path to the music file.
        """
        self.path = path
        pygame.mixer.music.load(self.path)

    def play_music(self, path: str | None = None, loop: int = -1) -> None:
        """
        Starts playback of a music file.

        Args:
            path: Optional path to a new music file. If None, plays the last loaded file.
            loop: Number of times to repeat the track (-1 = loop forever).
        """
        if path:
            self.load_music(path)
        if self.path:
            pygame.mixer.music.play(loop)
            self._paused = False

    def is_playing(self) -> bool:
        """
        Checks if music is currently playing (not paused).

        Returns:
            True if music is playing, False otherwise.
        """
        return pygame.mixer.music.get_busy() and not self._paused

    def get_state(self) -> str:
        """
        Returns the current playback state of the music.

        Returns:
            One of:
                - "playing": Music is currently playing.
                - "paused": Music is paused.
                - "stopped": Music is stopped or no music is loaded.

        Examples:
            >>> state = world.music.get_state()
            >>> print(f"State: {state}")
        """
        if self._paused:
            return "paused"
        elif pygame.mixer.music.get_busy():
            return "playing"
        else:
            return "stopped"

    def stop_music(self) -> None:
        """
        Stops the currently playing music immediately.
        """
        pygame.mixer.music.stop()
        self._paused = False

    def fade_out(self, time: int) -> None:
        """
        Fades out the currently playing music over the given duration.

        Args:
            time: Fade-out duration in milliseconds.
        """
        pygame.mixer.music.fadeout(time)
        self._paused = False

    def fade_in(self, time: int) -> None:
        """
        Fades in the currently loaded music and starts playback.

        Args:
            time: Fade-in duration in milliseconds.
        """
        pygame.mixer.music.play(-1, 0, time)
        self._paused = False

    def pause(self) -> None:
        """
        Pauses the music if it is currently playing.
        """
        pygame.mixer.music.pause()
        self._paused = True

    def unpause(self) -> None:
        """
        Unpauses the music if it was previously paused.
        """
        pygame.mixer.music.unpause()
        self._paused = False

    def resume(self) -> None:
        """
        Alias for unpause. Used by world.music.toggle_pause().
        """
        self.unpause()

    @property
    def volume(self) -> float:
        """
        Gets the current music volume.

        Returns:
            Volume as a float between 0.0 and 100.0.
        """
        return self.get_volume()

    @volume.setter
    def volume(self, value: float) -> None:
        """
        Sets the current music volume.

        Args:
            value: Volume as a float between 0.0 and 100.0.
        """
        self.set_volume(value)

    def set_volume(self, percent: float) -> None:
        """
        Sets the music volume.

        Args:
            percent: Volume level (0.0 to 100.0).
        """
        pygame.mixer.music.set_volume(percent / 100)

    def get_volume(self) -> float:
        """
        Returns the current volume level.

        Returns:
            Volume level (0.0 to 100.0).
        """
        return pygame.mixer.music.get_volume() * 100
