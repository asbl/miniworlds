from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock


def _apply_overrides(namespace: SimpleNamespace, **overrides: Any) -> SimpleNamespace:
    for name, value in overrides.items():
        setattr(namespace, name, value)
    return namespace


def make_app_with_event_queue(**overrides: Any) -> SimpleNamespace:
    app = SimpleNamespace(
        event_manager=SimpleNamespace(
            event_queue=[],
            to_event_queue=Mock(),
        )
    )
    return _apply_overrides(app, **overrides)


def make_camera(**overrides: Any) -> SimpleNamespace:
    camera = SimpleNamespace(
        is_in_screen=Mock(return_value=True),
        screen_rect=SimpleNamespace(collidepoint=Mock(return_value=True)),
        get_global_coordinates_for_world=Mock(side_effect=lambda position: position),
    )
    return _apply_overrides(camera, **overrides)


def make_registered_events(initial: dict[str, Any] | None = None):
    registered_events = defaultdict(set)
    if initial is None:
        return registered_events

    for event_name, value in initial.items():
        if isinstance(value, dict) and not isinstance(value, defaultdict):
            registered_events[event_name] = defaultdict(set, value)
        else:
            registered_events[event_name] = value
    return registered_events


class FakeEventRegistry:
    """Test double for the internal event-registry API used by dispatcher tests."""

    def __init__(self, initial: dict[str, Any] | None = None):
        self.registered_events = make_registered_events(initial)
        self.change_counter = 0

    def copy_event_methods(self, event_name: str):
        methods = self.registered_events.get(event_name, set())
        return methods.copy() if isinstance(methods, set) else set()

    def copy_message_methods(self, message: str):
        message_registry = self.registered_events.get("message")
        if not isinstance(message_registry, dict):
            return set()
        methods = message_registry.get(message, set())
        return methods.copy() if isinstance(methods, set) else set()

    def copy_generic_message_methods(self):
        return self.copy_event_methods("on_message")

    def iter_sensor_methods(self):
        sensor_registry = self.registered_events.get("sensor")
        if not isinstance(sensor_registry, dict):
            return []
        return [
            (target, tuple(methods.copy()))
            for target, methods in sensor_registry.items()
        ]

    def registered_event_names(self):
        return set(self.registered_events.keys())


def make_event_registry(initial: dict[str, Any] | None = None) -> SimpleNamespace:
    return FakeEventRegistry(initial)


def make_event_handler_world(**overrides: Any) -> SimpleNamespace:
    world = SimpleNamespace(
        camera=make_camera(),
        detect_actors=Mock(return_value=[]),
    )
    return _apply_overrides(world, **overrides)


def make_collision_world(
    registered_events: dict[str, Any] | None = None,
    class_events: dict[str, set[Any]] | None = None,
    copy_registered_events=None,
    **overrides: Any,
) -> SimpleNamespace:
    registry = make_event_registry(registered_events)
    if not isinstance(registry.registered_events.get("sensor"), dict):
        registry.registered_events["sensor"] = defaultdict(set)

    definition = SimpleNamespace(
        class_events={
            "on_detecting": set(),
            "on_not_detecting": set(),
            "border": set(),
        }
    )
    if class_events:
        definition.class_events.update(class_events)

    world = SimpleNamespace(
        event_manager=SimpleNamespace(
            registry=registry,
            definition=definition,
            copy_registered_events=copy_registered_events or Mock(return_value=set()),
        )
    )
    return _apply_overrides(world, **overrides)


def make_mouse_world(active_world=None, **overrides: Any) -> SimpleNamespace:
    worlds_manager = SimpleNamespace(get_world_by_pixel=Mock())
    world = SimpleNamespace(app=SimpleNamespace(worlds_manager=worlds_manager))
    worlds_manager.get_world_by_pixel.return_value = active_world if active_world is not None else world
    return _apply_overrides(world, **overrides)


def make_worlds_manager_app(**overrides: Any) -> SimpleNamespace:
    app = SimpleNamespace(
        window=Mock(),
        running_worlds=[],
        running_world=None,
    )
    app.add_running_world = Mock(
        side_effect=lambda world: app.running_worlds.append(world)
        if world not in app.running_worlds
        else None
    )
    app.remove_running_world = Mock(
        side_effect=lambda world: app.running_worlds.remove(world)
        if world in app.running_worlds
        else None
    )
    app.set_running_world = Mock(
        side_effect=lambda world: setattr(app, "running_world", world)
    )
    app.resize = Mock()
    app.prepare_mainloop = Mock()
    return _apply_overrides(app, **overrides)


def make_managed_world(frame: int = 0, **overrides: Any) -> SimpleNamespace:
    world = SimpleNamespace(
        stop=Mock(),
        _stop_listening=Mock(),
        app=make_app_with_event_queue(),
        backgrounds=SimpleNamespace(_init_display=Mock()),
        background=SimpleNamespace(set_dirty=Mock()),
        camera=SimpleNamespace(_disable_resize=Mock(), _enable_resize=Mock()),
        _mainloop=SimpleNamespace(dirty_all=Mock()),
        _default_start_running=True,
        frame=frame,
        is_running=False,
        _is_setup_completed=False,
        on_setup=Mock(),
        _start_listening=Mock(),
        on_change=Mock(),
        _layout=SimpleNamespace(docking_position="top_left"),
        reset=Mock(),
        dirty=0,
    )
    return _apply_overrides(world, **overrides)