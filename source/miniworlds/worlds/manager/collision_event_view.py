from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miniworlds.worlds.manager.event_manager import EventManager


class CollisionEventView:
    """Provides a read-only view over collision-related event registrations."""

    def __init__(self, event_manager: "EventManager"):
        self.event_manager = event_manager
        self._cache_key: tuple[int, tuple[tuple[str, tuple[str, ...]], ...]] | None = None
        self._group_cache: dict[str, tuple[tuple[str, tuple[Callable, ...]], ...]] = {}
        self._event_cache: dict[str, tuple[Callable, ...]] = {}
        self._sensor_cache: tuple[tuple[str, tuple[Callable, ...]], ...] | None = None

    def _current_cache_key(self) -> tuple[int, tuple[tuple[str, tuple[str, ...]], ...]]:
        registry_counter = getattr(self.event_manager.registry, "change_counter", 0)
        class_events = getattr(self.event_manager.definition, "class_events", {})
        event_signature = tuple(
            sorted((group, tuple(sorted(events))) for group, events in class_events.items())
        )
        return registry_counter, event_signature

    def _refresh_cache_if_needed(self) -> None:
        cache_key = self._current_cache_key()
        if cache_key == self._cache_key:
            return
        self._cache_key = cache_key
        self._group_cache.clear()
        self._event_cache.clear()
        self._sensor_cache = None

    def _iter_event_methods(self, event_name: str) -> tuple[Callable, ...]:
        self._refresh_cache_if_needed()
        if event_name not in self._event_cache:
            registry = self.event_manager.registry
            iter_event_methods = getattr(registry, "iter_event_methods", None)
            if callable(iter_event_methods):
                self._event_cache[event_name] = iter_event_methods(event_name)
            else:
                self._event_cache[event_name] = tuple(registry.copy_event_methods(event_name))
        return self._event_cache[event_name]

    def iter_sensor_methods(self) -> tuple[tuple[str, tuple[Callable, ...]], ...]:
        self._refresh_cache_if_needed()
        if self._sensor_cache is None:
            self._sensor_cache = tuple(self.event_manager.registry.iter_sensor_methods())
        return self._sensor_cache

    def iter_registered_methods(
        self, event_group: str
    ) -> tuple[tuple[str, tuple[Callable, ...]], ...]:
        self._refresh_cache_if_needed()
        if event_group in self._group_cache:
            return self._group_cache[event_group]
        class_events = self.event_manager.definition.class_events.get(event_group, set())
        registered_methods = []
        for event_name in class_events:
            methods = self._iter_event_methods(event_name)
            if methods:
                registered_methods.append((event_name, methods))
        self._group_cache[event_group] = tuple(registered_methods)
        return self._group_cache[event_group]

    def copy_registered_methods(self, event_name: str) -> set[Callable]:
        return self.event_manager.registry.copy_event_methods(event_name)

    def has_group_methods(self, event_group: str) -> bool:
        return bool(self.iter_registered_methods(event_group))

    def has_event_methods(self, event_name: str) -> bool:
        return bool(self._iter_event_methods(event_name))

    def has_sensor_methods(self) -> bool:
        return any(methods for _target, methods in self.iter_sensor_methods())
