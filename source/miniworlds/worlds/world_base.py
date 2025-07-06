from abc import ABC
import miniworlds.worlds.manager.world_connector as world_connector
import miniworlds.worlds.manager.event_manager as event_manager
import miniworlds.worlds.manager.camera_manager as world_camera_manager
import miniworlds.worlds.manager.mainloop_manager as mainloop_manager

class WorldBase(ABC):
    """
    Base class for worlds
    """

    def __init__(self):
        self.dirty = 1
        self.is_listening = True
        self.registered_events = {"mouse_left", "mouse_right"}
        # private
        self._window = None  # Set in add_to_window
        self._app = None
        self.screen_top_left_x = 0  # Set in add_to_window
        self.screen_top_left_y = 0  # Set in add_to_window
        self._image = None


    @property
    def window(self):
        return self._window

    @property
    def size(self):
        return self.screen_width, self.screen_height

    def remove(self, actor):
        """
        Implemented in subclasses
        """
        actor.remove()

    @property
    def topleft(self):
        return self.screen_top_left_x, self.screen_top_left_y

    @property
    def width(self):
        return self.camera.width

    @property
    def height(self):
        return self.camera.height

    def on_change(self):
        """implemented in subclasses"""
        pass

    def on_new_actor(self, actor):
        pass

    def on_remove_actor(self, actor):
        pass
    

    @staticmethod
    def _get_mainloopmanager_class():
        return mainloop_manager.MainloopManager

    @staticmethod
    def _get_camera_manager_class():
        return world_camera_manager.CameraManager

    @staticmethod
    def _get_world_connector_class():
        """needed by get_world_connector in parent class"""
        return world_connector.WorldConnector

    def get_world_connector(self, actor) -> world_connector.WorldConnector:
        return self._get_world_connector_class()(self, actor)

    def _create_event_manager(self):
        return event_manager.EventManager(self)