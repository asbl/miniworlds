"""JSON command layer for Greenfoot-style IDEs (browser or desktop).

``ScenarioHost`` implements the ``runtime_host`` protocol: install it before
``world.run()`` and it pauses the program before the first frame and binds a
:class:`Scenario` to the main world. A UI then sends text commands through
:meth:`dispatch` and receives JSON, so the same layer serves Pyodide
(``host.dispatch(name, json)``) and socket transports.

Arguments typed by pupils are parsed with ``ast.literal_eval`` only; no
expression is ever evaluated.
"""
from __future__ import annotations

import ast
import inspect
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Optional

from miniworlds.tools.scenario import Scenario

ENGINE_METHODS = ("move", "turn_left", "turn_right", "turn_around")
# Attributes set by the engine itself; shown separately from pupil attributes.
ENGINE_FIELDS = frozenset(
    {"actor_id", "is_focusable", "has_focus", "blendmode", "source_rect", "speed"}
)
SIMPLE = (str, int, float, bool, type(None))
MAX_TEXT = 120


def _short(value: Any) -> str:
    text = repr(value)
    return text if len(text) <= MAX_TEXT else text[: MAX_TEXT - 1] + "…"


def _describe_parameters(function: Any, skip: int) -> list[dict]:
    """Parameters of ``function`` after the first ``skip`` positional ones."""
    signature = inspect.signature(function)
    params = []
    for parameter in list(signature.parameters.values())[skip:]:
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            continue
        params.append(
            {
                "name": parameter.name,
                "keyword_only": parameter.kind is parameter.KEYWORD_ONLY,
                "required": parameter.default is parameter.empty,
                "default": None
                if parameter.default is parameter.empty
                else _short(parameter.default),
            }
        )
    return params


def _parse_values(function_name: str, params: list[dict], texts: list) -> tuple[list, dict]:
    """Turn field texts into ``(positional, keywords)`` for ``params``.

    Values are Python literals (``ast.literal_eval``); anything else is taken
    as plain text. Empty optional fields keep their default, later ones are
    passed by name so a gap never drops a value.
    """
    if len(texts) > len(params):
        raise ValueError(
            f"{function_name} erwartet höchstens {len(params)} Wert(e), "
            f"bekommen: {len(texts)}."
        )
    arguments: list = []
    keywords: dict = {}
    skipped_optional = False
    for parameter, text in zip(params, texts):
        text = str(text).strip()
        if text == "":
            if parameter["required"]:
                raise ValueError(f"Wert für „{parameter['name']}“ fehlt.")
            skipped_optional = True
            continue
        try:
            value = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            value = text
        if parameter["keyword_only"] or skipped_optional:
            keywords[parameter["name"]] = value
        else:
            arguments.append(value)
    return arguments, keywords


def _describe_value(value: Any) -> str:
    if isinstance(value, SIMPLE):
        return _short(value)
    if isinstance(value, (list, tuple, set, dict)) and len(value) <= 8:
        try:
            return _short(value)
        except Exception:
            pass
    return f"<{type(value).__name__}>"


class ScenarioHost:
    """Runtime host plus command dispatcher for one running program."""

    def __init__(self, on_ready: Optional[Callable[["ScenarioHost"], None]] = None):
        self.scenario: Optional[Scenario] = None
        self.namespace: dict = {}
        self.project_dir: Optional[str] = None
        self._on_ready = on_ready

    # --- runtime_host protocol ------------------------------------------

    def start(self, app) -> None:
        worlds = list(app.worlds_manager.worlds)
        if not worlds:
            raise ValueError("Das Programm muss zuerst eine World erzeugen.")
        for world in worlds:
            world.pause()
        self.scenario = Scenario(worlds[0])
        for world in worlds:
            world.refresh()
        if self._on_ready:
            self._on_ready(self)

    def poll(self, app) -> None:
        return None

    def close(self) -> None:
        if self.scenario is not None:
            self.scenario.close()
            self.scenario = None

    # --- program context --------------------------------------------------

    def bind_program(self, namespace: dict, project_dir: Optional[str] = None) -> None:
        self.namespace = namespace
        self.project_dir = project_dir

    def _modules(self):
        yield self.namespace
        if self.project_dir:
            root = str(Path(self.project_dir))
            for module in list(sys.modules.values()):
                file = getattr(module, "__file__", None)
                # "/proj" must not match "/proj2/x.py": compare whole path parts
                if file and (str(file) == root or str(file).startswith(root + "/")):
                    yield vars(module)

    def _user_classes(self) -> dict[str, type]:
        from miniworlds.actors.actor import Actor
        from miniworlds.worlds.world import World

        found: dict[str, type] = {}
        for space in self._modules():
            for name, value in list(space.items()):
                if (
                    inspect.isclass(value)
                    and issubclass(value, (Actor, World))
                    and not value.__module__.startswith("miniworlds")
                ):
                    found.setdefault(value.__name__, value)
        return found

    # --- dispatcher -------------------------------------------------------

    def dispatch(self, command: str, args_json: str = "[]") -> str:
        """Run ``cmd_<command>`` and return ``{"ok": ..., "value"|"error": ...}``."""
        try:
            handler = getattr(self, "cmd_" + command, None)
            if handler is None:
                raise ValueError(f"Unbekanntes Kommando: {command}")
            if self.scenario is None:
                raise RuntimeError("Das Programm läuft nicht.")
            return json.dumps({"ok": True, "value": handler(*json.loads(args_json))})
        except Exception as error:  # reported to the UI, never fatal
            return json.dumps(
                {"ok": False, "error": f"{type(error).__name__}: {error}"}
            )

    # --- commands -------------------------------------------------------------

    def cmd_act(self, frames: int = 1):
        self.scenario.act(frames)

    def cmd_run(self):
        self.scenario.run()

    def cmd_pause(self):
        self.scenario.pause()

    def cmd_speed(self, factor: float):
        return self.scenario.set_speed(factor)

    def cmd_snapshot(self):
        return self.scenario.snapshot()

    def cmd_status(self):
        """Cheap poll: counts only (actors per class name), no per-actor data."""
        world = self.scenario.world
        return {
            "frame": world.frame,
            "paused": bool(world.is_paused),
            "fps": world.fps,
            "speed": self.scenario.speed,
            "actors": len(world.actors),
            "by_class": dict(Counter(type(actor).__name__ for actor in world.actors)),
        }

    def cmd_classes(self):
        from miniworlds.actors.actor import Actor

        classes = self._user_classes()
        return [
            {
                "name": name,
                "base": next(
                    (b.__name__ for b in cls.__mro__[1:] if b.__name__ != "object"),
                    None,
                ),
                "is_actor": issubclass(cls, Actor),
            }
            for name, cls in classes.items()
        ]

    def _class(self, class_name: str) -> type:
        cls = self._user_classes().get(class_name)
        if cls is None:
            raise ValueError(f"Unbekannte Klasse: {class_name}")
        return cls

    def cmd_constructor(self, class_name: str):
        """Constructor parameters after the position, for a "new object" dialog."""
        init = self._class(class_name).__init__
        try:
            return _describe_parameters(init, 2)  # self, position
        except (TypeError, ValueError):
            return []

    def cmd_place(self, class_name: str, x: float, y: float, texts: Optional[list] = None):
        cls = self._class(class_name)
        arguments, keywords = _parse_values(
            class_name, self.cmd_constructor(class_name), list(texts or [])
        )
        return self.scenario.place(cls, x, y, *arguments, **keywords)

    def cmd_pick(self, x: float, y: float):
        return self.scenario.pick(x, y)

    def cmd_move(self, handle: str, x: float, y: float):
        self.scenario.move(handle, x, y)

    def cmd_delete(self, handle: str):
        self.scenario.delete(handle)

    def cmd_export_code(self):
        return self.scenario.export_setup_code()

    def cmd_inspect(self, handle: str):
        obj = self.scenario.resolve(handle)
        fields: dict[str, str] = {}
        engine: dict[str, str] = {}
        if hasattr(obj, "center"):
            engine["center"] = _describe_value(tuple(obj.center))
            engine["direction"] = _describe_value(obj.direction)
            engine["size"] = _describe_value(tuple(obj.size))
        for name, value in list(getattr(obj, "__dict__", {}).items()):
            if name.startswith("_") or name in engine:
                continue
            target = engine if name in ENGINE_FIELDS else fields
            target[name] = _describe_value(value)
        return {"cls": type(obj).__name__, "fields": fields, "engine": engine}

    def cmd_methods(self, handle: str):
        obj = self.scenario.resolve(handle)
        seen: set[str] = set()
        methods = []

        def add(name: str, function: Any, origin: str):
            if name in seen or name.startswith("_"):
                return
            seen.add(name)
            try:
                params = _describe_parameters(function, 1)
            except (TypeError, ValueError):
                return
            methods.append({"name": name, "origin": origin, "params": params})

        for cls in type(obj).__mro__:
            if cls.__module__.startswith("miniworlds") or cls is object:
                continue
            for name, function in vars(cls).items():
                if inspect.isfunction(function):
                    add(name, function, cls.__name__)
        for name in ENGINE_METHODS:
            function = getattr(type(obj), name, None)
            if inspect.isfunction(function):
                add(name, function, "Actor")
        return methods

    def cmd_call(self, handle: str, method: str, texts: list):
        obj = self.scenario.resolve(handle)
        listed = {m["name"]: m for m in self.cmd_methods(handle)}
        if method not in listed:
            raise ValueError(f"Methode nicht verfügbar: {method}")
        arguments, keywords = _parse_values(method, listed[method]["params"], list(texts))
        result = self.scenario.world.invoke(getattr(obj, method), *arguments, **keywords)
        return {"result": None if result is None else _describe_value(result)}
