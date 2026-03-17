from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from miniworlds.base.app import App
    from miniworlds.base.app_state import AppState
    from miniworlds.base.window import Window
    from miniworlds.worlds.world import World


class AppStateBridge:
    _FIELDS = ("running_world", "running_worlds", "path", "running_app", "window")

    def __init__(self, app_class: type["App"], state: "AppState"):
        self.app_class = app_class
        self.state = state

    def _get_class_value(self, field_name: str) -> Any:
        return getattr(self.app_class, field_name)

    def _get_state_value(self, field_name: str) -> Any:
        return getattr(self.state, field_name)

    def _class_override_exists(self, field_name: str) -> bool:
        class_value = self._get_class_value(field_name)
        state_value = self._get_state_value(field_name)
        if field_name == "running_worlds":
            return class_value is not state_value and class_value != state_value
        return class_value is not state_value

    def _consume_class_override(self, field_name: str) -> Any:
        value = self._get_state_value(field_name)
        if self._class_override_exists(field_name):
            value = self._get_class_value(field_name)
            setattr(self.state, field_name, value)
        return value

    def _mutate_state(self, operation: Callable[[], None]) -> None:
        operation()
        self.sync_class_state()

    def sync_class_state(self) -> None:
        for field_name in self._FIELDS:
            setattr(self.app_class, field_name, self._get_state_value(field_name))

    def reset(self, unittest: bool = False, file: str | None = None) -> None:
        self._mutate_state(lambda: self.state.reset(unittest=unittest, file=file))

    def bind_app(self, app: "App", world: "World", window: "Window") -> None:
        self._mutate_state(lambda: self.state.bind_app(app, world, window))

    def set_running_world(self, world: "World | None") -> None:
        self._mutate_state(lambda: self.state.set_running_world(world))

    def add_running_world(self, world: "World") -> None:
        self._mutate_state(lambda: self.state.add_running_world(world))

    def remove_running_world(self, world: "World") -> None:
        self._mutate_state(lambda: self.state.remove_running_world(world))

    def set_path(self, path: str | None) -> None:
        self._mutate_state(lambda: self.state.set_path(path))

    def get_running_world(self) -> "World | None":
        return self._consume_class_override("running_world")

    def get_running_app(self) -> "App | None":
        return self._consume_class_override("running_app")

    def get_window(self) -> "Window | None":
        return self._consume_class_override("window")

    def get_path(self) -> str | None:
        return self._consume_class_override("path")

    def get_running_worlds(self) -> list["World"]:
        return self._consume_class_override("running_worlds")