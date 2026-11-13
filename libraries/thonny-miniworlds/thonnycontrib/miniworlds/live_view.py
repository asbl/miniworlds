"""Object laboratory attached to Thonny's own local CPython backend."""

import ast
import queue
import time
import tkinter as tk
from tkinter import ttk

from thonny import get_runner, get_workbench

from .lab_model import revision
from .lab_view import LabDialog
from .live_connection import Connection


class ConnectedLabDialog(LabDialog):
    def __init__(self, owner):
        self.connection = None
        self.pending = None
        self.revision_tick = 0
        super().__init__(owner)
        self.title("miniworlds · Experimentieren im Thonny-Interpreter")
        bar = ttk.Frame(self)
        bar.pack(fill="x", before=self.log, padx=10)
        self.world_choice = tk.StringVar(value="Alle Welten")
        self.world_box = ttk.Combobox(
            bar, state="readonly", textvariable=self.world_choice
        )
        self.world_box.pack(side="left")
        self.world_box.configure(values=["Alle Welten"])
        self.world_handles = {}
        self.pause_button = ttk.Button(
            bar, text="Pausieren", command=lambda: self.control("pause")
        )
        self.pause_button.pack(side="left", padx=4)
        self.resume_button = ttk.Button(
            bar, text="Fortsetzen", command=lambda: self.control("resume")
        )
        self.resume_button.pack(side="left")
        self.inspect_button = ttk.Button(
            bar,
            text="Zustand aktualisieren",
            command=lambda: self.send({"action": "inspect"}),
        )
        self.inspect_button.pack(side="left", padx=4)
        self.status.set(
            "Programm hier neu laden; Schülercode bleibt unverändert. Thonnys Stop/Restart beendet die Sitzung."
        )
        self.bindings = []
        wb = get_workbench()
        for event in ("BackendRestart", "BackendTerminated", "ToplevelResponse"):
            handler = lambda e, name=event: self.backend_event(name, e)
            wb.bind(event, handler, True)
            self.bindings.append((event, handler))

    def current_revision(self):
        buffers = {
            e.get_filename(): e.get_content()
            for e in get_workbench().get_editor_notebook().get_all_editors()
            if e.get_filename()
        }
        return revision(
            self.root_dir, self.filename, self.editor.get_content(), buffers
        )

    def start(self):
        try:
            from thonny.common import ToplevelCommand
            from thonny.plugins.cpython_frontend.cp_front import LocalCPythonProxy

            editor, filename, source = self.source()
            ast.parse(source)
            runner = get_runner()
            if not runner or not isinstance(
                runner.get_backend_proxy(), LocalCPythonProxy
            ):
                raise ValueError("Wähle einen lokalen CPython-Interpreter.")
            if not runner.is_waiting_toplevel_command():
                raise ValueError(
                    "Bitte zuerst Thonnys Stop/Restart verwenden und dann neu laden."
                )
            self.stop()
            self.editor, self.filename, self.loaded_source = editor, filename, source
            self.root_dir = self.owner.project_dir()
            # Imported modules are loaded from disk by ordinary Python imports.
            # Do not mislabel unsaved helper buffers as executed source.
            for other in get_workbench().get_editor_notebook().get_all_editors():
                path = other.get_filename()
                if path and path != filename:
                    from pathlib import Path

                    if (
                        not Path(path)
                        .resolve()
                        .is_relative_to(Path(self.root_dir).resolve())
                    ):
                        continue
                    try:
                        saved = Path(path).read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        continue
                    if other.get_content() != saved:
                        raise ValueError(
                            "Speichere zuerst Änderungen in weiteren Projektdateien."
                        )
            self.loaded_revision = self.current_revision()
            self.sent_revision = self.loaded_revision
            self.connection = Connection()
            self.connection_started = time.monotonic()
            configuration = {
                "port": self.connection.port,
                "token": self.connection.token,
                "source": source,
                "version": self.loaded_revision,
            }
            self.busy = True
            runner.send_command(
                ToplevelCommand(
                    "Run", args=[filename], miniworlds_experiment=configuration
                )
            )
            self.status.set(
                "Programm startet im Thonny-Interpreter … Stop/Restart bricht auch lange Aufrufe ab."
            )
            self.draw_classes()
        except (ValueError, OSError, SyntaxError) as error:
            self.status.set(str(error))
        self.controls()

    def send(self, command):
        if self.busy or self.connection is None:
            return
        try:
            if (
                command.get("action") == "create"
                and self.world_choice.get() in self.world_handles
            ):
                command = dict(
                    command, world=self.world_handles[self.world_choice.get()]
                )
            self.pending = self.connection.send(command)
            self.busy = True
        except OSError as error:
            self.status.set(str(error))
        self.controls()

    def control(self, action):
        command = {"action": action}
        if self.world_choice.get() in self.world_handles:
            command["world"] = self.world_handles[self.world_choice.get()]
        self.send(command)

    def controls(self):
        ready = bool(self.connection and self.data and not self.busy and not self.stale)
        self.invoke_button.configure(
            state="normal" if ready and self.bank.selection() else "disabled"
        )
        self.create_button.configure(state="normal" if ready else "disabled")
        if hasattr(self, "pause_button"):
            self.pause_button.configure(
                state="normal"
                if self.connection and self.data and not self.busy
                else "disabled"
            )
            self.resume_button.configure(state="normal" if ready else "disabled")
            self.inspect_button.configure(
                state="normal"
                if self.connection and self.data and not self.busy
                else "disabled"
            )

    def show_data(self, data):
        super().show_data(data)
        self.world_handles = {
            f"{i + 1}: {w['type']}": w["handle"]
            for i, w in enumerate(data.get("worlds", []))
        }
        self.world_box.configure(values=["Alle Welten", *self.world_handles])
        if self.world_choice.get() not in self.world_handles:
            self.world_choice.set("Alle Welten")

    def poll(self):
        if not self.winfo_exists():
            return
        connection = self.connection
        if connection:
            try:
                while True:
                    response = connection.events.get_nowait()
                    if response.get("ended"):
                        self.stop()
                        break
                    if (
                        response.get("id") is not None
                        and response["id"] != self.pending
                    ):
                        continue
                    self.pending = None
                    self.busy = False
                    if "data" in response:
                        self.show_data(response["data"])
                    self.status.set(
                        (
                            "Welt pausiert · Methoden einzeln ausprobieren."
                            if self.data and self.data.get("paused")
                            else "Simulation läuft."
                        )
                        if response.get("ok")
                        else response.get("error", "Verbindungsfehler")
                    )
                    if response.get("traceback"):
                        self.log.configure(state="normal")
                        self.log.insert("end", response["traceback"] + "\n")
                        self.log.configure(state="disabled")
            except queue.Empty:
                pass
        if (
            self.connection
            and self.data is None
            and time.monotonic() - self.connection_started > 20
        ):
            self.stop()
            self.status.set(
                "Keine Verbindung zum Experiment-Backend. Benötigt werden miniworlds mit den IDE-Host-Hooks und das Backend-Plugin. Bitte Bibliothek aktualisieren und Thonny neu starten; Details stehen in der Shell."
            )
        self.revision_tick += 1
        if self.connection and self.loaded_revision and self.revision_tick % 3 == 0:
            try:
                current = self.current_revision()
                self.stale = current != self.loaded_revision
                if self.stale:
                    self.status.set(
                        "Code geändert – Laufzeit verwendet noch den vorherigen Stand. Bitte Stop/Restart und neu laden."
                    )
                if not self.busy and self.data and current != self.sent_revision:
                    self.send({"action": "revision", "version": current})
                    self.sent_revision = current
            except (OSError, tk.TclError):
                self.stale = True
                self.status.set("Projektstand nicht lesbar. Bitte neu laden.")
        self.controls()
        self.after(250, self.poll)

    def backend_event(self, name, event):
        # A fresh CPython backend also returns environment information before
        # Run starts. That response must not tear down our pending connection.
        if name == "ToplevelResponse" and getattr(event, "command_name", None) != "Run":
            return
        if name == "BackendRestart" and not getattr(event, "full", False):
            return
        if self.connection:
            loaded = self.data is not None
            self.stop()
            self.status.set(
                "Thonny-Ausführung beendet oder neu gestartet. Objektbank geleert."
                if loaded else "Experiment konnte nicht gestartet werden. Benötigt werden miniworlds mit IDE-Host-API 1 und das aktuelle Backend-Plugin. Details stehen in der Shell."
            )

    def stop(self):
        if self.connection:
            self.connection.close()
        self.connection = None
        self.pending = None
        self.data = None
        self.busy = False
        self.stale = False
        self.highlighted = None
        self.fields_before.clear()
        self.bank.delete(*self.bank.get_children())
        self.fields.delete(*self.fields.get_children())
        self.status.set(
            "Verbindung beendet. Die Objektbank wurde geleert; Thonnys Stop/Restart beendet das Programm."
        )
        self.controls()

    def close(self):
        self.stop()
        for name, handler in self.bindings:
            get_workbench().unbind(name, handler)
        self.destroy()
