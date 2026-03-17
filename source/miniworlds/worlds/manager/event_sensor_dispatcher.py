from __future__ import annotations

import miniworlds.tools.method_caller as method_caller


class EventSensorDispatcher:
    def __init__(self, event_view):
        self.event_view = event_view

    def dispatch(self) -> None:
        sensor_handlers = self.event_view.iter_sensor_methods()
        if not sensor_handlers:
            return

        for target, methods in sensor_handlers:
            for method in methods:
                actor = method.__self__
                if actor.sensor_manager.detect_actors(filter=target):
                    method_caller.call_method(method, (target,))