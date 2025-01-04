import pygame
from abc import ABC


class WorldBase(ABC):
    """
    Base class for containers
    """

    def __init__(self):
        self.dirty = 1
        self.is_listening = True
        self._surface = pygame.Surface((1, 1))
        self.registered_events = {"mouse_left", "mouse_right"}
        # private
        self._window = None  # Set in add_to_window
        self._app = None
        self.screen_top_left_x = 0  # Set in add_to_window
        self.screen_top_left_y = 0  # Set in add_to_window
        self.docking_position = None  # Set in add_to_windows
        self._image = None

    @property
    def surface(self):
        return self._surface

    @surface.setter
    def surface(self, value):
        self._surface = value

    def on_change(self):
        """implemented in subclasses"""
        pass

    @property
    def window(self):
        return self._window

    def add_to_window(self, app, dock, size: int = 100):
        self._app = app
        self._window = self._app.window
        self.docking_position = dock
        # self.update_width_and_height()
        self._image = pygame.Surface((self.width, self.height))

    def update_width_and_height(self):
        if self.docking_position == "top_left":
            self.screen_top_left_x = 0
            self.screen_top_left_y = 0
        elif self.docking_position == "right":
            self.screen_top_left_y = 0
            self.screen_height = self._app.window.height
            self.screen_width = self.window.width
        elif self.docking_position == "bottom":
            self.screen_top_left_x = 0
            self.screen_width = self._app.window.width
            self.screen_height = self.window.height

    @property
    def size(self):
        return self.screen_width, self.screen_height

    def repaint(self):
        """
        Implemented in subclasses
        """
        pass

    def blit_surface_to_window_surface(self):
        self._app.window.surface.blit(self.surface, self.camera.get_screen_rect())

    def remove(self, actor):
        """
        Implemented in subclasses
        """
        actor.remove()

    def handle_event(self, event, data):
        self.get_event(event, data)

    def get_event(self, event, data):
        """
        Implemented in subclasses
        """
        pass

    @property
    def rect(self):
        return pygame.Rect(
            self.screen_top_left_x, self.screen_top_left_y, self.width, self.height
        )

    @property
    def topleft(self):
        return self.screen_top_left_x, self.screen_top_left_y

    @property
    def window_docking_position(self):
        return self.docking_position

    def update(self):
        """
        Implemented in subclasses
        """
        pass

    @property
    def width(self):
        return self.camera.width

    @property
    def height(self):
        return self.camera.height

    def get_local_position(self, position: tuple) -> tuple:
        x = position[0] - self.screen_top_left_x
        y = position[1] - self.screen_top_left_y
        return (x, y)

    def on_new_actor(self, actor):
        pass

    def on_remove_actor(self, actor):
        pass
    