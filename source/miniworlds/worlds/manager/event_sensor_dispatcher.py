from __future__ import annotations

import miniworlds.tools.method_caller as method_caller


class EventSensorDispatcher:
    def __init__(self, event_view, detect=None):
        self.event_view = event_view
        # Optional detect(actor, target) callable. When given (e.g. by the
        # CollisionManager), filtered detection is derived from a per-frame
        # cached unfiltered result instead of re-running collision checks.
        self._detect = detect

    def dispatch(self) -> None:
        sensor_handlers = self.event_view.iter_sensor_methods()
        if not sensor_handlers:
            return

        for target, methods in sensor_handlers:
            for method in methods:
                actor = method.__self__
                if self._detect is not None:
                    found = self._detect(actor, target)
                else:
                    found = actor.sensor_manager.detect_actors(filter=target)
                if found:
                    method_caller.call_method(method, (target,))