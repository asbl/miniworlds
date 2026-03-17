from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miniworlds.worlds.manager.event_manager import EventManager


class CollisionEventView:
    """Provides a read-only view over collision-related event registrations."""

    def __init__(self, event_manager: "EventManager"):
        self.event_manager = event_manager

    def iter_sensor_methods(self) -> list[tuple[str, tuple[Callable, ...]]]:
        return self.event_manager.registry.iter_sensor_methods()

    def iter_registered_methods(
        self, event_group: str
    ) -> list[tuple[str, tuple[Callable, ...]]]:
        class_events = self.event_manager.definition.class_events.get(event_group, set())
        return [
            (event_name, tuple(self.event_manager.registry.copy_event_methods(event_name)))
            for event_name in class_events
        ]

    def copy_registered_methods(self, event_name: str) -> set[Callable]:
        return self.event_manager.registry.copy_event_methods(event_name)