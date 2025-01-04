import collections
import inspect
import logging
from collections import defaultdict
from typing import Any, Optional

import miniworlds.tools.method_caller as method_caller
import miniworlds.actors.actor as actor_mod
from miniworlds.base.exceptions import MissingActorPartsError

class EventHandler:

    def __init__(self, world, registry):
        self.world = world
        self.event_registry = registry
        self.focus_actor: Optional[actor_mod.Actor] = None
        self._last_focus_actor = None
        self.executed_events: set = set()

    def act_all(self):
        registered_act_methods = self.event_registry.registered_events["act"].copy()
        # acting
        for method in registered_act_methods:
            # act method
            instance = method.__self__
            if instance._is_acting:
                method_caller.call_method(method, None, False)
        del registered_act_methods

    def handle_event(self, event: str, data: Any):
        """Call specific event handlers (e.g. "on_mouse_left", "on_mouse_right", ...) for actors

        Args:
            event: A string-identifier for the event, e.g. `reset`, `setup`, `switch_world`
            data: Data for the event, e.g. the mouse-position, the pressed key, ...
        """

        event = "on_" + event
        if not self.can_handle_event(event):
            return
        # Handle different events
        self.executed_events.add(event)
        if event in [
            "on_mouse_left",
            "on_mouse_right",
            "on_mouse_left_released",
            "on_mouse_right_released",
            "on_mouse_motion",
            "on_clicked_left",
            "on_clicked_right",
            "on_mouse_leave",
        ]:
            return self.handle_mouse_event(event, data)
        if event.startswith("on_key"):
            return self.handle_key_event(event, data)
        if event == "on_message":
            return self.handle_message_event(event, data)
        if event == "on_sensor":
            return self.handle_message_event(event, data)
        # If none of the events above is triggered, handle
        # all other events in a default way.
        return self.default_event_handler(event, data)

    def default_event_handler(self, event: str, data: Any):
        registered_events = self.event_registry.registered_events[event].copy()
        for method in registered_events:
            if type(data) in [list, str, tuple]:
                if type(data) == tuple and not self.world.camera.get_screen_rect().collidepoint(data):
                    return
                data = [data]
            method_caller.call_method(method, data, allow_none=False)
        registered_events.clear()
        del registered_events

    def can_handle_event(self, event):
        """ True, if event can be auto handled.
        False, if event needs manual handling."""
        if event == "setup":
            return False # Setup is not handled by event manager
        if event in self.executed_events:
            return False # events shouldn't be called more than once per tick
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
        if not self.event_registry.registered_events["message"] == set():
            message_methods = self.event_registry.registered_events["message"][data]
            # if message_dict == set():
            #   return
            for method in message_methods:
                method_caller.call_method(method, (data,))
        else:
            message_methods = self.event_registry.registered_events["on_message"]
            for method in message_methods:
                # Handle on_key_down, on_key_pressed, ....
                if event == method.__name__:
                    method_caller.call_method(method, (data,))

    def handle_key_event(self, event, data):
        key_methods = (
            self.event_registry.registered_events["on_key_down"]
            .copy()
            .union(self.event_registry.registered_events["on_key_up"].copy())
            .union(self.event_registry.registered_events["on_key_pressed"].copy())
        )
        # collect specific items:
        specific_key_methods = set()
        for e, values in self.event_registry.registered_events.items():
            if e.startswith("on_key_down_"):
                specific_key_methods = specific_key_methods.union(values)
            if e.startswith("on_key_pressed_"):
                specific_key_methods = specific_key_methods.union(values)
            if e.startswith("on_key_up_"):
                specific_key_methods = specific_key_methods.union(values)
        for method in key_methods:
            # Handle on_key_down, on_key_pressed, ....
            if event == method.__name__:
                method_caller.call_method(method, (data,))
        # Handle on_key_pressed_w, on_key_pressed_a, ....
        for method in specific_key_methods:
            if method.__name__ == event:
                method_caller.call_method(method, None)

    def handle_mouse_event(self, event, data):
        if not self.world.camera.is_in_screen(data):
            return False
        mouse_methods = set()
        for e, values in self.event_registry.registered_events.items():
            if e == event:
                mouse_methods = mouse_methods.union(values)
        for method in mouse_methods:
            method_caller.call_method(method, (data,))
        # Handle additional events like clicked on actor or mouse mouse over
        if event in ["on_mouse_motion"]:
            return self.handle_mouse_over_event(event, data)
        if event in ["on_mouse_left", "on_mouse_right"]:
            self.handle_click_on_actor_event(event, data)

    def handle_mouse_over_event(self, event, data):
        if not self.world.camera.is_in_screen(data):
            return False
        pos = self.world.camera.get_global_coordinates_for_world(
            data
        )  # get global mouse pos by window
        all_mouse_over_methods = (
            self.event_registry.registered_events["on_mouse_over"]
            .union(self.event_registry.registered_events["on_mouse_enter"])
            .union(self.event_registry.registered_events["on_mouse_leave"].copy())
        )
        mouse_over_methods = self.event_registry.registered_events["on_mouse_over"]
        if not all_mouse_over_methods:
            return
        for method in all_mouse_over_methods:
            break  # get the first method
        actor = method.__self__

        if not hasattr(actor, "_mouse_over"):
            actor._mouse_over = False
        # Store state in actor._mouse over -> Call handle_mouse_enter and mouse_event methods
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
        # Handle the mouse over
        if actor._mouse_over:
            for method in mouse_over_methods:
                method_caller.call_method(method, (data,))
        del mouse_over_methods

    def handle_mouse_enter_event(self, event, data):
        mouse_over_methods = self.event_registry.registered_events["on_mouse_enter"].copy()
        for method in mouse_over_methods:
            method_caller.call_method(method, (data,))

    def handle_mouse_leave_event(self, event, data):
        mouse_over_methods = self.event_registry.registered_events["on_mouse_leave"].copy()
        for method in mouse_over_methods:
            method_caller.call_method(method, (data,))

    def handle_click_on_actor_event(self, event, data):
        """handles specific methods ``on_clicked_left``,``on_clicked_left``,
        which are called, if actor is detecting mouse position
        """
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
