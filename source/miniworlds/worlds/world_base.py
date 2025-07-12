from abc import ABC, ABCMeta
from typing import Set, Callable
import pygame
import miniworlds.worlds.manager.world_connector as world_connector
import miniworlds.worlds.manager.event_manager as event_manager
import miniworlds.worlds.manager.camera_manager as world_camera_manager
import miniworlds.worlds.manager.mainloop_manager as mainloop_manager
import miniworlds.tools.world_inspection as world_inspection

class AutoSetupMeta(ABCMeta):
    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)  # führt __init__ aus
        if hasattr(instance, "app"):
            instance.app.worlds_manager.add_topleft_if_empty(instance)
            instance._after_init_setup()
        return instance

class WorldBase(metaclass=AutoSetupMeta):
    """
    Base class for worlds
    """
    def __init__(self):
        self.dirty = 1
        # Core state
        self.is_listening = True # is reacting to events
        self._is_setup_completed = False # should setup be called
        self._is_acting = True # is used to stop acting, if world will be removed
        self.is_running: bool = True # If world is running only event manager still listens to events; No costume update, no acting, ....
        self._default_start_running: bool = True # default running state e.g. if stop() is called before world.run()
        self.is_tiled = False # is a tiled world?
        self.registered_events = {"mouse_left", "mouse_right"}
        # private
        self._window = None  # Set in add_to_window
        self._app = None
        self.screen_top_left_x = 0  # Set in add_to_window
        self.screen_top_left_y = 0  # Set in add_to_window
        self._image = None

    def _after_init_setup(self):
        pass
        
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
        """implemented in subclasses
        
        on_change() is called, after world is added to window, resized, ...
        """
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

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    def screenshot(self, filename: str = "screenshot.jpg") -> None:
        """
        Saves a screenshot of the current window surface to a file.

        Args:
            filename: Path to the output image file. Directory must exist.

        Example:
            >>> world.screenshot(\"images/capture.jpg\")
        """
        pygame.image.save(self.app.window.surface, filename)


    def get_events(self) -> None:
        """
        Prints a list of all events that can be registered in this world.

        Useful for debugging or discovering built-in hooks.

        Example:
            >>> world.get_events()
            {'act', 'on_setup', 'on_key_down', ...}
        """
        print(self.event_manager.class_events_set)

    @property
    def registered_events(self) -> Set[str]:
        """
        Returns the set of all event names that are currently registered.

        Example:
            >>> print(world.registered_events)
            {'on_setup', 'act', 'on_key_down'}
        """
        return self.event_manager.registered_events

    @registered_events.setter
    def registered_events(self, value) -> None:
        """
        Prevents accidental overwriting of the event set.

        This is a dummy setter to avoid inheritance conflicts.
        """
        return

    def register(self, method: Callable) -> Callable:
        """
        Registers a method as a world event handler.

        Typically used as a decorator to bind a function to the event loop.

        Args:
            method: The function or method to register.

        Returns:
            The bound method that will be invoked by the world event system.

        Example:
            >>> @world.register
            ... def act():
            ...     print(\"Acting...\")
        """
        self._registered_methods.append(method)
        bound_method = world_inspection.WorldInspection(self).bind_method(method)
        self.event_manager.register_event(method.__name__, self)
        if method.__name__ == "on_setup":
            self._is_setup_completed = False
        return bound_method
        
    def _unregister(self, method: Callable) -> None:
        """
        Unregisters a previously registered world method.

        Args:
            method: The method that should no longer receive world events.
        """
        self._registered_methods.remove(method)
        world_inspection.WorldInspection(self).unbind_method(method)

    def _start_listening(self) -> None:
        """
        Enables input listening for the world.

        After calling this method, the world will start responding
        to input-related events such as mouse or keyboard interactions.

        Example:
            >>> world.start_listening()
        """
        self.is_listening = True


    def _stop_listening(self) -> None:
        """
        Disables input listening for the world.

        After calling this method, the world will stop reacting to user input events.

        Example:
            >>> world.stop_listening()
        """
        self.is_listening = False