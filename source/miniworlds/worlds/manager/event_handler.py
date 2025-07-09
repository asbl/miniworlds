import collections
import inspect
import logging
from collections import defaultdict
from typing import Any, Optional

import miniworlds.tools.method_caller as method_caller
import miniworlds.actors.actor as actor_mod
from miniworlds.base.exceptions import MissingActorPartsError

class EventHandler:
    """
    Handles all events (keyboard, mouse, message, etc.) for the game world.
    Uses an event registry to dispatch to the appropriate bound methods.
    """

    def __init__(self, world, registry):
        """Initialize with a reference to the world and the event registry."""
        self.world = world
        self.event_registry = registry
        self.focus_actor: Optional[actor_mod.Actor] = None
        self._last_focus_actor = None
        self.executed_events: set = set()
        # Dispatch map for fast event routing
        self._event_dispatch_map = {}
        self._key_event_prefixes = ()
        self._init_event_dispatch_map()


    def _init_event_dispatch_map(self):
        """
        Initializes the static event-to-handler dispatch map.
        """
        mouse_events = {
            "on_mouse_left",
            "on_mouse_right",
            "on_mouse_left_down",
            "on_mouse_right_down",
            "on_mouse_left_up",
            "on_mouse_right_up",
            "on_mouse_motion",
            "on_clicked_left",
            "on_clicked_right",
            "on_mouse_leave",
        }

        # Register mouse events
        self._event_dispatch_map = {event: self.handle_mouse_event for event in mouse_events}

        # Register special events like messages or sensors
        self._event_dispatch_map.update({
            "on_message": self.handle_message_event,
            "on_sensor": self.handle_message_event,
        })

        # Register key prefixes to handle dynamic key events
        self._key_event_prefixes = ("on_key_down", "on_key_up", "on_key_pressed")

    def act_all(self):
        """Calls all registered 'act' methods for actors currently acting."""
        registered_act_methods = self.event_registry.registered_events["act"].copy()
        for method in registered_act_methods:
            instance = method.__self__
            if instance._is_acting:
                method_caller.call_method(method, None, False)
        del registered_act_methods

    def handle_event(self, event: str, data: Any):
        """
        Main dispatcher for all event types using a dispatch map.
        Tries to route the event to a specific handler function, otherwise falls back to the default handler.
        """
        event = f"on_{event}"

        if not self.can_handle_event(event):
            return

        self.executed_events.add(event)

        # Direct dispatch if a handler is registered for this event
        handler = self._event_dispatch_map.get(event)
        if handler:
            return handler(event, data)

        # Handle dynamic key events (e.g. on_key_down_w)
        if event.startswith(self._key_event_prefixes):
            return self.handle_key_event(event, data)

        # Fall back to default event handler
        return self.default_event_handler(event, data)

    def default_event_handler(self, event: str, data: Any):
        """Handles any generic events that are not mouse, key or message events."""
        registered_events = self.event_registry.registered_events[event].copy()
        for method in registered_events:
            if type(data) in [list, str, tuple]:
                if type(data) == tuple and not self.world.camera.screen_rect.collidepoint(data):
                    return
                data = [data]
            method_caller.call_method(method, data, allow_none=False)
        registered_events.clear()
        del registered_events

    def can_handle_event(self, event):
        """Checks whether the event should be handled automatically by the event system."""
        if event == "setup":
            return False
        if event in self.executed_events:
            return False
        registered_event_keys = self.event_registry.registered_events.keys()
        if (
                event not in registered_event_keys
                and not event.startswith("on_key_down_")
                and not event.startswith("on_key_pressed_")
                and not event.startswith("on_key_up_")
                and not event.startswith("on_mouse_left_")
                and "on_clicked_left" in registered_event_keys
                and not event.startswith("on_mouse_right_")
                and "on_clicked_right" in registered_event_keys
                and not event.startswith("on_mouse_motion")
                and "on_mouse enter" in registered_event_keys
                and not event.startswith("on_mouse_motion")
                and "on_mouse_leave" in registered_event_keys
        ):
            return False
        else:
            return True

    def handle_message_event(self, event, data):
        """Handles 'on_message' or 'message' events by calling registered message handlers."""
        if not self.event_registry.registered_events["message"] == set():
            message_methods = self.event_registry.registered_events["message"][data]
            for method in message_methods:
                method_caller.call_method(method, (data,))
        else:
            message_methods = self.event_registry.registered_events["on_message"]
            for method in message_methods:
                if event == method.__name__:
                    method_caller.call_method(method, (data,))

    def handle_key_event(self, event, data):
        """Dispatches key events (e.g. on_key_down, on_key_pressed_w, etc.) to matching methods."""
        key_methods = (
            self.event_registry.registered_events["on_key_down"]
            .copy()
            .union(self.event_registry.registered_events["on_key_up"].copy())
            .union(self.event_registry.registered_events["on_key_pressed"].copy())
        )
        specific_key_methods = set()
        for e, values in self.event_registry.registered_events.items():
            if e.startswith("on_key_down_"):
                specific_key_methods = specific_key_methods.union(values)
            if e.startswith("on_key_pressed_"):
                specific_key_methods = specific_key_methods.union(values)
            if e.startswith("on_key_up_"):
                specific_key_methods = specific_key_methods.union(values)
        for method in key_methods:
            if event == method.__name__:
                method_caller.call_method(method, (data,))
        for method in specific_key_methods:
            if method.__name__ == event:
                method_caller.call_method(method, None)

    def handle_mouse_event(self, event, mouse_pos):
        """Handles mouse-related events (clicks, motion, etc.)."""
        if not self.world.camera.is_in_screen(mouse_pos):
            return False
        mouse_methods = set()
        for e, values in self.event_registry.registered_events.items():
            if e == event:
                mouse_methods = mouse_methods.union(values)
        for method in mouse_methods:
            method_caller.call_method(method, (mouse_pos,))
        if event in ["on_mouse_motion"]:
            return self.handle_mouse_over_event(event, mouse_pos)
        if event in ["on_mouse_left", "on_mouse_right"]:
            self.handle_click_on_actor_event(event, mouse_pos)

    def handle_mouse_over_event(self, event, data):
        """Handles mouse-over and hover-related events for actors."""
        if not self.world.camera.is_in_screen(data):
            return False
        pos = self.world.camera.get_global_coordinates_for_world(data)
        all_mouse_over_methods = (
            self.event_registry.registered_events["on_mouse_over"]
            .union(self.event_registry.registered_events["on_mouse_enter"])
            .union(self.event_registry.registered_events["on_mouse_leave"].copy())
        )
        mouse_over_methods = self.event_registry.registered_events["on_mouse_over"]
        if not all_mouse_over_methods:
            return
        for method in all_mouse_over_methods:
            break
        actor = method.__self__
        if not hasattr(actor, "_mouse_over"):
            actor._mouse_over = False
        is_detecting_pixel = actor.detect_pixel(pos)
        if is_detecting_pixel and not actor._mouse_over:
            self.handle_mouse_enter_event(event, data)
            actor._mouse_over = True
        elif not is_detecting_pixel and actor._mouse_over:
            self.handle_mouse_leave_event(event, data)
            actor._mouse_over = False
        elif is_detecting_pixel:
            actor._mouse_over = True
        else:
            actor._mouse_over = False
        if actor._mouse_over:
            for method in mouse_over_methods:
                method_caller.call_method(method, (data,))
        del mouse_over_methods

    def handle_mouse_enter_event(self, event, data):
        """Calls all registered 'on_mouse_enter' methods for matching actors."""
        mouse_over_methods = self.event_registry.registered_events["on_mouse_enter"].copy()
        for method in mouse_over_methods:
            method_caller.call_method(method, (data,))

    def handle_mouse_leave_event(self, event, data):
        """Calls all registered 'on_mouse_leave' methods for matching actors."""
        mouse_over_methods = self.event_registry.registered_events["on_mouse_leave"].copy()
        for method in mouse_over_methods:
            method_caller.call_method(method, (data,))

    def handle_click_on_actor_event(self, event, data):
        """Handles actor-specific click detection and dispatches 'on_clicked' events."""
        pos = data
        if event == "on_mouse_left":
            on_click_methods = (
                self.event_registry.registered_events["on_clicked_left"]
                .union(self.event_registry.registered_events["on_clicked"])
                .copy()
            )
        elif event == "on_mouse_right":
            on_click_methods = (
                self.event_registry.registered_events["on_clicked_right"]
                .union(self.event_registry.registered_events["on_clicked"])
                .copy()
            )
        else:
            return
        for method in on_click_methods:
            actor = method.__self__
            try:
                if actor.detect_pixel(pos):
                    method_caller.call_method(method, (data,))
            except MissingActorPartsError:
                logging.info("Warning: Actor parts missing from: ", actor.actor_id)
        del on_click_methods
        actors = self.world.detect_actors(pos)
        self.call_focus_methods(actors)

    def set_new_focus(self, actors):
        """Sets the focus_actor based on which actor was clicked or hovered."""
        self._last_focus_actor = self.focus_actor
        if self._last_focus_actor:
            self._last_focus_actor.has_focus = False
        if actors:
            for actor in actors:
                if actor.is_focusable:
                    self.focus_actor = actor
                    actor.has_focus = True
                    return actor
        self.focus_actor = None

    def call_focus_methods(self, actors: list):
        """Handles 'on_focus' and 'on_focus_lost' for actors gaining or losing focus."""
        focus_methods = self.event_registry.registered_events["on_focus"].copy()
        unfocus_methods = self.event_registry.registered_events["on_focus_lost"].copy()
        self.set_new_focus(actors)
        if self.focus_actor:
            for method in focus_methods:
                if (
                        self.focus_actor == method.__self__
                        and self.focus_actor != self._last_focus_actor
                ):
                    self.focus_actor.focus = True
                    method_caller.call_method(method, None)
        for method in unfocus_methods:
            if (
                    self._last_focus_actor == method.__self__
                    and self.focus_actor != self._last_focus_actor
            ):
                self._last_focus_actor.focus = False
                method_caller.call_method(method, None)
