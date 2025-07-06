from typing import List
import os
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
        pygame.display.set_caption(title)
        my_path = os.path.abspath(os.path.dirname(__file__))
        try:
            path = os.path.join(my_path, "../resources/logo_small_32.png")
            surface = pygame.image.load(path)
            pygame.display.set_icon(surface)
        except Exception as e:
            raise Exception("Error on creating window: " + str(e))

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

    def _update_surface(self):
        """Updates the surface of window. Everything is drawn and scaled to the surface

        Defaults to containers_width/height

        Depends on the values of self.fullscreen, self.fit_desktop and self.replit
        """
        if self.fullscreen:
            self._surface = pygame.display.set_mode(
                (self.width, self.height), pygame.SCALED
            )
            pygame.display.toggle_fullscreen()
        elif self.fit_desktop:
            self._surface = pygame.display.set_mode((0, 0))
        elif self.replit:
            self._surface = pygame.display.set_mode((800, 600), pygame.SCALED)
        else:
            
            if self.app.init:
                info = pygame.display.Info()
                x, y = (
                    max((info.current_w - self.width) / 2, 0),
                    max((info.current_h - self.height) / 2, 0),
                )
                os.environ["SDL_VIDEO_WINDOW_POS"] = "%d,%d" % (x, y)
                self._surface = pygame.display.set_mode((self.width, self.height))
            else:
                if not self.mode:
                    self._surface = pygame.display.set_mode((1, 1))
                    self.mode = True
        self._surface.set_alpha(None)

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