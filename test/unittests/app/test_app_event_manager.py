import unittest
from collections import deque
from types import SimpleNamespace
from unittest.mock import Mock

import pygame

from miniworlds.base.manager.app_event_manager import AppEventManager


class DummyPlatform:
    def __init__(self, events=None, mouse_pos=(10, 20)):
        self._events = events or []
        self._mouse_pos = mouse_pos

    def poll_events(self):
        return list(self._events)

    def get_mouse_pos(self):
        return self._mouse_pos


class TestAppEventManager(unittest.TestCase):
    def _create_app(self, events=None):
        listening_world = SimpleNamespace(is_listening=True, _mainloop=SimpleNamespace(handle_event=Mock()))
        silent_world = SimpleNamespace(is_listening=False, _mainloop=SimpleNamespace(handle_event=Mock()))
        app = SimpleNamespace(
            platform=DummyPlatform(events=events),
            worlds_manager=SimpleNamespace(worlds=[listening_world, silent_world]),
            quit=Mock(),
            add_display_to_repaint_areas=Mock(),
        )
        return app, listening_world, silent_world

    def test_handle_event_queue_routes_only_to_listening_worlds(self):
        app, listening_world, silent_world = self._create_app()
        manager = AppEventManager(app)
        manager.event_queue = deque([("key_down", ["a"])])

        manager.handle_event_queue()

        listening_world._mainloop.handle_event.assert_called_once_with("key_down", ["a"])
        silent_world._mainloop.handle_event.assert_not_called()

    def test_pygame_events_create_middle_mouse_down_and_up_events(self):
        events = [
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 2}),
            pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 2}),
        ]
        app, _, _ = self._create_app(events=events)
        manager = AppEventManager(app)

        manager.pygame_events_to_event_queue()

        queue_entries = list(manager.event_queue)
        self.assertIn(("mouse_middle", (10, 20)), queue_entries)
        self.assertIn(("mouse_middle_down", (10, 20)), queue_entries)
        self.assertIn(("mouse_middle_up", (10, 20)), queue_entries)

    def test_pygame_events_use_native_mouse_position_when_available(self):
        events = [
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (11, 12)}),
            pygame.event.Event(pygame.MOUSEMOTION, {"pos": (13, 14)}),
            pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (15, 16)}),
        ]
        app, _, _ = self._create_app(events=events)
        manager = AppEventManager(app)

        manager.pygame_events_to_event_queue()

        queue_entries = list(manager.event_queue)
        self.assertIn(("mouse_left", (11, 12)), queue_entries)
        self.assertIn(("mouse_left_down", (11, 12)), queue_entries)
        self.assertIn(("mouse_motion", (13, 14)), queue_entries)
        self.assertIn(("mouse_left_up", (15, 16)), queue_entries)

    def test_pygame_events_emit_specific_event_for_named_special_keys(self):
        events = [
            pygame.event.Event(pygame.KEYDOWN, {"unicode": "", "key": pygame.K_PAGEUP}),
        ]
        app, _, _ = self._create_app(events=events)
        manager = AppEventManager(app)

        manager.pygame_events_to_event_queue()

        queue_entries = list(manager.event_queue)
        self.assertIn(("key_down", ["page_up"]), queue_entries)
        self.assertIn(("key_down_page_up", None), queue_entries)
        self.assertIn(("key_pressed", ["page_up"]), queue_entries)
        self.assertIn(("key_pressed_page_up", None), queue_entries)

    def test_pygame_events_emit_normalized_specific_event_for_held_space(self):
        events = [
            pygame.event.Event(pygame.KEYDOWN, {"unicode": " ", "key": pygame.K_SPACE}),
        ]
        app, _, _ = self._create_app(events=events)
        manager = AppEventManager(app)

        manager.pygame_events_to_event_queue()

        queue_entries = list(manager.event_queue)
        self.assertIn(("key_down_space", None), queue_entries)
        self.assertIn(("key_pressed_space", None), queue_entries)


if __name__ == "__main__":
    unittest.main()