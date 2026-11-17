"""Greenfoot-style scenario control, independent of any IDE transport.

A ``Scenario`` binds one world to an :class:`ExperimentSession` and offers the
operations a stepping IDE needs: act/run/pause, speed, picking, placing,
moving and deleting actors, a JSON-friendly snapshot and generated setup code.
Like ``ExperimentSession`` it must be driven from the world's mainloop thread
(Pyodide: the single JS thread) and is never imported into an IDE UI process.
"""
from __future__ import annotations

import inspect
from typing import Any, Optional

from miniworlds.tools.experiment import ExperimentSession

MIN_SPEED = 0.1
MAX_SPEED = 8.0
PRUNE_MIN = 64  # registered handles before dead actors are forgotten


class Scenario:
    def __init__(self, world, source_version: str = "0"):
        self.world = world
        self.session = ExperimentSession(world, source_version)
        self._handles: dict[int, str] = {}
        self._base_fps = world.fps
        self._applied_fps = world.fps
        self._speed = 1.0
        self._prune_at = PRUNE_MIN

    # --- run control -----------------------------------------------------

    def act(self, frames: int = 1) -> None:
        """Advance exactly ``frames`` frames and stay paused ("Act")."""
        self.world.step(frames)

    def run(self) -> None:
        self.world.resume()

    def pause(self) -> None:
        self.world.pause()
        self.world.refresh()

    @property
    def speed(self) -> float:
        return self._speed

    def set_speed(self, factor: float) -> float:
        """Scale the frame rate; returns the clamped factor actually used."""
        if isinstance(factor, bool) or not isinstance(factor, (int, float)):
            raise TypeError("speed must be a number")
        if self.world.fps != self._applied_fps:
            # the program changed the frame rate itself: that is the new base
            self._base_fps = self.world.fps
        self._speed = min(MAX_SPEED, max(MIN_SPEED, float(factor)))
        self.world.fps = max(1, round(self._base_fps * self._speed))
        self._applied_fps = self.world.fps
        return self._speed

    # --- objects ---------------------------------------------------------

    def handle(self, obj) -> str:
        """Stable handle for ``obj`` (registered on first use)."""
        key = id(obj)
        handle = self._handles.get(key)
        if handle is None:
            if len(self._handles) >= self._prune_at:
                self._prune()
            handle = self._handles[key] = self.session.register(obj)
        return handle

    def _prune(self) -> None:
        """Forget handles of actors that left the world (the session keeps
        objects alive, so long sessions with many spawned and removed actors
        would otherwise grow without bound)."""
        alive = {id(actor) for actor in self.world.actors}
        actor_type = self._actor_type()
        for key, handle in list(self._handles.items()):
            try:
                obj = self.session.resolve(handle)
            except KeyError:
                del self._handles[key]
                continue
            if isinstance(obj, actor_type) and key not in alive:
                self.session.release(handle)
                del self._handles[key]
        self._prune_at = max(PRUNE_MIN, 2 * len(self._handles))

    def resolve(self, handle: str):
        try:
            return self.session.resolve(handle)
        except KeyError:
            raise LookupError("Das Objekt existiert nicht mehr.") from None

    def pick(self, x: float, y: float) -> Optional[str]:
        """Handle of the topmost actor at world position (x, y), if any."""
        found = self.world.detect_actors((x, y))
        if not found:
            return None
        top = max(enumerate(found), key=lambda item: (getattr(item[1], "layer", 0), item[0]))
        return self.handle(top[1])

    def place(self, cls, x: float, y: float) -> str:
        """Create ``cls`` centered at (x, y); returns its handle."""
        if not (inspect.isclass(cls) and issubclass(cls, self._actor_type())):
            raise TypeError("place expects an Actor subclass")

        def create():
            actor = cls((x, y))
            actor.center = (x, y)
            return actor

        return self.handle(self.world.invoke(create))

    def move(self, handle: str, x: float, y: float) -> None:
        actor = self.resolve(handle)

        def relocate():
            actor.center = (x, y)

        self.world.invoke(relocate)

    def delete(self, handle: str) -> None:
        actor = self.resolve(handle)
        self.world.invoke(actor.remove)
        handle = self._handles.pop(id(actor), None)
        if handle is not None:
            self.session.release(handle)

    # --- views -----------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        actors = []
        for actor in list(self.world.actors):
            cx, cy = actor.center
            actors.append(
                {
                    "handle": self.handle(actor),
                    "cls": type(actor).__name__,
                    "x": round(cx, 2),
                    "y": round(cy, 2),
                    "direction": actor.direction,
                    "size": list(actor.size),
                }
            )
        return {
            "world": {
                "cls": type(self.world).__name__,
                "frame": self.world.frame,
                "paused": bool(self.world.is_paused),
                "fps": self.world.fps,
                "speed": self._speed,
            },
            "actors": actors,
        }

    def export_setup_code(self, indent: str = "    ") -> str:
        """Python lines that recreate the current actors ("Save the World").

        Names are ``<class>_<n>`` in lower case. Direction is only written when
        it differs from the default (0 would be the engine default).
        """
        counters: dict[str, int] = {}
        lines = []
        for actor in list(self.world.actors):
            cls_name = type(actor).__name__
            counters[cls_name] = counters.get(cls_name, 0) + 1
            name = f"{cls_name.lower()}_{counters[cls_name]}"
            cx, cy = actor.center
            lines.append(f"{indent}{name} = {cls_name}(({round(cx)}, {round(cy)}))")
            if actor.direction:
                lines.append(f"{indent}{name}.direction = {actor.direction}")
        return "\n".join(lines)

    @staticmethod
    def _actor_type():
        from miniworlds.actors.actor import Actor

        return Actor

    def close(self) -> None:
        self.session.close()
        self._handles.clear()
