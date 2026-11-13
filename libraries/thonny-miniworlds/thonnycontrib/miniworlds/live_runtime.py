"""Side channel for a real Thonny backend; only poll() executes pupil code."""

import json
import queue
import socket
import threading
import traceback
from uuid import uuid4

from .lab_runtime import Laboratory


class RuntimeHost:
    def __init__(self, configuration, namespace):
        self.configuration = configuration
        self.namespace = namespace
        self.generation = uuid4().hex
        self.commands = queue.Queue(maxsize=100)
        self.lab = None
        self.closed = False
        self.socket = socket.create_connection(
            ("127.0.0.1", configuration["port"]), timeout=5
        )
        self.socket.settimeout(None)
        self.reader = self.socket.makefile("r", encoding="utf-8")
        self.writer = self.socket.makefile("w", encoding="utf-8")
        self.send({"token": configuration["token"], "generation": self.generation})
        threading.Thread(target=self._read, daemon=True).start()

    def send(self, message):
        self.writer.write(json.dumps(message, ensure_ascii=False) + "\n")
        self.writer.flush()

    def _read(self):
        try:
            for line in self.reader:
                if len(line) > 1024 * 1024:
                    break
                command = json.loads(line)
                if not isinstance(command, dict) or not isinstance(
                    command.get("action"), str
                ):
                    raise TypeError("Invalid experiment command")
                self.commands.put(command)
        except (OSError, TypeError, ValueError):
            pass
        finally:
            self.commands.put({"action": "disconnect"})

    def start(self, app):
        if self.lab is not None:
            return
        self.lab = Laboratory.attach(app, self.namespace, self.configuration["version"])
        self.send({"ok": True, "generation": self.generation, "data": self.snapshot()})

    def snapshot(self):
        data = self.lab.snapshot()
        data["paused"] = all(w.is_paused for w in self.lab.worlds())
        data["worlds"] = [
            {"handle": self.lab.identities[id(w)], "type": type(w).__name__}
            for w in self.lab.worlds()
        ]
        return data

    def encode_result(self, value, depth=0):
        """Bounded, typed values; live objects stay in the backend object bank."""
        if type(value) in (str, int, float, bool, type(None)):
            return {"kind": "value", "value": value}
        handle = self.lab.identities.get(id(value))
        if handle:
            return {"kind": "reference", "handle": handle, "type": type(value).__name__}
        if depth < 4 and type(value) in (list, tuple):
            return {
                "kind": type(value).__name__,
                "items": [self.encode_result(v, depth + 1) for v in value[:50]],
                "truncated": len(value) > 50,
            }
        if depth < 4 and type(value) is dict:
            return {
                "kind": "dict",
                "items": [
                    [self.encode_result(k, depth + 1), self.encode_result(v, depth + 1)]
                    for k, v in list(value.items())[:50]
                ],
                "truncated": len(value) > 50,
            }
        return {
            "kind": "summary",
            "type": type(value).__name__,
            "text": self.lab.value(value),
        }

    def poll(self, app):
        if self.closed or self.lab is None:
            return
        # Bound work per frame; keep SDL events and stop/restart responsive.
        for _ in range(10):
            try:
                command = self.commands.get_nowait()
            except queue.Empty:
                return
            if command.get("action") == "disconnect":
                for world in self.lab.worlds():
                    world.pause()
                self.close()
                return
            response = {"id": command.get("id"), "generation": self.generation}
            try:
                if command.get("generation") != self.generation:
                    raise ValueError("Die Experimentiersitzung ist nicht mehr gültig.")
                action = command["action"]
                if action in ("pause", "resume"):
                    if action == "resume" and any(
                        s.is_stale for s in self.lab.sessions.values()
                    ):
                        raise ValueError(
                            "Code geändert – bitte das Programm neu laden."
                        )
                    handle = command.get("world")
                    worlds = (
                        self.lab.worlds()
                        if handle is None
                        else [self.lab.objects[handle][0]]
                    )
                    if any(w not in self.lab.worlds() for w in worlds):
                        raise ValueError("Bitte eine vorhandene Welt wählen.")
                    if action == "resume":
                        self.lab.replay_complete = False
                    for world in worlds:
                        getattr(world, action)()
                else:
                    previous = app.running_world
                    try:
                        if action == "create" and command.get("world"):
                            chosen = self.lab.objects[command["world"]][0]
                            if chosen not in self.lab.worlds():
                                raise ValueError("Bitte eine vorhandene Welt wählen.")
                            app.set_running_world(chosen)
                            if chosen is not self.lab.worlds()[0]:
                                self.lab.replay_complete = False
                        self.lab.command(command)
                        if action in ("invoke", "create"):
                            response["result"] = self.encode_result(
                                self.lab.last_result
                            )
                    finally:
                        app.set_running_world(previous)
                response.update(ok=True, data=self.snapshot())
            except Exception as error:  # noqa: BLE001 -- pupil exceptions cross the protocol boundary
                response.update(
                    ok=False,
                    error=f"{type(error).__name__}: {error}",
                    traceback=traceback.format_exc(),
                )
                # Reporting must not replace the pupil's original exception.
                try:
                    response["data"] = self.snapshot()
                except Exception as snapshot_error:  # noqa: BLE001 -- preserve the original pupil error
                    response["snapshot_error"] = (
                        f"{type(snapshot_error).__name__}: {snapshot_error}"
                    )
            try:
                self.send(response)
            except OSError:
                self.close()
                return

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.lab is not None:
            self.lab.close(quit_display=False)
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.writer.close()
        except OSError:
            pass
        self.socket.close()
