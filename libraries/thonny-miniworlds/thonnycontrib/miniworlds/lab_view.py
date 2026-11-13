"""BlueJ-style laboratory UI; the engine is only imported by the worker."""

import ast
import json
import queue
import subprocess
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from thonny import get_runner

from .lab_model import classes_in, export_calls, revision


class LabDialog(tk.Toplevel):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.title("miniworlds · Objektlabor")
        self.geometry("1050x780")
        self.minsize(750, 560)
        self.process = None
        self.highlighted = None
        self.threads = []
        self.temporary = None
        self.events = queue.Queue()
        self.data = None
        self.loaded_revision = None
        self.sent_revision = None
        self.busy = False
        self.last_error = None
        self.stale = False
        self.fields_before = {}
        self.status = tk.StringVar(
            value="Programm im Experimentiermodus laden. Es wird wie beim Starten ausgeführt, danach bleibt die Welt pausiert."
        )
        ttk.Label(self, textvariable=self.status, wraplength=950, padding=10).pack(
            fill="x"
        )
        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")
        ttk.Button(bar, text="Programm neu laden", command=self.start).pack(side="left")
        ttk.Button(bar, text="Experiment beenden", command=self.stop).pack(
            side="left", padx=8
        )
        ttk.Button(bar, text="Aufrufe in Code übernehmen …", command=self.export).pack(
            side="right"
        )
        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=10)
        left, right = ttk.Frame(panes), ttk.Frame(panes)
        panes.add(left, weight=1)
        panes.add(right, weight=2)
        self.class_header = ttk.Label(
            left, text="Klassen in dieser Datei · Doppelklick öffnet Code"
        )
        self.class_header.pack(anchor="w")
        self.diagram = tk.Canvas(left, height=230, highlightthickness=0)
        self.diagram.pack(fill="x")
        ttk.Label(
            left, text="Objektbank · mehrere Namen können dasselbe Objekt meinen"
        ).pack(anchor="w")
        self.bank = ttk.Treeview(
            left, columns=("type",), height=10, selectmode="browse"
        )
        self.bank.heading("#0", text="Namen")
        self.bank.heading("type", text="Klasse")
        self.bank.column("#0", width=200)
        self.bank.column("type", width=100)
        self.bank.pack(fill="both", expand=True)
        self.bank.bind("<<TreeviewSelect>>", self.select_object)
        ttk.Label(right, text="Zustand · geänderte Werte sind markiert").pack(
            anchor="w"
        )
        self.fields = ttk.Treeview(right, columns=("value",), height=8)
        self.fields.heading("#0", text="Attribut")
        self.fields.heading("value", text="Wert")
        self.fields.column("#0", width=130)
        self.fields.column("value", width=330)
        self.fields.tag_configure("changed", foreground="#18664b")
        self.fields.pack(fill="both", expand=True)
        self.method = tk.StringVar()
        ttk.Label(
            right, text="Methode · Herkunft und Parameter stehen in der Auswahl"
        ).pack(anchor="w")
        self.method_box = ttk.Combobox(
            right, textvariable=self.method, state="readonly"
        )
        self.method_box.pack(fill="x")
        ttk.Label(
            right,
            text='Argumente: z. B. 20, direction="right" oder ein Name aus der Objektbank',
        ).pack(anchor="w")
        self.args = tk.StringVar()
        ttk.Entry(right, textvariable=self.args).pack(fill="x")
        ttk.Button(
            right,
            text="Gewähltes Objekt als Argument einsetzen",
            command=self.use_reference,
        ).pack(anchor="w")
        ttk.Label(right, text="Vorhersage: Was wird sich ändern? (freiwillig)").pack(
            anchor="w"
        )
        self.prediction = tk.StringVar()
        ttk.Entry(right, textvariable=self.prediction).pack(fill="x")
        self.invoke_button = ttk.Button(
            right, text="Methode ausführen", command=self.invoke
        )
        self.invoke_button.pack(fill="x", pady=5)
        create = ttk.LabelFrame(right, text="Neues Objekt erzeugen", padding=5)
        create.pack(fill="x")
        self.class_name = tk.StringVar()
        self.class_box = ttk.Combobox(
            create, textvariable=self.class_name, state="readonly"
        )
        self.class_box.pack(fill="x")
        self.name = tk.StringVar(value="figur2")
        ttk.Label(create, text="Objektname").pack(anchor="w")
        ttk.Entry(create, textvariable=self.name).pack(fill="x")
        self.constructor_args = tk.StringVar(value="(100, 100)")
        ttk.Label(create, text="Konstruktorargumente").pack(anchor="w")
        ttk.Entry(create, textvariable=self.constructor_args).pack(fill="x")
        self.create_button = ttk.Button(
            create, text="Objekt erzeugen", command=self.create
        )
        self.create_button.pack(fill="x")
        ttk.Label(
            self,
            text="Aufrufprotokoll · Vorhersage → Aufruf → Ergebnis",
            padding=(10, 5),
        ).pack(anchor="w")
        self.log = tk.Text(self, height=7, wrap="word", state="disabled")
        self.log.pack(fill="x", padx=10, pady=(0, 10))
        self.methods = {}
        self.classes = {}
        if owner.mode_key == "E2":
            self.diagram.pack_forget()
            self.class_header.pack_forget()
        self.draw_classes()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(100, self.poll)
        self.controls()

    def source(self):
        editor = self.owner.editor()
        if not editor:
            raise ValueError("Öffne zuerst eine Python-Datei.")
        filename = editor.get_filename()
        if not filename or not Path(filename).is_file():
            raise ValueError("Speichere die Datei zuerst lokal.")
        return editor, filename, editor.get_content()

    def draw_classes(self):
        self.diagram.delete("all")
        try:
            _, _, source = self.source()
            rows = classes_in(source)
        except (ValueError, SyntaxError):
            rows = []
        self.class_lines = {r["name"]: r["line"] for r in rows}
        # The scrollable graph shows inheritance, including external bases.
        names = list(
            dict.fromkeys(
                [b for r in rows for b in r["bases"]] + [r["name"] for r in rows]
            )
        )
        positions = {
            name: (10 + (i % 2) * 160, 10 + (i // 2) * 65)
            for i, name in enumerate(names)
        }
        for row in rows:
            x, y = positions[row["name"]]
            for base in row["bases"]:
                bx, by = positions[base]
                self.diagram.create_line(
                    x + 75, y, bx + 75, by + 38, arrow="last", fill="#607788"
                )
        for name, (x, y) in positions.items():
            tag = "class_" + name
            self.diagram.create_rectangle(
                x, y, x + 145, y + 38, fill="#e8f1f0", outline="#60857d", tags=tag
            )
            self.diagram.create_text(x + 72, y + 19, text=name, tags=tag)
            self.diagram.tag_bind(
                tag, "<Double-Button-1>", lambda e, n=name: self.goto_class(n)
            )
        self.diagram.configure(scrollregion=self.diagram.bbox("all"))
        self.diagram.bind(
            "<MouseWheel>",
            lambda e: self.diagram.yview_scroll(-1 if e.delta > 0 else 1, "units"),
        )

    def goto_class(self, name):
        if name in self.class_lines:
            editor = self.owner.editor()
            self.owner.goto(editor, self.class_lines[name])

    def start(self):
        try:
            editor, filename, source = self.source()
            ast.parse(source)
            from thonny.plugins.cpython_frontend.cp_front import LocalCPythonProxy

            runner = get_runner()
            proxy = runner.get_backend_proxy() if runner else None
            if (
                not isinstance(proxy, LocalCPythonProxy)
                or not proxy.get_target_executable()
            ):
                raise ValueError(
                    "Wähle zuerst einen gestarteten lokalen Python-Interpreter."
                )
            self.stop()
            self.filename, self.loaded_source = filename, source
            self.editor = editor
            self.root_dir = self.owner.project_dir()
            self.loaded_revision = revision(self.root_dir, filename, source)
            self.sent_revision = self.loaded_revision
            self.temporary = tempfile.TemporaryDirectory(prefix="miniworlds-lab-")
            snapshot = Path(self.temporary.name) / "source.py"
            snapshot.write_text(source, encoding="utf-8")
            self.process = subprocess.Popen(
                [
                    proxy.get_target_executable(),
                    "-I",
                    str(Path(__file__).with_name("lab_runtime.py")),
                    "--source",
                    str(snapshot),
                    "--filename",
                    filename,
                    "--version",
                    self.loaded_revision,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            process = self.process

            def read(stream, kind):
                for line in stream:
                    self.events.put((process, kind, line))
                self.events.put((process, "eof", kind))

            for stream, kind in [
                (process.stdout, "result"),
                (process.stderr, "output"),
            ]:
                thread = threading.Thread(target=read, args=(stream, kind), daemon=True)
                self.threads.append(thread)
                thread.start()
            self.busy = True
            self.last_error = None
            self.stale = False
            self.status.set(
                "Programm wird geladen … Bei einer Endlosschleife kannst du „Experiment beenden“ wählen."
            )
            self.controls()
            self.draw_classes()
        except (ValueError, OSError, SyntaxError) as error:
            self.status.set(str(error))

    def controls(self):
        ready = bool(
            self.process
            and self.process.poll() is None
            and self.data
            and not self.busy
            and not self.stale
        )
        self.invoke_button.configure(
            state="normal" if ready and self.bank.selection() else "disabled"
        )
        self.create_button.configure(state="normal" if ready else "disabled")

    def send(self, command):
        if self.busy or not self.process or self.process.poll() is not None:
            return
        try:
            self.process.stdin.write(json.dumps(command) + "\n")
            self.process.stdin.flush()
            self.busy = True
            self.controls()
        except (OSError, BrokenPipeError) as error:
            self.status.set(str(error))

    def selected(self):
        ids = self.bank.selection()
        return next(
            (
                r
                for r in (self.data or {}).get("objects", [])
                if ids and r["handle"] == ids[0]
            ),
            None,
        )

    def select_object(self, event=None):
        row = self.selected()
        if not row:
            return
        previous = self.fields_before.get(row["handle"], {})
        self.fields.delete(*self.fields.get_children())
        for name, value in row["fields"].items():
            changed = name in previous and previous[name] != value
            self.fields.insert(
                "",
                "end",
                text=("● " if changed else "") + name,
                values=(value,),
                tags=("changed",) if changed else (),
            )
        self.fields_before[row["handle"]] = row["fields"].copy()
        self.methods = {
            f"{m['name']}{m['signature']} · {m['owner']}"
            + (" (geerbt)" if m["inherited"] else ""): m["name"]
            for m in row["methods"]
        }
        self.method_box.configure(values=list(self.methods))
        if self.method.get() not in self.methods:
            self.method.set(next(iter(self.methods), ""))
        self.controls()
        if not self.busy and self.highlighted != row["handle"]:
            self.highlighted = row["handle"]
            self.send({"action": "select", "handle": row["handle"]})

    def use_reference(self):
        row = self.selected()
        if row:
            self.args.set(
                (self.args.get() + ", " if self.args.get().strip() else "")
                + row["aliases"][0]
            )

    def invoke(self):
        row = self.selected()
        if row and not self.stale and self.method.get() in self.methods:
            self.send(
                {
                    "action": "invoke",
                    "handle": row["handle"],
                    "method": self.methods[self.method.get()],
                    "arguments": self.args.get(),
                    "prediction": self.prediction.get(),
                }
            )

    def create(self):
        if not self.stale and self.class_name.get() in self.classes:
            self.send(
                dict(
                    action="create",
                    name=self.name.get(),
                    **{"class": self.classes[self.class_name.get()]},
                    arguments=self.constructor_args.get(),
                    prediction=self.prediction.get(),
                )
            )

    def show_data(self, data):
        selection = self.bank.selection()
        self.data = data
        self.bank.delete(*self.bank.get_children())
        for row in data["objects"]:
            self.bank.insert(
                "",
                "end",
                iid=row["handle"],
                text=" = ".join(row["aliases"]),
                values=(row["type"],),
            )
        self.classes = {c["name"] + c["signature"]: c["name"] for c in data["classes"]}
        self.class_box.configure(values=list(self.classes))
        if self.class_name.get() not in self.classes:
            self.class_name.set(next(iter(self.classes), ""))
        if selection and self.bank.exists(selection[0]):
            self.bank.selection_set(selection[0])
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        for item in data["history"]:
            self.log.insert(
                "end",
                f"Vorhersage: {item['prediction'] or '—'}\n{item['code']} → {item['result']}\n",
            )
        self.log.configure(state="disabled")

    def poll(self):
        if not self.winfo_exists():
            return
        try:
            while True:
                process, kind, value = self.events.get_nowait()
                if process is not self.process:
                    continue
                if kind == "result":
                    response = json.loads(value)
                    self.busy = False
                    self.last_error = (
                        response.get("error") if not response["ok"] else None
                    )
                    if "data" in response:
                        self.show_data(response["data"])
                    self.status.set(
                        "Welt pausiert · Methoden einzeln ausprobieren."
                        if response["ok"]
                        else response["error"]
                    )
                elif kind == "output":
                    self.log.configure(state="normal")
                    self.log.insert("end", value)
                    self.log.configure(state="disabled")
                elif kind == "eof" and value == "result":
                    self.busy = False
                    self.status.set("Experiment beendet. Zum Weiterarbeiten neu laden.")
                    self.data = None
                    self.bank.delete(*self.bank.get_children())
        except queue.Empty:
            pass
        if self.process and self.process.poll() is None and self.loaded_revision:
            try:
                current = revision(
                    self.root_dir, self.filename, self.editor.get_content()
                )
                self.stale = current != self.loaded_revision
                if self.stale:
                    self.status.set(
                        "Code geändert – diese Objekte verwenden den vorherigen Stand. Bitte neu laden."
                    )
                if current != self.sent_revision and not self.busy:
                    self.sent_revision = current
                    self.send({"action": "revision", "version": current})
            except (OSError, tk.TclError):
                self.stale = True
                self.status.set(
                    "Quelldatei geschlossen oder nicht lesbar. Bitte neu laden."
                )
        self.controls()
        self.after(350, self.poll)

    def export(self):
        if (
            not self.data
            or self.stale
            or self.busy
            or not self.data.get("replay_complete", True)
        ):
            messagebox.showinfo(
                "Aufrufe übernehmen",
                "Lade den aktuellen Programmstand und führe Methoden ohne Fehler aus. Änderungen vor einem Methodenfehler können nicht vollständig als Ablauf übernommen werden.",
                parent=self,
            )
            return
        try:
            _, filename, source = self.source()
            if filename != self.filename or source != self.loaded_source:
                raise ValueError("Bitte zuerst den aktuellen Code neu laden.")
            calls = [item["code"] for item in self.data["history"]]
            if not calls:
                return
            prelude = (
                ["from miniworlds import App", *self.data["prelude"]]
                if self.data["prelude"]
                else []
            )
            updated = export_calls(source, [*prelude, *calls])
            from .core import CodeEdit

            self.owner.review_edit(
                self.editor,
                source,
                CodeEdit(0, len(source), updated, 1),
                "Experiment in Programm übernehmen",
            )
        except (ValueError, SyntaxError) as error:
            self.status.set(str(error))

    def stop(self):
        process = self.process
        self.process = None
        if process:
            if process.poll() is None:
                try:
                    process.stdin.write('{"action":"quit"}\n')
                    process.stdin.flush()
                    process.wait(timeout=0.6)
                except (OSError, subprocess.TimeoutExpired):
                    process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
        for thread in self.threads:
            thread.join(timeout=1)
        self.threads = []
        if process:
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
        self.highlighted = None
        if self.temporary:
            self.temporary.cleanup()
            self.temporary = None
        self.data = None
        self.bank.delete(*self.bank.get_children())
        self.fields.delete(*self.fields.get_children())
        self.busy = False
        self.status.set("Experiment beendet. Die Objektbank wurde geleert.")
        self.controls()

    def close(self):
        self.stop()
        self.destroy()
