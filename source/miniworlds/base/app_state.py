from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miniworlds.base.app import App
    from miniworlds.base.window import Window
    from miniworlds.worlds.world import World


@dataclass
class AppState:
    running_world: "World | None" = None
    running_worlds: list["World"] = field(default_factory=list)
    path: str | None = ""
    running_app: "App | None" = None
    window: "Window | None" = None

    def reset(self, unittest: bool = False, file: str | None = None) -> None:
        self.running_world = None
        self.running_worlds = []
        self.running_app = None
        self.window = None
        self.path = os.path.dirname(file) if file and unittest else ""

    def bind_app(self, app: "App", world: "World", window: "Window") -> None:
        self.running_app = app
        self.window = window
        self.running_world = world
        self.running_worlds = [world]

    def set_running_world(self, world: "World | None") -> None:
        self.running_world = world

    def add_running_world(self, world: "World") -> None:
        if world not in self.running_worlds:
            self.running_worlds.append(world)

    def remove_running_world(self, world: "World") -> None:
        if world in self.running_worlds:
            self.running_worlds.remove(world)
        if self.running_world is world:
            self.running_world = self.running_worlds[0] if self.running_worlds else None

    def set_path(self, path: str | None) -> None:
        self.path = path or ""
