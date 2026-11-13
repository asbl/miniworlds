"""Version-aware installation dialog with explicit, reversible repair."""

import json
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import thonny
from thonny import get_runner

from .maintenance import RESULT_PREFIX
from .updates import fetch_versions, installation_hint, version_message

WORKER = Path(__file__).with_name("maintenance.py")


def get_thonny_user_dir():
    return thonny.THONNY_USER_DIR


def run_worker(executable, action, emit, backup_root=None):
    command = [executable, "-I", str(WORKER), action]
    if backup_root:
        command.extend(["--backup-root", str(backup_root)])
    result = None
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ) as process:
        for line in process.stdout:
            if line.startswith(RESULT_PREFIX):
                result = json.loads(line[len(RESULT_PREFIX) :])
            else:
                emit(line)
        process.wait()
        if result is None:
            raise RuntimeError(
                f"Der Installationshelfer lieferte kein Ergebnis (Fehlercode {process.returncode})."
            )
    return result


class LibraryDialog(tk.Toplevel):
    def __init__(self, master, executable):
        super().__init__(master)
        self.executable = executable
        self.title("miniworlds installieren und aktualisieren")
        self.transient(master)
        self.geometry("700x610")
        self.minsize(460, 430)
        self.busy = False
        self.operation = None
        self.closed = False
        self.installation = None
        self.versions = None
        self.events = queue.Queue()
        self.log = ""
        self.status = tk.StringVar(
            value="Installierte Version und neue Versionen werden geprüft …"
        )
        self.summary = ttk.Label(
            self, textvariable=self.status, wraplength=650, justify="left", padding=12
        )
        self.summary.pack(fill="x")
        self.summary.bind(
            "<Configure>",
            lambda e: self.summary.configure(wraplength=max(300, e.width - 24)),
        )
        ttk.Label(
            self,
            text="Ausgewähltes Python: " + executable,
            wraplength=650,
            padding=(12, 0),
        ).pack(fill="x")
        bar = ttk.Frame(self, padding=12)
        bar.pack(fill="x")
        self.check_button = ttk.Button(bar, text="Erneut prüfen", command=self.check)
        self.check_button.pack(side="left")
        self.install_button = ttk.Button(
            bar,
            text="Installieren / aktualisieren",
            command=lambda: self.change("install"),
        )
        self.install_button.pack(side="left", padx=6)
        self.repair_button = ttk.Button(
            bar,
            text="Reparieren mit Sicherung …",
            command=lambda: self.change("repair"),
        )
        self.repair_button.pack(side="left")
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=12)
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        self.output = tk.Text(frame, state="disabled", wrap="word", height=15, width=60)
        scroll = ttk.Scrollbar(frame, command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.output.pack(fill="both", expand=True)
        ttk.Label(
            self,
            text="Die Reparatur sichert nur miniworlds-Paketdateien. Schülerprojekte bleiben erhalten.",
            wraplength=650,
            padding=(12, 0),
        ).pack(fill="x")
        bottom = ttk.Frame(self, padding=12)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Protokoll speichern …", command=self.save_log).pack(
            side="left"
        )
        self.close_button = ttk.Button(bottom, text="Schließen", command=self.close)
        self.close_button.pack(side="right")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda e: self.close())
        self.after(50, self.poll)
        self.check()

    def append(self, text):
        self.log += text
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def selected(self):
        runner = get_runner()
        proxy = runner.get_backend_proxy() if runner else None
        return bool(proxy and proxy.get_target_executable() == self.executable)

    def set_busy(self, busy):
        self.busy = busy
        self.check_button.configure(state="disabled" if busy else "normal")
        enabled = (
            not busy
            and self.installation
            and self.installation.get("pip")
            and not self.installation.get("managed")
            and self.installation.get("user_enabled")
            and tuple(map(int, self.installation["python"].split(".")[:2])) >= (3, 10)
        )
        self.install_button.configure(state="normal" if enabled else "disabled")
        self.repair_button.configure(
            state="normal"
            if enabled and not self.installation.get("editable")
            else "disabled"
        )
        self.close_button.configure(
            state="disabled"
            if busy and self.operation in {"install", "repair"}
            else "normal"
        )
        if busy:
            self.progress.start(15)
        else:
            self.progress.stop()

    def check(self):
        if self.busy:
            return
        if not self.selected():
            self.status.set(
                "Der Interpreter wurde gewechselt. Schließe diesen Dialog und öffne ihn für das neue Python erneut."
            )
            self.installation = None
            self.set_busy(False)
            return
        self.operation = "inspect"
        self.status.set("Installierte Version und neue Versionen werden geprüft …")
        self.set_busy(True)

        def work():
            try:
                state = run_worker(
                    self.executable,
                    "inspect",
                    lambda line: self.events.put(("log", line)),
                )
                versions = {}
                if state.get("ok"):
                    try:
                        versions = fetch_versions(state["python"])
                    except Exception as error:  # noqa: BLE001 -- network failure is displayed, never called current
                        versions = {"error": str(error)}
                self.events.put(("checked", (state, versions)))
            except Exception as error:  # noqa: BLE001 -- report a failed background worker
                self.events.put(("failed", str(error)))

        threading.Thread(target=work, daemon=True).start()

    def show_state(self):
        if not self.installation or not self.installation.get("ok"):
            self.status.set(
                "Installation konnte nicht geprüft werden: "
                + (self.installation or {}).get("error", "Unbekannter Fehler")
            )
            return
        state = self.installation
        text = f"Installiert: {state['version'] or 'noch nicht installiert'}\n"
        text += version_message(
            state["version"], self.versions or {"error": "Keine Versionsantwort"}
        )
        if state["issues"]:
            text += "\n\nInstallation prüfen: " + " ".join(state["issues"])
        if state["managed"]:
            text += "\n\nDiese Umgebung wird vom Betriebssystem verwaltet (PEP 668). Wähle eine virtuelle Umgebung."
        if not state["pip"]:
            text += "\n\npip fehlt. Bitte eine virtuelle Umgebung mit pip auswählen."
        if not state["user_enabled"]:
            text += "\n\nInstallationen im Benutzerverzeichnis sind hier deaktiviert. Bitte eine venv auswählen."
        if state.get("editable"):
            text += "\n\nEntwicklungsinstallation: Die automatische Bereinigung ist ausgeschaltet."
        self.status.set(text)

    def change(self, action):
        if self.busy or not self.installation or not self.installation.get("ok"):
            return
        runner = get_runner()
        if not self.selected() or not runner.is_waiting_toplevel_command():
            self.status.set(
                "Bitte zuerst das Programm stoppen und den ausgewählten Interpreter erneut prüfen."
            )
            return
        if (
            self.installation.get("managed")
            or not self.installation.get("pip")
            or not self.installation.get("user_enabled")
        ):
            return
        backup_root = Path(get_thonny_user_dir()) / "miniworlds-backups"
        if action == "repair":
            if self.installation.get("editable"):
                return
            if not messagebox.askyesno(
                "miniworlds reparieren",
                "Die Pakete werden zuerst heruntergeladen. Danach werden ausschließlich miniworlds und seine Paketinformationen gesichert und neu installiert.\n\n"
                "Bei einem Fehler wird die bisherige miniworlds-Installation wiederhergestellt. Andere von pip ergänzte Abhängigkeiten können erhalten bleiben.\n\n"
                f"Sicherungsordner: {backup_root}\n\nReparatur starten?",
                parent=self,
            ):
                return
        self.operation = action
        self.status.set(
            "miniworlds wird repariert …"
            if action == "repair"
            else "miniworlds wird installiert / aktualisiert …"
        )
        self.append("\n--- " + self.status.get() + " ---\n")
        self.set_busy(True)

        def work():
            try:
                result = run_worker(
                    self.executable,
                    action,
                    lambda line: self.events.put(("log", line)),
                    backup_root if action == "repair" else None,
                )
                self.events.put(("changed", result))
            except Exception as error:  # noqa: BLE001 -- report background installation failure
                self.events.put(("failed", str(error)))

        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        if self.closed:
            return
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log":
                    self.append(value)
                elif kind == "checked":
                    self.installation, self.versions = value
                    self.show_state()
                    self.set_busy(False)
                elif kind == "changed":
                    self.append(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
                    if value.get("ok"):
                        self.installation = value
                        self.show_state()
                        if value.get("backup"):
                            self.append("Sicherung: " + value["backup"] + "\n")
                        if self.selected():
                            get_runner().restart_backend(clean=True)
                    else:
                        self.status.set(
                            value.get("error", "Installation fehlgeschlagen")
                            + "\n\n"
                            + installation_hint(self.log + value.get("error", ""))
                        )
                    self.set_busy(False)
                elif kind == "failed":
                    self.append(value + "\n")
                    self.status.set(
                        "Prüfung oder Installation fehlgeschlagen.\n"
                        + installation_hint(self.log)
                    )
                    self.set_busy(False)
        except queue.Empty:
            pass
        self.after(50, self.poll)

    def save_log(self):
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            parent=self,
            title="Installationsprotokoll speichern",
            defaultextension=".txt",
            initialfile="miniworlds-installation.txt",
        )
        if filename:
            try:
                Path(filename).write_text(
                    self.status.get()
                    + "\n\nPython: "
                    + self.executable
                    + "\n\n"
                    + self.log,
                    encoding="utf-8",
                )
            except OSError as error:
                messagebox.showerror("Protokoll", str(error), parent=self)

    def close(self):
        if self.busy and self.operation in {"install", "repair"}:
            return
        self.closed = True
        self.destroy()
