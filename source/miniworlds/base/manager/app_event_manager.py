from collections import deque
import pygame

import miniworlds.base.app as app_mod
from miniworlds.tools import keys


class AppEventManager:
    _MOUSE_DOWN_EVENT_MAP = {
        1: ("mouse_left", "mouse_left_down"),
        2: ("mouse_middle", "mouse_middle_down"),
        3: ("mouse_right", "mouse_right_down"),
    }
    _MOUSE_UP_EVENT_MAP = {
        1: ("mouse_left", "mouse_left_up"),
        2: ("mouse_middle", "mouse_middle_up"),
        3: ("mouse_right", "mouse_right_up"),
    }
    _MOUSE_WHEEL_EVENT_MAP = {
        4: "wheel_up",
        5: "wheel_down",
    }

    def __init__(self, app: "app_mod.App"):
        """Initializes the central application event manager.

        Args:
            app: The application instance that owns the event queue.
        """
        self.event_queue: deque = deque()
        self.is_key_pressed: dict = {}
        self.is_mouse_pressed: set = set()
        self.app: "app_mod.App" = app
        self._pygame_event_handlers = {
            pygame.QUIT: self._handle_quit_event,
            pygame.MOUSEBUTTONDOWN: self.put_mouse_down_in_event_queue,
            pygame.MOUSEBUTTONUP: self.put_mouse_up_in_event_queue,
            pygame.MOUSEMOTION: self._handle_mouse_motion_event,
            pygame.KEYDOWN: self._handle_key_down_event,
            pygame.KEYUP: self._handle_key_up_event,
            pygame.VIDEORESIZE: self._handle_resize_event,
            pygame.VIDEOEXPOSE: self._handle_resize_event,
        }

    def handle_event_queue(self):
        """Handle the event queue
        This function is called once per mainloop iteration.
        The event_queue is build with `to_event_queue`.
        """
        while self.event_queue:
            element = self.event_queue.pop()
            for world in self.app.worlds_manager.worlds:
                if world.is_listening:
                    world._mainloop.handle_event(element[0], element[1])
        self.event_queue.clear()

    def to_event_queue(self, event, data):
        """Puts an event to the event queue.

        It is handled in the handle_event_queue
        """
        self.event_queue.appendleft((event, data))


    def add_special_chars(self, keys):
        if " " in keys and "space" not in keys:
            keys.append("space")
        return keys
    
    
    def convert_special_chars(self, key: str) -> str:
        if key == " ":
            return "space"
        else:
            return key

    def _get_pressed_keys(self):
        return self.add_special_chars(list(self.is_key_pressed.values()))

    def _get_mouse_pos(self, event=None):
        if event is not None and hasattr(event, "pos"):
            return event.pos
        return self.app.platform.get_mouse_pos()

    def _resolve_key_name(self, event) -> str | None:
        key = keys.get_key(event.unicode, event.key)
        if key:
            return key

        native_key = pygame.key.name(event.key)
        if not native_key:
            return None
        return native_key.replace(" ", "_").replace("-", "_")

    def _iter_specific_key_names(self, key: str):
        normalized_key = self.convert_special_chars(key).replace(" ", "_").replace("-", "_")
        if len(normalized_key) > 1 and normalized_key.lower() != normalized_key:
            return (normalized_key, normalized_key.lower())
        return (normalized_key,)

    def _queue_specific_key_events(self, prefix: str, key: str) -> None:
        for key_name in self._iter_specific_key_names(key):
            self.to_event_queue(f"{prefix}_{key_name}", None)

    def _handle_quit_event(self, event) -> None:
        del event
        self.app.quit()

    def _handle_mouse_motion_event(self, event) -> None:
        self.to_event_queue("mouse_motion", self._get_mouse_pos(event))

    def _handle_key_down_event(self, event) -> None:
        key = self._resolve_key_name(event)
        if key:
            self.is_key_pressed[key] = key
        self.to_event_queue("key_down", self._get_pressed_keys())
        if key:
            self._queue_specific_key_events("key_down", key)

    def _handle_key_up_event(self, event) -> None:
        key = self._resolve_key_name(event)
        if key:
            self.is_key_pressed[key] = key
        self.to_event_queue("key_up", self._get_pressed_keys())
        if key:
            self._queue_specific_key_events("key_up", key)
            self.is_key_pressed.pop(key, None)

    def _handle_resize_event(self, event) -> None:
        del event
        for container in self.app.worlds_manager.worlds:
            container.dirty = 1
        self.app.add_display_to_repaint_areas()
    
    def pygame_events_to_event_queue(self):
        """Puts pygame events to event queue. Called in mainloop (App._update) 1/frame.

        Iterates over pygame.event.get() and puts events in event queue.
        """
        # Pressed keys are stored across frames and updated by key down/up handlers.
        for event in self.app.platform.poll_events():
            handler = self._pygame_event_handlers.get(event.type)
            if handler is not None:
                handler(event)
            if "\x11" in self._get_pressed_keys():
                self.app.quit()

        pressed_keys = self._get_pressed_keys()
        if self.is_key_pressed:
            self.to_event_queue("key_pressed", pressed_keys)
        pos = self.app.platform.get_mouse_pos()
        if self.is_mouse_pressed:
            for event in self.is_mouse_pressed:
                self.to_event_queue(event, pos)
        for value in self.is_key_pressed.values():
            if value != "":
                self._queue_specific_key_events("key_pressed", value)

        return False

    def put_mouse_down_in_event_queue(self, event):
        """function is called in 'pygame_events_to_event_queue"""
        pos = self._get_mouse_pos(event)
        mouse_events = self._MOUSE_DOWN_EVENT_MAP.get(event.button)
        if mouse_events is not None:
            hold_event, down_event = mouse_events
            self.to_event_queue(hold_event, pos)
            self.to_event_queue(down_event, pos)
            self.is_mouse_pressed.add(hold_event)
            return

        wheel_event = self._MOUSE_WHEEL_EVENT_MAP.get(event.button)
        if wheel_event is not None:
            self.to_event_queue(wheel_event, pos)

    def put_mouse_up_in_event_queue(self, event):
        """function is called in 'pygame_events_to_event_queue"""
        pos = self._get_mouse_pos(event)
        mouse_events = self._MOUSE_UP_EVENT_MAP.get(event.button)
        if mouse_events is None:
            return

        hold_event, up_event = mouse_events
        self.to_event_queue(up_event, pos)
        self.is_mouse_pressed.discard(hold_event)
