"""Object laboratory worker. All engine operations stay on this main thread."""

import argparse
import contextlib
import inspect
import json
import queue
import sys
import threading
import types
from pathlib import Path

# Also runnable by filename in an interpreter without the plugin installed.
if __package__:
    from .lab_model import arguments, object_name, parameter_schema
else:
    sys.path.insert(0, str(Path(__file__).parent))
    from lab_model import arguments, object_name, parameter_schema

ENGINE_METHODS = {
    "move",
    "turn_left",
    "turn_right",
    "set_position",
    "add_costume",
    "add_background",
    "play_sound",
    "detect_actors",
    "act",
}


class Laboratory:
    def __init__(self, source, filename, version):
        import miniworlds as mw

        if not hasattr(mw, "ExperimentSession") or not all(
            hasattr(mw.World, n) for n in ("pause", "refresh", "invoke")
        ):
            raise RuntimeError(
                "Das Objektlabor benötigt die Experiment-API von miniworlds ab 4.4.0.11. Bitte die Bibliothek aktualisieren."
            )
        self.mw = mw
        self.sessions = {}
        self.objects = {}
        self.identities = {}
        self.aliases = {}
        self.history = []
        self.replay_complete = True
        self.prelude = []
        self.version = version
        self.closed = False
        self.selected = None
        self.namespace = {"__name__": "__main__", "__file__": str(filename)}
        module = types.ModuleType("__main__")
        module.__dict__.update(self.namespace)
        self.namespace = module.__dict__
        sys.modules["__main__"] = module
        mw.App.reset(file=str(filename))
        original = mw.World.run
        try:
            mw.World.run = lambda world, *args, **kwargs: world.pause()
            exec(compile(source, str(filename), "exec"), self.namespace)  # noqa: S102 -- explicit pupil-program execution
        finally:
            mw.World.run = original
        self.app = mw.App.get_running_app()
        if self.app is None:
            raise ValueError("Das Programm muss zuerst eine World erzeugen.")
        self.sync()
        self.refresh()
        mw.App._run_started = True  # The adapter has presented the experiment window.

    @classmethod
    def attach(cls, app, namespace, version):
        """Inspect an already initialized program without replacing World.run."""
        import miniworlds as mw

        self = cls.__new__(cls)
        self.mw = mw
        self.app = app
        self.namespace = namespace
        self.sessions = {}
        self.objects = {}
        self.identities = {}
        self.aliases = {}
        self.history = []
        self.prelude = []
        self.version = version
        self.closed = False
        self.selected = None
        self.live = True
        self.replay_complete = True
        self.sync()
        self.refresh()
        return self

    def worlds(self):
        return list(self.app.worlds_manager.worlds)

    def refresh(self):
        for world in self.worlds():
            world.pause()
            world.refresh()

    def sync(self):
        for world in self.worlds():
            if id(world) not in self.sessions:
                self.sessions[id(world)] = self.mw.ExperimentSession(
                    world, self.version
                )
            if not getattr(self, "live", False):
                world.pause()

        containers_seen = set()

        def add(obj, name, depth=0):
            if type(obj) in (list, tuple, dict):
                if depth >= 4 or id(obj) in containers_seen:
                    return
                containers_seen.add(id(obj))
                entries = (
                    list(obj.items())[:50] if type(obj) is dict else enumerate(obj[:50])
                )
                for key, value in entries:
                    if type(key) in (str, int):
                        add(value, f"{name}[{key!r}]", depth + 1)
                return
            if not isinstance(obj, (self.mw.World, self.mw.Actor)) and (
                type(obj).__module__ == "builtins"
                or type(obj).__module__.startswith("miniworlds.")
                or inspect.ismodule(obj)
                or inspect.isroutine(obj)
            ):
                return
            identity = id(obj)
            if identity not in self.identities:
                world = (
                    obj
                    if isinstance(obj, self.mw.World)
                    else getattr(obj, "world", self.worlds()[0])
                )
                session = self.sessions.get(
                    id(world), next(iter(self.sessions.values()))
                )
                handle = session.register(obj)
                self.identities[identity] = handle
                self.objects[handle] = (obj, session)
                self.aliases[handle] = []
            handle = self.identities[identity]
            if name not in self.aliases[handle]:
                self.aliases[handle].append(name)

        for name, obj in list(self.namespace.items()):
            if not name.startswith("_") and not inspect.isclass(obj):
                add(obj, name)
        for handle, (obj, _) in list(self.objects.items()):
            for name, value in list(getattr(obj, "__dict__", {}).items()):
                if not name.startswith("_"):
                    add(value, self.aliases[handle][0] + "." + name)
        for index, world in enumerate(self.worlds()):
            if id(world) not in self.identities:
                name = self.free_name("world")
                self.namespace[name] = world
                add(world, name)
                self.prelude.append(
                    f"{name} = App.get_running_app().worlds_manager.worlds[{index}]"
                )
            world_name = self.aliases[self.identities[id(world)]][0]
            for position, actor in enumerate(world.actors):
                if id(actor) not in self.identities:
                    name = self.free_name("figur")
                    self.namespace[name] = actor
                    add(actor, name)
                    self.prelude.append(
                        f"{name} = list({world_name}.actors)[{position}]"
                    )

    def free_name(self, stem):
        index = 1
        while f"{stem}_{index}" in self.namespace:
            index += 1
        return f"{stem}_{index}"

    def value(self, value):
        handle = self.identities.get(id(value))
        if handle:
            return " → ".join(self.aliases[handle]) + " [Objektreferenz]"
        if type(value) in (str, int, float, bool, type(None), tuple, list, dict):
            # Bounded containers avoid invoking arbitrary user-defined reprs.
            if type(value) in (tuple, list, dict):
                return (
                    f"{type(value).__name__} mit {len(value)} Einträgen"
                    if len(value) > 12
                    else str(self.simple(value))[:300]
                )
            return repr(value)[:300]
        return f"<{type(value).__name__}>"

    def simple(self, value):
        if type(value) in (str, int, float, bool, type(None)):
            return value
        if type(value) in (tuple, list):
            values = [
                v
                if type(v) in (str, int, float, bool, type(None))
                else "<" + type(v).__name__ + ">"
                for v in value[:12]
            ]
            return tuple(values) if type(value) is tuple else values
        return "<" + type(value).__name__ + ">"

    def methods(self, obj):
        result = []
        for cls in type(obj).__mro__:
            for name, member in vars(cls).items():
                if name.startswith("_") or any(m["name"] == name for m in result):
                    continue
                if not inspect.isfunction(member):
                    continue
                own = not cls.__module__.startswith("miniworlds.")
                if not own and name not in ENGINE_METHODS:
                    continue
                try:
                    signature = str(inspect.signature(getattr(obj, name)))
                except (ValueError, TypeError):
                    signature = "(...)"
                result.append(
                    {
                        "name": name,
                        "owner": cls.__name__,
                        "inherited": cls is not type(obj),
                        "signature": signature,
                        "parameters": parameter_schema(getattr(obj, name)),
                    }
                )
        # @register functions live on instances, not on the Actor class.
        for name, member in getattr(obj, "__dict__", {}).items():
            if (
                not name.startswith("_")
                and inspect.ismethod(member)
                and not any(m["name"] == name for m in result)
            ):
                result.append(
                    {
                        "name": name,
                        "owner": type(obj).__name__,
                        "inherited": False,
                        "signature": str(inspect.signature(member)),
                        "parameters": parameter_schema(member),
                    }
                )
        return result

    def thumbnail(self, obj):
        """Bounded visual metadata; pygame stays in the execution backend."""
        if not isinstance(obj, self.mw.Actor):
            return None
        import base64
        import io

        import pygame

        try:
            surface = obj.image
            width, height = surface.get_size()
            if not width or not height:
                return None
            scale = min(48 / width, 48 / height, 1)
            preview = pygame.transform.smoothscale(
                surface, (max(1, int(width * scale)), max(1, int(height * scale)))
            )
            buffer = io.BytesIO()
            pygame.image.save(preview, buffer, "preview.png")
            return base64.b64encode(buffer.getvalue()).decode("ascii")
        except Exception:  # noqa: BLE001 -- user costume properties may raise; previews are optional
            # An unavailable costume must not make the object bank unusable.
            return None

    def snapshot(self):
        self.sync()
        result = []
        for handle, (obj, session) in self.objects.items():
            fields = {
                name: self.value(v)
                for name, v in getattr(obj, "__dict__", {}).items()
                if not name.startswith("_") and not callable(v)
            }
            if isinstance(obj, self.mw.Actor):
                for name in ("position", "direction", "size", "world"):
                    fields[name] = self.value(getattr(obj, name))
            result.append(
                dict(
                    handle=handle,
                    aliases=self.aliases[handle],
                    type=type(obj).__name__,
                    fields=fields,
                    methods=self.methods(obj),
                    thumbnail=self.thumbnail(obj) if len(result) < 80 else None,
                    **{
                        k: v
                        for k, v in session.describe(handle).items()
                        if k not in ("handle", "type")
                    },
                )
            )
        classes = []
        for name, cls in self.namespace.items():
            if (
                inspect.isclass(cls)
                and not name.startswith("_")
                and (
                    (
                        cls.__module__ != "builtins"
                        and not cls.__module__.startswith("miniworlds.")
                    )
                    or cls in (self.mw.Actor, self.mw.World, self.mw.TiledWorld)
                )
            ):
                try:
                    signature = str(inspect.signature(cls))
                except (ValueError, TypeError):
                    signature = "(...)"
                classes.append(
                    {
                        "name": name,
                        "signature": signature,
                        "parameters": parameter_schema(cls),
                    }
                )
        return {
            "objects": result,
            "classes": classes,
            "history": self.history,
            "prelude": self.prelude,
            "replay_complete": self.replay_complete,
            "stale": any(s.is_stale for s in self.sessions.values()),
        }

    def command(self, command):
        action = command["action"]
        if action == "revision":
            for session in self.sessions.values():
                session.mark_source_changed(command["version"])
            return self.snapshot()
        if action == "inspect":
            return self.snapshot()
        if any(s.is_stale for s in self.sessions.values()):
            raise ValueError("Code geändert – bitte das Objektlabor neu laden.")
        refs = {
            alias: self.objects[h][0] for h in self.objects for alias in self.aliases[h]
        }
        if action == "select":
            self.selected = command["handle"]
            self.refresh()
            obj = self.objects[self.selected][0]
            if isinstance(obj, self.mw.Actor):
                import pygame

                pygame.draw.rect(
                    self.app.window.surface,
                    (220, 130, 10),
                    obj.position_manager.get_screen_rect(),
                    3,
                )
                pygame.display.flip()
            return self.snapshot()
        prelude_length = len(self.prelude)
        args, kwargs = arguments(command.get("arguments", ""), refs)
        if action == "create":
            name = command["name"]
            object_name(name)
            if name in self.namespace:
                raise ValueError("Dieser Name ist bereits vergeben.")
            cls = self.namespace.get(command["class"])
            if not inspect.isclass(cls) or command["class"] not in {
                c["name"] for c in self.snapshot()["classes"]
            }:
                raise ValueError("Bitte eine angebotene Klasse wählen.")
            inspect.signature(cls).bind(*args, **kwargs)
            try:
                value = self.worlds()[0].invoke(cls, *args, **kwargs)
            except BaseException:
                self.replay_complete = False
                raise
            self.namespace[name] = value
            code = f"{name} = {command['class']}({command.get('arguments', '')})"
        elif action == "invoke":
            handle = command["handle"]
            obj, session = self.objects[handle]
            method = command["method"]
            if method not in {m["name"] for m in self.methods(obj)}:
                raise ValueError("Bitte eine angebotene Methode wählen.")
            inspect.signature(getattr(obj, method)).bind(*args, **kwargs)
            try:
                value = session.invoke(handle, method, *args, **kwargs)
            except BaseException:
                self.replay_complete = False
                raise
            code = f"{self.aliases[handle][0]}.{method}({command.get('arguments', '')})"
        else:
            raise ValueError("Unbekanntes Kommando")
        if (
            action == "invoke"
            and type(value) not in (str, int, float, bool, type(None))
            and id(value) not in self.identities
        ):
            name = self.free_name("ergebnis")
            self.namespace[name] = value
            code = name + " = " + code
        self.last_result = value
        self.sync()
        new_bindings = self.prelude[prelude_length:]
        del self.prelude[prelude_length:]
        self.history.append(
            {
                "code": code,
                "prediction": command.get("prediction", ""),
                "result": self.value(value),
            }
        )
        for binding in new_bindings:
            self.history.append(
                {"code": binding, "prediction": "", "result": "Objektreferenz"}
            )
        self.refresh()
        return self.snapshot()

    def close(self, quit_display=True):
        for session in self.sessions.values():
            session.close()
        self.closed = True
        import pygame

        if quit_display:
            pygame.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    output = sys.stdout

    def send(data):
        output.write(json.dumps(data, ensure_ascii=False) + "\n")
        output.flush()

    import os

    os.chdir(Path(args.filename).parent)
    sys.path.insert(0, str(Path(args.filename).parent))
    commands = queue.Queue()

    def read():
        for line in sys.stdin:
            commands.put(json.loads(line))
        commands.put({"action": "quit"})

    lab = None
    try:
        with contextlib.redirect_stdout(sys.stderr):
            lab = Laboratory(
                Path(args.source).read_text(encoding="utf-8"),
                args.filename,
                args.version,
            )
            send({"ok": True, "data": lab.snapshot()})
            threading.Thread(target=read, daemon=True).start()
            import pygame

            while not lab.closed:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                try:
                    command = commands.get(timeout=0.03)
                except queue.Empty:
                    continue
                if command["action"] == "quit":
                    break
                try:
                    send({"ok": True, "data": lab.command(command)})
                except Exception as error:  # noqa: BLE001 -- pupil exceptions are shown in the IDE
                    lab.refresh()
                    send(
                        {
                            "ok": False,
                            "error": f"{type(error).__name__}: {error}",
                            "data": lab.snapshot(),
                        }
                    )
    except Exception as error:  # noqa: BLE001 -- report startup failures across process boundary
        send({"ok": False, "error": f"{type(error).__name__}: {error}"})
    finally:
        if lab:
            lab.close()


if __name__ == "__main__":
    main()
