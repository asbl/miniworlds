import logging
from collections import defaultdict
from typing import Any, Optional

import miniworlds.tools.method_caller as method_caller
import miniworlds.actors.actor as actor_mod
from miniworlds.base.exceptions import MissingActorPartsError
from miniworlds.worlds.manager.event_message_dispatcher import EventMessageDispatcher


logger = logging.getLogger(__name__)


class _KeyEventDispatcher:
    """Routes specific and generic keyboard events to registered handlers."""

    def __init__(self, event_registry):
        self.event_registry = event_registry

    def dispatch(self, event: str, data: Any, generic_event: Optional[str]) -> None:
        if generic_event is None:
            return

        if data is not None:
            for method in self.event_registry.copy_event_methods(generic_event):
                method_caller.call_method(method, (data,))

        if event != generic_event:
            for method in self.event_registry.copy_event_methods(event):
                method_caller.call_method(method, None)


class _MouseEventDispatcher:
    """Handles mouse, click, hover, and focus-related dispatch for a world."""

    _HOVER_EVENT_NAMES = ("on_mouse_over", "on_mouse_enter", "on_mouse_leave")
    _CLICK_EVENT_NAMES = {
        "on_mouse_left": "on_clicked_left",
        "on_mouse_right": "on_clicked_right",
    }

    def __init__(self, world, event_registry, focus_callback):
        self.world = world
        self.event_registry = event_registry
        self.focus_callback = focus_callback
        self._hover_methods_by_actor_cache = None
        self._hover_cache_token = None

    def dispatch(self, event: str, mouse_pos: Any):
        if not self.world.camera.is_in_screen(mouse_pos):
            return False

        self._call_mouse_methods(self.event_registry.copy_event_methods(event), mouse_pos)
        if event == "on_mouse_motion":
            return self.handle_mouse_over_event(mouse_pos, skip_screen_check=True)
        if event in self._CLICK_EVENT_NAMES:
            self.handle_click_on_actor_event(event, mouse_pos)

    def handle_mouse_over_event(self, data: Any, skip_screen_check: bool = False):
        if not skip_screen_check and not self.world.camera.is_in_screen(data):
            return False

        pos = self.world.camera.get_global_coordinates_for_world(data)
        hover_methods_by_actor = self._get_hover_methods_by_actor()
        if not hover_methods_by_actor:
            return

        for actor, methods_by_event in hover_methods_by_actor.items():
            was_mouse_over = getattr(actor, "_mouse_over", False)
            try:
                is_detecting_pixel = actor.detect_pixel(pos)
            except MissingActorPartsError:
                logger.info(
                    "Skipping hover dispatch for incomplete actor %s",
                    getattr(actor, "actor_id", actor),
                )
                continue

            if is_detecting_pixel and not was_mouse_over:
                self._call_mouse_methods(methods_by_event["on_mouse_enter"], data)
                actor._mouse_over = True
            elif not is_detecting_pixel and was_mouse_over:
                self._call_mouse_methods(methods_by_event["on_mouse_leave"], data)
                actor._mouse_over = False
            else:
                actor._mouse_over = is_detecting_pixel

            if actor._mouse_over:
                self._call_mouse_methods(methods_by_event["on_mouse_over"], data)

    def handle_mouse_enter_event(self, data: Any):
        self._call_registered_mouse_methods("on_mouse_enter", data)

    def handle_mouse_leave_event(self, data: Any):
        self._call_registered_mouse_methods("on_mouse_leave", data)

    def handle_click_on_actor_event(self, event: str, data: Any):
        specific_click_event = self._CLICK_EVENT_NAMES.get(event)
        if specific_click_event is None:
            return

        on_click_methods = (
            self.event_registry.copy_event_methods(specific_click_event)
            .union(self.event_registry.copy_event_methods("on_clicked"))
        )
        for method in on_click_methods:
            actor = method.__self__
            try:
                if actor.detect_pixel(data):
                    method_caller.call_method(method, (data,))
            except MissingActorPartsError:
                logger.info(
                    "Skipping click dispatch for incomplete actor %s",
                    getattr(actor, "actor_id", actor),
                )
        actors = self.world.detect_actors(data)
        self.focus_callback(actors)

    def _call_registered_mouse_methods(self, event_name: str, data: Any) -> None:
        self._call_mouse_methods(self.event_registry.copy_event_methods(event_name), data)

    def _call_mouse_methods(self, mouse_methods, data: Any) -> None:
        for method in mouse_methods:
            method_caller.call_method(method, (data,))

    def _get_hover_cache_token(self):
        return getattr(self.event_registry, "change_counter", None)

    def _build_hover_methods_by_actor(self):
        methods_by_actor = defaultdict(
            lambda: {
                "on_mouse_over": [],
                "on_mouse_enter": [],
                "on_mouse_leave": [],
            }
        )
        for event_name in self._HOVER_EVENT_NAMES:
            for method in self.event_registry.copy_event_methods(event_name):
                methods_by_actor[method.__self__][event_name].append(method)
        return {
            actor: {
                event_name: tuple(methods)
                for event_name, methods in method_groups.items()
            }
            for actor, method_groups in methods_by_actor.items()
        }

    def _get_hover_methods_by_actor(self):
        cache_token = self._get_hover_cache_token()
        if cache_token is None:
            return self._build_hover_methods_by_actor()

        if self._hover_methods_by_actor_cache is None or cache_token != self._hover_cache_token:
            self._hover_methods_by_actor_cache = self._build_hover_methods_by_actor()
            self._hover_cache_token = cache_token
        return self._hover_methods_by_actor_cache


class EventHandler:
    """Dispatches world events to the specialized mouse, key, and message handlers."""

    _KEY_EVENT_PREFIX_MAP = {
        "down": "on_key_down",
        "pressed": "on_key_pressed",
        "up": "on_key_up",
    }

    _MOUSE_EVENT_DEPENDENCIES = {
        "on_mouse_left": (
            "on_mouse_left",
            "on_clicked",
            "on_clicked_left",
            "on_focus",
            "on_focus_lost",
        ),
        "on_mouse_right": (
            "on_mouse_right",
            "on_clicked",
            "on_clicked_right",
            "on_focus",
            "on_focus_lost",
        ),
        "on_mouse_motion": (
            "on_mouse_motion",
            "on_mouse_over",
            "on_mouse_enter",
            "on_mouse_leave",
        ),
    }

    _EVENT_DEPENDENCIES = {
        "on_message": ("on_message", "message"),
        **_MOUSE_EVENT_DEPENDENCIES,
    }

    def __init__(self, world, registry):
        """Initialize with a reference to the world and the event registry."""
        self.world = world
        self.event_registry = registry
        self.focus_actor: Optional[actor_mod.Actor] = None
        self._last_focus_actor = None
        self.executed_events: set = set()
        # Dispatch map for fast event routing
        self._event_dispatch_map = {}
        self._message_dispatcher = EventMessageDispatcher(self.event_registry)
        self._key_dispatcher = _KeyEventDispatcher(self.event_registry)
        self._mouse_dispatcher = _MouseEventDispatcher(
            world,
            self.event_registry,
            self.call_focus_methods,
        )
        self._init_event_dispatch_map()


    def _init_event_dispatch_map(self):
        """
        Initializes the static event-to-handler dispatch map.
        """
        mouse_events = {
            "on_mouse_middle",
            "on_mouse_middle_down",
            "on_mouse_middle_up",
            "on_clicked_left",
            "on_clicked_right",
            "on_mouse_leave",
        }
        mouse_events.update(self._MOUSE_EVENT_DEPENDENCIES)
        mouse_events.update({
            "on_mouse_left_down",
            "on_mouse_right_down",
            "on_mouse_left_up",
            "on_mouse_right_up",
        })

        # Register mouse events
        self._event_dispatch_map = {event: self.handle_mouse_event for event in mouse_events}

        # Register special events like messages or sensors
        self._event_dispatch_map.update({
            "on_message": self.handle_message_event,
        })

    def act_all(self):
        """Calls all registered 'act' methods for actors currently acting."""
        registered_act_methods = self.event_registry.copy_event_methods("act")
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
        generic_key_event = self._get_generic_key_event(event)
        if generic_key_event is not None:
            return self.handle_key_event(event, data, generic_key_event)

        # Fall back to default event handler
        return self.default_event_handler(event, data)

    def default_event_handler(self, event: str, data: Any):
        """Handles any generic events that are not mouse, key or message events."""
        registered_events = self.event_registry.copy_event_methods(event)
        for method in registered_events:
            method_data = data
            if type(method_data) in [list, str, tuple]:
                if type(method_data) == tuple and not self.world.camera.screen_rect.collidepoint(method_data):
                    return
                method_data = [method_data]
            method_caller.call_method(method, method_data, allow_none=False)
        registered_events.clear()
        del registered_events

    def can_handle_event(self, event):
        """Checks whether the event should be handled automatically by the event system."""
        if event == "setup":
            return False
        if event in self.executed_events:
            return False
        registered_event_keys = self.event_registry.registered_event_names()
        if event in registered_event_keys:
            return True
        generic_key_event = self._get_generic_key_event(event)
        if generic_key_event is not None:
            return generic_key_event in registered_event_keys
        return self._has_registered_event_dependency(event, registered_event_keys)

    def _has_registered_event_dependency(self, event: str, registered_event_keys) -> bool:
        dependencies = self._EVENT_DEPENDENCIES.get(event)
        if dependencies is None:
            return False
        return any(key in registered_event_keys for key in dependencies)

    def handle_message_event(self, event, data):
        """Handles 'on_message' or 'message' events by calling registered message handlers."""
        return self._message_dispatcher.dispatch(event, data)

    def handle_key_event(self, event, data, generic_event: Optional[str] = None):
        """Dispatches key events (e.g. on_key_down, on_key_pressed_w, etc.) to matching methods."""
        if generic_event is None:
            generic_event = self._get_generic_key_event(event)
        return self._key_dispatcher.dispatch(event, data, generic_event)

    def handle_mouse_event(self, event, mouse_pos):
        """Handles mouse-related events (clicks, motion, etc.)."""
        return self._mouse_dispatcher.dispatch(event, mouse_pos)

    def handle_mouse_over_event(self, event, data):
        """Handles mouse-over and hover-related events for actors."""
        del event
        return self._mouse_dispatcher.handle_mouse_over_event(data)

    def _get_generic_key_event(self, event: str) -> Optional[str]:
        key_event_parts = event.split("_", 3)
        if len(key_event_parts) < 3 or key_event_parts[0] != "on" or key_event_parts[1] != "key":
            return None
        return self._KEY_EVENT_PREFIX_MAP.get(key_event_parts[2])

    def _call_registered_mouse_methods(self, event_name: str, data: Any):
        self._mouse_dispatcher._call_registered_mouse_methods(event_name, data)

    def _call_mouse_methods(self, mouse_methods, data: Any) -> None:
        self._mouse_dispatcher._call_mouse_methods(mouse_methods, data)

    def _get_hover_methods_by_actor(self):
        return self._mouse_dispatcher._get_hover_methods_by_actor()

    def handle_mouse_enter_event(self, event, data):
        """Calls all registered 'on_mouse_enter' methods for matching actors."""
        del event
        self._mouse_dispatcher.handle_mouse_enter_event(data)

    def handle_mouse_leave_event(self, event, data):
        """Calls all registered 'on_mouse_leave' methods for matching actors."""
        del event
        self._mouse_dispatcher.handle_mouse_leave_event(data)

    def handle_click_on_actor_event(self, event, data):
        """Handles actor-specific click detection and dispatches 'on_clicked' events."""
        return self._mouse_dispatcher.handle_click_on_actor_event(event, data)

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
        focus_methods = self.event_registry.copy_event_methods("on_focus")
        unfocus_methods = self.event_registry.copy_event_methods("on_focus_lost")
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
