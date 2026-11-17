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
    def __init__(self, owner, parent=None):
        self.connection = None
        self.pending = None
        self.revision_tick = 0
        super().__init__(owner, parent)
        bar = ttk.Frame(self.world_controls)
        bar.pack(fill="x", padx=4)
        self.world_choice = tk.StringVar(value="Alle Welten")
        self.world_box = ttk.Combobox(
            bar, state="readonly", textvariable=self.world_choice, width=14
        )
        self.world_box.configure(values=["Alle Welten"])
        self.world_handles = {}
        self.pause_button = ttk.Button(
            bar, text="▶ Start", command=self.toggle_pause, width=9
        )
        self.pause_button.pack(side="left", padx=4)
        self.inspect_button = ttk.Button(
            self.properties_frame,
            text="Aktualisieren",
            command=lambda: self.send({"action": "inspect"}),
        )
        self.inspect_button.pack(anchor="w")
        self.status.set(
            "Wähle eine Figur und probiere eine Methode aus. Ausblenden erhält deine Sitzung."
        )
        self.bindings = []
        wb = get_workbench()
        for event in ("BackendRestart", "BackendTerminated", "ToplevelResponse"):
            handler = lambda e, name=event: self.backend_event(name, e)
            wb.bind(event, handler, True)
            self.bindings.append((event, handler))

    def toggle_pause(self):
        self.control(
            "resume" if self.data and self.data.get("paused", True) else "pause"
        )

    def wait_for_restart(self):
        self.reload_job = None
        runner = get_runner()
        if runner and runner.is_waiting_toplevel_command():
            self.start()
        elif time.monotonic() < self.reload_deadline:
            self.reload_job = self.after(100, self.wait_for_restart)
        else:
            self.status.set("Neustart dauert zu lange. Bitte erneut Laden wählen.")

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
        if getattr(self, "reload_job", None):
            return
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
            if not runner.is_waiting_toplevel_command() and self.connection:
                self.stop_program()
                self.reload_deadline = time.monotonic() + 10
                self.reload_job = self.after(100, self.wait_for_restart)
                self.busy = True
                self.status.set("Programm wird neu geladen …")
                self.controls()
                return
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
            self.begin_action(command)
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
        ready = bool(
            self.connection
            and self.data
            and not self.busy
            and not self.stale
            and self.data.get("paused", True)
        )
        self.common_controls(ready)
        self.invoke_button.configure(
            state="normal" if self.action_ready(ready) else "disabled"
        )
        self.create_button.configure(
            state="normal"
            if ready
            and self.class_name.get() in self.classes
            and self.constructor_form.valid()
            else "disabled"
        )
        if hasattr(self, "pause_button"):
            self.pause_button.configure(
                state="normal"
                if self.connection and self.data and not self.busy
                else "disabled"
            )
            self.pause_button.configure(
                text="▶ Start"
                if not self.data or self.data.get("paused", True)
                else "Ⅱ Pause"
            )
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
        if len(self.world_handles) > 1:
            self.world_box.pack(side="left", before=self.pause_button)
        else:
            self.world_box.pack_forget()
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
                        first_snapshot = self.data is None
                        self.show_data(response["data"])
                        if first_snapshot:
                            self.owner.lab_ready()
                    self.status.set(
                        (
                            "Welt pausiert · Methoden einzeln ausprobieren."
                            if self.data and self.data.get("paused")
                            else "Simulation läuft."
                        )
                        if response.get("ok")
                        else "Aufruf fehlgeschlagen · Prüfe die Hinweise unten."
                    )
                    self.set_outcome(response)
                    self.select_object()
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
        self.poll_job = self.after(250, self.poll)

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
                if loaded
                else "Experiment konnte nicht gestartet werden. Benötigt werden miniworlds mit IDE-Host-API 1 und das aktuelle Backend-Plugin. Details stehen in der Shell."
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
        self.last_error = None
        self.fields_before.clear()
        self.comparison_before.clear()
        self.comparison_after.clear()
        self.field_detail.set("")
        self._viewed_handle = None
        self.receiver.set("Noch kein Objekt ausgewählt")
        self.last_call.set("")
        self.result_summary.set("")
        self.result_panel.configure(text="Ergebnis")
        self.chosen_methods.clear()
        self.bank.clear()
        self.fields.delete(*self.fields.get_children())
        self.status.set(
            "Verbindung beendet. Die Objektbank wurde geleert; Thonnys Stop/Restart beendet das Programm."
        )
        self.controls()

    def stop_program(self):
        if getattr(self, "reload_job", None):
            self.after_cancel(self.reload_job)
            self.reload_job = None
        runner = get_runner()
        self.stop()
        if runner:
            runner.cmd_stop_restart()
        self.status.set("Programm gestoppt. Zum Weiterarbeiten neu laden.")

    def close(self):
        if getattr(self, "reload_job", None):
            self.after_cancel(self.reload_job)
        if hasattr(self, "poll_job"):
            self.after_cancel(self.poll_job)
        self.stop()
        for name, handler in self.bindings:
            get_workbench().unbind(name, handler)
        self.destroy()
