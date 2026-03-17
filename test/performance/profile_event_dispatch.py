import time
from collections import defaultdict
from types import SimpleNamespace

import pygame

from miniworlds.base.manager.app_event_manager import AppEventManager
from miniworlds.worlds.manager.event_sensor_dispatcher import EventSensorDispatcher
from miniworlds.worlds.manager.event_handler import EventHandler
from logic_benchmark_utils import record_measurement_summary


class Recorder:
    def __init__(self):
        self._mouse_over = False

    def on_key_down(self, keys):
        return keys

    def on_key_down_a(self):
        return None

    def on_message_saved(self, message):
        return message

    def on_mouse_enter(self, position):
        return position

    def on_mouse_over(self, position):
        return position

    def detect_pixel(self, position):
        return True


class SensorRecorder:
    def __init__(self):
        self.sensor_manager = SimpleNamespace(detect_actors=lambda filter: [object()])

    def on_sensor_saved(self, target):
        return target


class DummyPlatform:
    def __init__(self, events, mouse_pos=(10, 10)):
        self._events = events
        self._mouse_pos = mouse_pos

    def poll_events(self):
        return list(self._events)

    def get_mouse_pos(self):
        return self._mouse_pos


def create_world():
    camera = SimpleNamespace(
        is_in_screen=lambda position: True,
        screen_rect=SimpleNamespace(collidepoint=lambda position: True),
        get_global_coordinates_for_world=lambda position: position,
    )
    return SimpleNamespace(camera=camera, detect_actors=lambda position: [])


def profile_event_dispatch(iterations: int = 50000):
    recorder = Recorder()
    second_recorder = Recorder()
    registry = SimpleNamespace(registered_events=defaultdict(set))
    registry.registered_events["on_key_down"].add(recorder.on_key_down)
    registry.registered_events["on_key_down_a"].add(recorder.on_key_down_a)
    registry.registered_events["message"] = defaultdict(set, {"saved": {recorder.on_message_saved}})
    registry.registered_events["on_mouse_over"] = {recorder.on_mouse_over, second_recorder.on_mouse_over}
    registry.registered_events["on_mouse_enter"] = {recorder.on_mouse_enter, second_recorder.on_mouse_enter}
    handler = EventHandler(create_world(), registry)

    start = time.perf_counter()
    for _ in range(iterations):
        handler.handle_event("key_down_a", ["a"])
        handler.executed_events.clear()
    key_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iterations):
        handler.handle_event("message", "saved")
        handler.executed_events.clear()
    message_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iterations):
        recorder._mouse_over = False
        second_recorder._mouse_over = False
        handler.handle_event("mouse_motion", (5, 5))
        handler.executed_events.clear()
    hover_elapsed = time.perf_counter() - start

    sensor_actor = SensorRecorder()
    sensor_method = sensor_actor.on_sensor_saved
    sensor_view = SimpleNamespace(iter_sensor_methods=lambda: [("saved", (sensor_method,))])
    sensor_dispatcher = EventSensorDispatcher(sensor_view)

    start = time.perf_counter()
    for _ in range(iterations):
        sensor_dispatcher.dispatch()
    sensor_elapsed = time.perf_counter() - start

    app = SimpleNamespace(
        platform=DummyPlatform(
            [
                pygame.event.Event(pygame.KEYDOWN, {"unicode": "a", "key": pygame.K_a}),
                pygame.event.Event(pygame.MOUSEMOTION, {"pos": (5, 5)}),
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}),
            ]
        ),
        worlds_manager=SimpleNamespace(worlds=[]),
        quit=lambda: None,
        add_display_to_repaint_areas=lambda: None,
    )
    app_event_manager = AppEventManager(app)

    start = time.perf_counter()
    for _ in range(iterations):
        app_event_manager.event_queue.clear()
        app_event_manager.is_key_pressed.clear()
        app_event_manager.is_mouse_pressed.clear()
        app_event_manager.pygame_events_to_event_queue()
    queue_elapsed = time.perf_counter() - start

    print(
        f"event dispatch: {iterations} key events in {key_elapsed * 1000:.2f} ms "
        f"({iterations / key_elapsed:.0f} events/s)"
    )
    print(
        f"event dispatch: {iterations} message events in {message_elapsed * 1000:.2f} ms "
        f"({iterations / message_elapsed:.0f} events/s)"
    )
    print(
        f"event dispatch: {iterations} hover events in {hover_elapsed * 1000:.2f} ms "
        f"({iterations / hover_elapsed:.0f} events/s)"
    )
    print(
        f"event dispatch: {iterations} sensor dispatches in {sensor_elapsed * 1000:.2f} ms "
        f"({iterations / sensor_elapsed:.0f} events/s)"
    )
    print(
        f"event dispatch: {iterations} pygame queue translations in {queue_elapsed * 1000:.2f} ms "
        f"({iterations / queue_elapsed:.0f} events/s)"
    )
    record_measurement_summary(
        "event dispatch",
        {
            "iterations": iterations,
            "key_events_ms": round(key_elapsed * 1000, 4),
            "key_events_per_s": round(iterations / key_elapsed, 4),
            "message_events_ms": round(message_elapsed * 1000, 4),
            "message_events_per_s": round(iterations / message_elapsed, 4),
            "hover_events_ms": round(hover_elapsed * 1000, 4),
            "hover_events_per_s": round(iterations / hover_elapsed, 4),
            "sensor_dispatches_ms": round(sensor_elapsed * 1000, 4),
            "sensor_dispatches_per_s": round(iterations / sensor_elapsed, 4),
            "queue_translations_ms": round(queue_elapsed * 1000, 4),
            "queue_translations_per_s": round(iterations / queue_elapsed, 4),
        },
    )


if __name__ == "__main__":
    profile_event_dispatch()