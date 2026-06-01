from typing import List
import os
from pathlib import Path
import pygame
import miniworlds.base.manager.app_worlds_manager as worlds_manager_mod
import miniworlds.base.manager.app_event_manager as event_manager_mod


class Window:
    def __init__(
        self,
        title,
        app,
        worlds_manager: "worlds_manager_mod.WorldsManager",
        event_manager: "event_manager_mod.AppEventManager",
    ):
        self.title: str = title
        self.app = app
        self.worlds_manager: "worlds_manager_mod.WorldsManager" = worlds_manager
        self.event_manager: "event_manager_mod.AppEventManager" = event_manager
        self.default_size: int = 200
        self.dirty: int = 1
        self._surface: pygame.Surface = pygame.Surface((0, 0))
        self._fullscreen: bool = False
        self._fit_desktop = False
        self._replit = False
        self.mode = False
        self.app.platform.set_window_caption(title)
        my_path = Path(__file__).resolve().parent
        try:
            path = my_path / "../resources/logo_small_32.png"
            surface = self.app.platform.load_surface(path)
            self.app.platform.set_window_icon(surface)
        except Exception as e:
            raise RuntimeError(
                f"Could not create the window. Common reasons:\n"
                f"1. Missing asset file: {path}\n"
                f"2. Wrong file path (use 'assets/file.png', not 'assets\\\\file.png')\n"
                f"3. File format not supported (use PNG, JPG, or GIF)\n"
                f"Full error: {e}"
            ) from e

    @property
    def fullscreen(self):
        """toggles fullscreen mode"""
        return self._fullscreen

    @fullscreen.setter
    def fullscreen(self, value):
        self._fullscreen = value
        self._update_surface()

    @property
    def fit_desktop(self):
        return self._fit_desktop

    @fit_desktop.setter
    def fit_desktop(self, value):
        """fits to desktop"""
        self._fit_desktop = value
        self.dirty = 1
        # self.display_update()

    @property
    def replit(self):
        """Scales display to 800x600 for replit"""
        return self._replit

    @replit.setter
    def replit(self, value):
        self._replit = value
        self.dirty = 1
        # self.display_update()

    @property
    def surface(self):
        return self._surface

    def _update_surface(self) -> None:
        """Updates the surface of window. Everything is drawn and scaled to the surface

        Defaults to containers_width/height

        Depends on the values of self.fullscreen, self.fit_desktop and self.replit
        """
        if self.fullscreen:
            self._surface = self.app.platform.set_mode(
                (self.width, self.height), pygame.SCALED
            )
            self.app.platform.toggle_fullscreen()
        elif self.fit_desktop:
            self._surface = self.app.platform.set_mode((0, 0))
        elif self.replit:
            self._surface = self.app.platform.set_mode((800, 600), pygame.SCALED)
        else:
            self._place_window_within_screen(self.width, self.height)
            if self.app.init:
                self._surface = self.app.platform.set_mode((self.width, self.height))
                self._place_window_within_screen(self.width, self.height)
            else:
                if not self.mode:
                    self._surface = self.app.platform.set_mode((1, 1))
                    self.mode = True
        self._surface.set_alpha(None)

    def _place_window_within_screen(self, width: int, height: int) -> None:
        x, y = self._window_position_within_screen(width, height)
        position = (x, y)
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{x},{y}"
        self.app.platform.set_window_position(position)

    def _window_position_within_screen(self, width: int, height: int) -> tuple[int, int]:
        info = self.app.platform.display_info()
        return (
            self._center_or_clamp(width, info.current_w),
            self._center_or_clamp(height, info.current_h),
        )

    @staticmethod
    def _center_or_clamp(window_size: int, screen_size: int) -> int:
        return max((screen_size - window_size) // 2, 0)

    @property
    def width(self) -> int:
        """Gets total width from worlds manager"""
        return self.worlds_manager.worlds_total_width

    @property
    def height(self) -> int:
        """Gets total height from worlds manager"""
        return self.worlds_manager.worlds_total_height

    def reset(self):
        self.worlds_manager.reset()
