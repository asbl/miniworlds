from typing import Optional
import miniworlds.base.app as app_mod

class MusicManager:
    def __init__(self, app: app_mod.App):
        # Store a reference to the app and its internal music manager
        self.app: app_mod.App = app
        self.music_manager = self.app.music_manager

    def pause(self) -> None:
        """
        Pauses the currently playing music.

        Examples:
            >>> world.music.pause()
        """
        self.music_manager.pause()

    def is_playing(self) -> bool:
        """
        Checks if music is currently playing (not paused).

        Returns:
            True if music is playing, False otherwise.

        Examples:
            >>> if world.music.is_playing():
            ...     print("Music is playing.")
        """
        return self.music_manager.is_playing()

    def get_path(self) -> str:
        """
        Returns the path of the currently loaded music file.

        Returns:
            Path to the current music file.

        Examples:
            >>> current_path = world.music.get_path()
            >>> print(current_path)
        """
        return self.music_manager.path()

    def play(self, path: Optional[str] = None, loop: int = -1) -> None:
        """
        Plays a music file from the given path.

        Args:
            path: Path to the music file. If None, replays the last used music.
            loop: Number of times to repeat the music. Use -1 for infinite looping.

        Examples:
            >>> world.music.play("assets/music/theme.mp3")
            >>> world.music.play("assets/music/loop.wav", loop=2)
            >>> world.music.play()  # Replays last loaded music
        """
        self.music_manager.play_music(path, loop)

    def stop(self) -> None:
        """
        Stops the currently playing music.

        Examples:
            >>> world.music.stop()
        """
        self.music_manager.stop_music()

    def set_volume(self, volume: float) -> None:
        """
        Sets the playback volume.

        Args:
            volume: Volume level from 0.0 (silent) to 100.0 (maximum).

        Raises:
            ValueError: If volume is outside the 0-100 range.

        Examples:
            >>> world.music.set_volume(80)
        """
        if not 0.0 <= volume <= 100.0:
            raise ValueError("Volume must be between 0 and 100.")
        self.music_manager.set_volume(volume)

    def get_volume(self) -> float:
        """
        Gets the current playback volume.

        Returns:
            Volume level as a float between 0.0 and 100.0.

        Examples:
            >>> current_volume = world.music.get_volume()
            >>> print(f"Volume: {current_volume}")
        """
        return self.music_manager.get_volume()

    def toggle_pause(self) -> None:
        """
        Toggles the pause state of the music. Pauses if playing, resumes if paused.

        Note:
            This assumes that the internal music manager has a `resume()` method.

        Examples:
            >>> world.music.toggle_pause()
        """
        if self.is_playing():
            self.pause()
        else:
            # Resume playback if previously paused
            self.music_manager.resume()
