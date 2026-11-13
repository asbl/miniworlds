"""Tk views and the small, version-bound adapter to Thonny's package manager."""

import difflib
import importlib.metadata
import json
import os
import subprocess
import sys
import sysconfig
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from thonny import get_runner, get_workbench, ui_utils

from .core import (
    EVENTS,
    EXAMPLES,
    IMAGE_EXTENSIONS,
    MODES,
    SOUND_EXTENSIONS,
    TOPICS,
    CodeEdit,
    check_code,
    contextual_topic,
    create_project,
    event_code,
    event_edit,
    events_for,
    filter_examples,
    import_media,
    learning_help,
    media_call,
    project_mode,
    project_root,
    save_project_mode,
    targets_for,
    teaching_project_code,
)


def install_library():
    wb = get_workbench()
    runner = get_runner()
    proxy = runner.get_backend_proxy() if runner else None
    if proxy is None or not runner.is_waiting_toplevel_command():
        messagebox.showinfo(
            "miniworlds installieren",
            "Bitte zuerst das Programm stoppen und den Python-Interpreter starten.",
            parent=wb,
        )
        return
    # The engine needs desktop CPython, not MicroPython/CircuitPython.
    from thonny.plugins.cpython_frontend.cp_front import LocalCPythonProxy

    if not isinstance(proxy, LocalCPythonProxy):
        messagebox.showinfo(
            "Python auswählen",
            "Wähle unter Extras → Optionen → Interpreter einen lokalen Python-3-Interpreter (ab 3.10). miniworlds benötigt eine grafische Desktop-Umgebung.",
            parent=wb,
        )
        return
    executable = proxy.get_target_executable()
    if not executable:
        messagebox.showinfo(
            "Python startet noch",
            "Bitte warte kurz und öffne die Installationshilfe erneut.",
            parent=wb,
        )
        return
    from .installer import LibraryDialog

    existing = getattr(wb, "_miniworlds_install_dialog", None)
    if existing is not None and existing.winfo_exists():
        existing.lift()
        return
    dialog = LibraryDialog(wb, executable)
    wb._miniworlds_install_dialog = dialog
    ui_utils.show_dialog(dialog)


def contextual_help():
    view = get_workbench().show_view("MiniworldsView")
    if isinstance(view, MiniworldsView):
        view.context_help()


class MiniworldsView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.current_project = None
        self.current_filename = None
        self.context_kind = None
        self.help_stage = 0
        self.example_stage = 0
        self.audio_process = None
        self.status_process = None
        self.status_generation = 0
        self.gallery_images = []
        self.gallery_tiles = []
        self.check_results = []
        self.media_project = None
        self.mode = tk.StringVar(
            value=MODES.get(get_workbench().get_option("miniworlds.mode"), MODES["E2"])
        )
        self.project_label = ttk.Label(
            self, text="Projekt: noch keine gespeicherte Datei", wraplength=420
        )
        self.project_label.grid(row=0, column=0, sticky="ew", padx=5)
        mode = ttk.Combobox(
            self,
            textvariable=self.mode,
            values=list(MODES.values()),
            state="readonly",
            width=39,
        )
        mode.grid(row=1, column=0, sticky="ew", padx=5, pady=4)
        mode.bind("<<ComboboxSelected>>", self.change_mode)
        ttk.Button(
            self, text="Installation & Interpreter prüfen", command=self.show_status
        ).grid(row=2, column=0, sticky="ew", padx=5)
        self.section = tk.StringVar(value="Hilfe")
        self.section_box = ttk.Combobox(
            self, textvariable=self.section, state="readonly"
        )
        self.section_box.grid(row=3, column=0, sticky="ew", padx=5, pady=4)
        self.section_box.bind("<<ComboboxSelected>>", lambda e: self.select_section())
        style = ttk.Style(self)
        style.layout("Miniworlds.TNotebook.Tab", [])
        self.tabs = ttk.Notebook(self, style="Miniworlds.TNotebook")
        self.tabs.bind("<<NotebookTabChanged>>", lambda e: self.update_section())
        self.tabs.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
        self.build_help()
        self.build_templates()
        self.build_events()
        self.build_examples()
        self.build_media()
        self.build_checks()
        self.build_status()
        self.build_lab()
        self.section_box.configure(
            values=[self.tabs.tab(tab, "text") for tab in self.tabs.tabs()]
        )
        self.refresh_learning()
        self.sync_project()
        self.bind("<Destroy>", self.cleanup, add=True)

    def build_lab(self):
        frame = self.tab("Objektlabor")
        self.note(
            frame,
            "Objekte wie in BlueJ ausprobieren: Klassen ansehen, Objekte erzeugen, Methoden aufrufen und Zustandsänderungen vergleichen. E2 zeigt Objekte, Q1 ergänzt Klassen und Vererbung.",
        )
        self.button(frame, "Objektlabor öffnen …", self.open_lab)
        self.note(
            frame,
            "Benötigt miniworlds ab 4.4.0.12. Das Programm läuft im ausgewählten Thonny-Interpreter. Stop/Restart beendet die Sitzung. Bei Codeänderungen muss es neu geladen werden.",
        )
        self.lab_dialog = None

    def open_lab(self):
        if self.lab_dialog and self.lab_dialog.winfo_exists():
            self.lab_dialog.lift()
            return
        from .live_view import ConnectedLabDialog

        self.lab_dialog = ConnectedLabDialog(self)

    def select_section(self):
        for tab in self.tabs.tabs():
            if self.tabs.tab(tab, "text") == self.section.get():
                self.tabs.select(tab)
                break

    def update_section(self):
        if self.tabs.select():
            self.section.set(self.tabs.tab(self.tabs.select(), "text"))

    def tab(self, title):
        frame = ttk.Frame(self.tabs, padding=5)
        self.tabs.add(frame, text=title)
        return frame

    def button(self, parent, title, action):
        button = ttk.Button(parent, text=title, command=action)
        button.pack(fill="x", pady=2)
        return button

    def combo(self, parent, variable, values, action=None, readonly=True):
        box = ttk.Combobox(
            parent,
            textvariable=variable,
            values=list(values),
            state="readonly" if readonly else "normal",
        )
        box.pack(fill="x", pady=2)
        if action:
            box.bind("<<ComboboxSelected>>", lambda event: action())
        return box

    def note(self, parent, text):
        label = ttk.Label(parent, text=text, wraplength=400, justify="left")
        label.pack(fill="x", pady=3)
        label.bind(
            "<Configure>",
            lambda event: label.configure(wraplength=max(100, event.width - 8)),
        )
        return label

    def output(self, parent, height=10):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        widget = tk.Text(frame, height=height, width=40, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(frame, command=widget.yview)
        widget.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        widget.pack(fill="both", expand=True)
        return widget

    def display(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    @property
    def mode_key(self):
        return next(k for k, value in MODES.items() if value == self.mode.get())

    def editor(self, notify=True):
        editor = get_workbench().get_editor_notebook().get_current_editor()
        if editor is None and notify:
            self.info("Öffne zuerst eine Python-Datei.")
        return editor

    def info(self, text):
        messagebox.showinfo("miniworlds", text, parent=self)

    def sync_project(self):
        editor = self.editor(False)
        filename = editor.get_filename() if editor else None
        if filename != self.current_filename:
            self.current_filename = filename
            self.current_project = (
                project_root(filename)
                if filename and Path(filename).is_file()
                else None
            )
            self.project_label.configure(
                text=f"Projekt: {self.current_project.name}"
                if self.current_project
                else "Projekt: Datei zuerst lokal speichern"
            )
            default = get_workbench().get_option("miniworlds.mode")
            try:
                key = (
                    project_mode(self.current_project, default)
                    if self.current_project
                    else default
                )
                self.mode.set(MODES.get(key, MODES["E2"]))
            except (OSError, ValueError) as error:
                self.project_label.configure(text=f"Projektdatei prüfen: {error}")
            self.refresh_learning()
            self.discover_targets(notify=False)
            self.stop_audio()
            self.clear_media()
        self.sync_job = self.after(500, self.sync_project)

    def change_mode(self, event=None):
        if self.current_project:
            try:
                save_project_mode(self.current_project, self.mode_key)
            except (OSError, ValueError) as error:
                self.info(f"Modus konnte nicht gespeichert werden: {error}")
                return
        else:
            get_workbench().set_option("miniworlds.mode", self.mode_key)
        self.refresh_learning()
        self.discover_targets(notify=False)

    def refresh_learning(self):
        self.help_stage = 0
        self.context_kind = None
        self.example_stage = 0
        self.refresh_help()
        self.preview_project()
        self.preview_example()
        self.preview_event()

    def build_help(self):
        self.help_tab = self.tab("Hilfe")
        self.topic = tk.StringVar(value="World")
        self.combo(
            self.help_tab, self.topic, list(TOPICS) + list(EVENTS), self.reset_help
        )
        self.button(self.help_tab, "Hilfe am Cursor (Strg+F1)", self.context_help)
        self.button(
            self.help_tab, "Nächster Schritt: Hinweis / Beispiel", self.reveal_help
        )
        self.help_output = self.output(self.help_tab)

    def reset_help(self):
        self.help_stage = 0
        self.context_kind = None
        self.refresh_help()

    def reveal_help(self):
        self.help_stage = min(2, self.help_stage + 1)
        self.refresh_help()

    def refresh_help(self):
        self.display(
            self.help_output,
            learning_help(
                self.topic.get(), self.mode_key, self.context_kind, self.help_stage
            ),
        )

    def context_help(self):
        editor = self.editor()
        if not editor:
            return
        text = editor.get_code_view().text
        line, column = map(int, text.index("insert").split("."))
        try:
            topic, kind = contextual_topic(editor.get_content(), line, column)
        except SyntaxError:
            topic, kind = "", None
        try:
            selected = text.get("sel.first", "sel.last").strip()
            if selected in TOPICS or selected in EVENTS:
                topic = selected
        except tk.TclError:
            pass
        self.help_stage = 0
        self.context_kind = kind
        if topic in TOPICS or topic in EVENTS:
            self.topic.set(topic)
            self.refresh_help()
        else:
            self.display(
                self.help_output,
                MODES[self.mode_key]
                + "\n\nKeine eigene Hilfe an dieser Stelle. Wähle oben ein Thema. Bei unvollständiger Syntax kann der Objekttyp noch nicht erkannt werden.",
            )
        self.tabs.select(self.help_tab)

    def build_templates(self):
        self.project_tab = self.tab("Vorlagen")
        self.kind = tk.StringVar(value="Pixelwelt")
        self.combo(
            self.project_tab,
            self.kind,
            ["Pixelwelt", "Kachelwelt"],
            self.preview_project,
        )
        self.note(
            self.project_tab,
            "Vorlagen enthalten eine kleine Aufgabe und Kommentare passend zum gewählten Unterrichtsmodus.",
        )
        self.button(self.project_tab, "Neues Projekt anlegen …", self.new_project)
        self.project_output = self.output(self.project_tab)

    def preview_project(self):
        self.display(
            self.project_output, teaching_project_code(self.mode_key, self.kind.get())
        )

    def new_project(self, example=False):
        parent = filedialog.askdirectory(
            parent=self, title="Übergeordneten Projektordner wählen"
        )
        if not parent:
            return
        name = simpledialog.askstring(
            "Projekt", "Name des neuen Projektordners:", parent=self
        )
        if name is None:
            return
        try:
            selected = self.example.get() if example else "Grundgerüst"
            if selected not in EXAMPLES:
                raise ValueError("Bitte zuerst ein Beispiel auswählen.")
            code = teaching_project_code(
                self.mode_key, "Pixelwelt" if example else self.kind.get(), selected
            )
            path = create_project(parent, name, code)
            save_project_mode(path.parent, self.mode_key)
            get_workbench().get_editor_notebook().show_file(str(path))
        except (OSError, ValueError) as error:
            self.info(str(error))

    def build_events(self):
        self.events_tab = self.tab("Ereignisse")
        self.note(
            self.events_tab,
            "E2: World/Actor-Objekt · Q1: World/Actor-Klasse. Vorhandene Ereignisse werden geöffnet.",
        )
        self.target = tk.StringVar(value="")
        self.target_box = self.combo(
            self.events_tab, self.target, [], self.preview_event
        )
        self.button(self.events_tab, "Ziele aus Editor laden", self.discover_targets)
        self.event = tk.StringVar(value="act")
        self.event_box = self.combo(
            self.events_tab, self.event, EVENTS, self.preview_event
        )
        self.button(
            self.events_tab, "Einfügen / vorhandenes Ereignis öffnen", self.insert_event
        )
        self.event_output = self.output(self.events_tab)

    def discover_targets(self, notify=True):
        editor = self.editor(notify)
        try:
            targets = targets_for(editor.get_content(), self.mode_key) if editor else {}
        except SyntaxError:
            targets = {}
            if notify:
                self.info("Bitte zuerst die Python-Syntax korrigieren.")
        self.targets = targets
        names = list(targets)
        self.target_box.configure(values=names)
        if self.target.get() not in names:
            self.target.set(names[0] if names else "")
        self.preview_event()

    def preview_event(self):
        target = getattr(self, "targets", {}).get(self.target.get())
        allowed = events_for(target.kind) if target else []
        self.event_box.configure(values=allowed)
        if self.event.get() not in allowed:
            self.event.set(allowed[0] if allowed else "")
        if not target:
            self.display(
                self.event_output,
                MODES[self.mode_key]
                + "\n\nLade zuerst ein erkennbares World-/Actor-Ziel aus dem Editor. Eigene Unterklassen und Importaliasnamen werden berücksichtigt.",
            )
            return
        event = self.event.get()
        self.display(
            self.event_output,
            MODES[self.mode_key]
            + f" · {target.kind}: {target.name}\n\n"
            + EVENTS[event][1]
            + "\n\n"
            + event_code(self.mode_key, target.name, event),
        )

    def insert_event(self):
        editor = self.editor()
        if not editor or not self.target.get() or not self.event.get():
            return
        try:
            code = editor.get_content()
            edit = event_edit(code, self.mode_key, self.target.get(), self.event.get())
            if edit.existing:
                self.goto(editor, edit.line)
                return
            self.review_edit(editor, code, edit, "Ereignis einfügen")
        except (ValueError, SyntaxError) as error:
            self.info(str(error))

    def index_at(self, code, offset):
        prefix = code[:offset]
        return f"{prefix.count(chr(10)) + 1}.{len(prefix.rsplit(chr(10), 1)[-1])}"

    def apply_edit(self, editor, original, edit):
        if editor not in get_workbench().get_editor_notebook().get_all_editors():
            self.info("Die Datei wurde geschlossen. Bitte erneut öffnen.")
            return False
        if editor.get_content() != original:
            self.info(
                "Der Code wurde inzwischen geändert. Bitte die Vorschau neu erstellen."
            )
            return False
        edit.apply(original)
        text = editor.get_code_view().text
        # Disable automatic separators so delete+insert is exactly one undo unit.
        previous = text.cget("autoseparators")
        text.configure(autoseparators=False)
        try:
            text.edit_separator()
            start = self.index_at(original, edit.start)
            if edit.end > edit.start:
                text.delete(start, self.index_at(original, edit.end))
            if edit.replacement:
                text.insert(start, edit.replacement)
            text.edit_separator()
        finally:
            text.configure(autoseparators=previous)
        self.goto(editor, edit.line)
        return True

    def review_edit(self, editor, original, edit, title):
        try:
            result = edit.apply(original)
        except (ValueError, SyntaxError) as error:
            self.info(f"Keine gültige Änderung möglich: {error}")
            return
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self.winfo_toplevel())
        dialog.geometry("760x480")
        self.note(
            dialog,
            "Prüfe die Änderung. Übernehmen ist als ein Schritt rückgängig machbar.",
        )
        output = self.output(dialog)
        diff = "".join(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                result.splitlines(keepends=True),
                fromfile="Vorher",
                tofile="Nachher",
            )
        )
        self.display(output, diff)

        def apply():
            if self.apply_edit(editor, original, edit):
                dialog.destroy()

        self.button(dialog, "Änderung übernehmen", apply)
        self.button(dialog, "Schließen", dialog.destroy)

    def goto(self, editor, line):
        notebook = get_workbench().get_editor_notebook()
        if editor not in notebook.get_all_editors():
            self.info(
                "Die zugehörige Datei wurde geschlossen. Bitte erneut öffnen und prüfen."
            )
            return
        notebook.select(editor)
        text = editor.get_code_view().text
        text.mark_set("insert", f"{line}.0")
        text.see(f"{line}.0")
        text.focus_set()

    def build_examples(self):
        self.example_tab = self.tab("Beispiele")
        self.example_topic = tk.StringVar(value="Alle")
        self.example_level = tk.StringVar(value="Alle")
        self.combo(
            self.example_tab,
            self.example_topic,
            ["Alle", "Einstieg", "Bewegung", "Eingabe"],
            self.filter_examples,
        )
        self.combo(
            self.example_tab,
            self.example_level,
            ["Alle", "Einstieg", "Fortgeschritten"],
            self.filter_examples,
        )
        self.example = tk.StringVar(value="Bewegung")
        self.example_box = self.combo(
            self.example_tab, self.example, EXAMPLES, self.reset_example
        )
        self.button(
            self.example_tab, "Nächster Schritt: Hinweis / Code", self.reveal_example
        )
        self.button(
            self.example_tab,
            "Als neues Projekt öffnen …",
            lambda: self.new_project(example=True),
        )
        self.example_output = self.output(self.example_tab)

    def filter_examples(self):
        names = filter_examples(self.example_topic.get(), self.example_level.get())
        self.example_box.configure(values=names)
        if self.example.get() not in names:
            self.example.set(names[0] if names else "")
        self.reset_example()

    def reset_example(self):
        self.example_stage = 0
        self.preview_example()

    def reveal_example(self):
        self.example_stage = min(2, self.example_stage + 1)
        self.preview_example()

    def preview_example(self):
        item = EXAMPLES.get(self.example.get())
        if item is None:
            self.display(
                self.example_output, "Keine Beispiele für diese Filterkombination."
            )
            return
        text = (
            MODES[self.mode_key]
            + f" · {item.topic} · {item.level}\n\nErwartetes Verhalten: {item.behavior}\n\nAufgabe: {item.task}"
        )
        if self.example_stage >= 1:
            text += "\n\nHinweis: " + item.hint
        if self.example_stage >= 2:
            text += "\n\n" + teaching_project_code(self.mode_key, example=item.name)
        self.display(self.example_output, text)

    def build_media(self):
        self.media_tab = self.tab("Bilder & Sounds")
        canvas = tk.Canvas(self.media_tab, height=420, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.media_tab, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        content = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfigure(window, width=e.width)
        )
        self.note(
            content,
            "Bilder und Sounds im aktuellen Projekt. PNG/JPEG/WebP und weitere Formate werden als Miniaturen angezeigt.",
        )
        bar = ttk.Frame(content)
        bar.pack(fill="x")
        ttk.Button(bar, text="Importieren …", command=self.import_files).pack(
            side="left", expand=True, fill="x"
        )
        ttk.Button(bar, text="Aktualisieren", command=self.refresh_media).pack(
            side="left", expand=True, fill="x"
        )
        self.media = ttk.Treeview(
            content, columns=("size", "alpha"), selectmode="browse", height=5
        )
        self.media.heading("#0", text="Datei")
        self.media.heading("size", text="Maße / Typ")
        self.media.heading("alpha", text="Transparenz")
        self.media.column("#0", width=150, stretch=True)
        self.media.column("size", width=90, stretch=False)
        self.media.column("alpha", width=80, stretch=False)
        self.media.pack(fill="both", expand=True)
        self.media.bind("<<TreeviewSelect>>", self.media_selected)
        gallery_frame = ttk.Frame(content)
        gallery_frame.pack(fill="both", expand=True)
        self.gallery = tk.Canvas(gallery_frame, height=140, highlightthickness=0)
        scroll = ttk.Scrollbar(gallery_frame, command=self.gallery.yview)
        self.gallery.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.gallery.pack(fill="both", expand=True)
        self.gallery_body = ttk.Frame(self.gallery)
        self.gallery_window = self.gallery.create_window(
            (0, 0), window=self.gallery_body, anchor="nw"
        )
        self.gallery_body.bind(
            "<Configure>",
            lambda e: self.gallery.configure(scrollregion=self.gallery.bbox("all")),
        )
        self.gallery.bind("<Configure>", self.resize_gallery)
        self.media_info = self.note(content, "")
        self.media_target = tk.StringVar(value="player")
        self.media_target_box = self.combo(
            content,
            self.media_target,
            ["player", "world", "self", "self.world"],
            readonly=False,
        )
        for title, action in [
            ("Pfad am Cursor einfügen", self.insert_media),
            ("Als Kostüm einfügen …", lambda: self.insert_media_call("Kostüm")),
            (
                "Als Hintergrund einfügen …",
                lambda: self.insert_media_call("Hintergrund"),
            ),
            ("Sound-Aufruf einfügen …", lambda: self.insert_media_call("Sound")),
        ]:
            self.button(content, title, action)
        controls = ttk.Frame(content)
        controls.pack(fill="x")
        ttk.Button(controls, text="▶ Sound", command=self.play_audio).pack(side="left")
        ttk.Button(controls, text="■ Stopp", command=self.stop_audio).pack(side="left")
        self.volume = tk.DoubleVar(value=60)
        ttk.Scale(
            controls, from_=0, to=100, variable=self.volume, command=self.set_volume
        ).pack(side="left", fill="x", expand=True)
        self.note(
            content,
            "Lautstärke: 0–100 % · Tonvorschau läuft in einem separaten Prozess.",
        )
        self.button(content, "Extern öffnen", self.preview_media)
        self.button(content, "Datei entfernen …", self.delete_media)

    def project_dir(self):
        editor = self.editor()
        if editor is None:
            return None
        filename = editor.get_filename()
        if not filename or not Path(filename).is_file():
            self.info(
                "Speichere die Python-Datei zuerst in einem lokalen Projektordner."
            )
            return None
        return project_root(filename)

    def clear_media(self):
        self.media.delete(*self.media.get_children())
        for child in self.gallery_body.winfo_children():
            child.destroy()
        self.gallery_images = []
        self.gallery_tiles = []
        self.media_info.configure(
            text="Dateiliste aktualisieren, um dieses Projekt anzuzeigen."
        )
        self.media_project = None

    def import_files(self):
        project = self.project_dir()
        if project is None:
            return
        files = filedialog.askopenfilenames(
            parent=self,
            title="Bilder oder Sounds importieren",
            filetypes=[
                (
                    "Bilder und Sounds",
                    "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.wav *.ogg *.mp3",
                ),
                ("Alle Dateien", "*"),
            ],
        )
        errors = []
        for filename in files:
            try:
                import_media(filename, project)
            except (OSError, ValueError) as error:
                errors.append(f"{Path(filename).name}: {error}")
        self.refresh_media()
        if errors:
            self.info("\n".join(errors))

    def refresh_media(self):
        project = self.project_dir()
        if project is None:
            return
        self.stop_audio()
        self.clear_media()
        self.media_project = project
        from PIL import Image, ImageDraw, ImageTk

        count = 0
        for folder in ("images", "sounds"):
            for path in sorted((project / folder).rglob("*")):
                if (
                    not path.is_file()
                    or path.suffix.lower() not in IMAGE_EXTENSIONS | SOUND_EXTENSIONS
                ):
                    continue
                relative = path.relative_to(project).as_posix()
                size, alpha = path.suffix[1:].upper(), "—"
                thumbnail = None
                if path.suffix.lower() in IMAGE_EXTENSIONS:
                    try:
                        with Image.open(path) as image:
                            size = f"{image.width} × {image.height}"
                            rgba = image.convert("RGBA")
                            alpha = (
                                "Ja"
                                if rgba.getchannel("A").getextrema()[0] < 255
                                else "Nein"
                            )
                            rgba.thumbnail((100, 75))
                            checker = Image.new("RGBA", (100, 75), "white")
                            draw = ImageDraw.Draw(checker)
                            for y in range(0, 75, 10):
                                for x in range(0, 100, 10):
                                    if (x // 10 + y // 10) % 2:
                                        draw.rectangle(
                                            (x, y, x + 9, y + 9), fill="#d0d0d0"
                                        )
                            checker.alpha_composite(
                                rgba, ((100 - rgba.width) // 2, (75 - rgba.height) // 2)
                            )
                            thumbnail = ImageTk.PhotoImage(checker)
                    except (OSError, ValueError, Image.DecompressionBombError):
                        size, alpha = "Lesefehler", "—"
                self.media.insert(
                    "", "end", iid=relative, text=relative, values=(size, alpha)
                )
                if thumbnail:
                    self.gallery_images.append(thumbnail)
                    tile = ttk.Frame(self.gallery_body, padding=2)
                    tile.grid(row=count // 2, column=count % 2, sticky="nsew")
                    button = ttk.Button(
                        tile,
                        image=thumbnail,
                        command=lambda name=relative: self.select_media(name),
                    )
                    button.pack()
                    ttk.Label(
                        tile,
                        text=f"{path.name}\n{size} · α: {alpha}",
                        wraplength=145,
                        justify="center",
                    ).pack()
                    self.gallery_tiles.append(tile)
                    count += 1
        columns = max(1, self.gallery.winfo_width() // 150)
        for index, tile in enumerate(self.gallery_tiles):
            tile.grid(row=index // columns, column=index % columns, sticky="nsew")
        self.media_info.configure(
            text="Datei auswählen. Schachbrettmuster zeigt transparente Bereiche."
        )
        try:
            names = list(targets_for(self.editor().get_content(), "E2"))
            self.media_target_box.configure(values=names + ["self", "self.world"])
            self.media_target.set(
                names[0] if names and self.mode_key == "E2" else "self"
            )
        except SyntaxError:
            pass

    def resize_gallery(self, event):
        self.gallery.itemconfigure(self.gallery_window, width=event.width)
        columns = max(1, event.width // 150)
        for index, tile in enumerate(self.gallery_tiles):
            tile.grid(row=index // columns, column=index % columns, sticky="nsew")

    def select_media(self, name):
        self.media.selection_set(name)
        self.media.see(name)

    def selected_media(self):
        selection = self.media.selection()
        if not selection or not self.media_project:
            self.info("Wähle zuerst eine Datei aus der Liste.")
            return None
        return self.media_project / selection[0]

    def media_selected(self, event=None):
        selection = self.media.selection()
        if not selection or not self.media_project:
            return
        path = self.media_project / selection[0]
        try:
            self.media_info.configure(
                text=f"{path.name} · {path.stat().st_size:,} Bytes"
            )
        except OSError as error:
            self.media_info.configure(text=str(error))

    def preview_media(self):
        path = self.selected_media()
        if path:
            webbrowser.open(path.resolve().as_uri())

    def media_reference(self, path):
        filename = self.editor().get_filename()
        return Path(os.path.relpath(path, Path(filename).parent)).as_posix()

    def insert_media(self):
        path = self.selected_media()
        if not path or self.project_dir() != self.media_project:
            return
        text = self.editor().get_code_view().text
        text.edit_separator()
        text.insert(
            "insert", json.dumps(self.media_reference(path), ensure_ascii=False)
        )
        text.edit_separator()

    def insert_media_call(self, purpose):
        path = self.selected_media()
        if not path or self.project_dir() != self.media_project:
            return
        if (purpose == "Sound") != (path.suffix.lower() in SOUND_EXTENSIONS):
            self.info(
                "Bitte eine Sounddatei für Sound oder eine Bilddatei für Kostüm/Hintergrund wählen."
            )
            return
        editor = self.editor()
        code = editor.get_content()
        text = editor.get_code_view().text
        try:
            target = self.media_target.get()
            line, column = map(int, text.index("insert").split("."))
            source_lines = code.splitlines(keepends=True)
            source_line = source_lines[line - 1] if line <= len(source_lines) else ""
            if source_line.strip():
                raise ValueError(
                    "Setze den Cursor für einen vollständigen Aufruf auf eine leere, passend eingerückte Codezeile."
                )
            call = media_call(self.media_reference(path), purpose, target)
            probe = source_line[:column] + call
            # Identify self in its actual surrounding class, not by mode alone.
            probe_code = (
                "".join(source_lines[: line - 1])
                + probe
                + "\n"
                + "".join(source_lines[line:])
            )
            _, kind = contextual_topic(
                probe_code, line, len(probe) - len(call) + len(target) + 1
            )
            if kind and (
                (purpose == "Kostüm" and kind != "Actor")
                or (purpose == "Hintergrund" and kind != "World")
            ):
                raise ValueError(
                    "Das gewählte Ziel passt nicht zu diesem Medienaufruf."
                )
            offset = sum(len(value) for value in source_lines[: line - 1]) + column
            edit = CodeEdit(offset, offset, call, line)
            self.review_edit(editor, code, edit, f"{purpose}-Aufruf einfügen")
        except (ValueError, SyntaxError) as error:
            self.info(str(error))

    def delete_media(self):
        path = self.selected_media()
        if not path or self.project_dir() != self.media_project:
            return
        if messagebox.askyesno(
            "Datei entfernen", f"{path.name} aus dem Projekt löschen?", parent=self
        ):
            try:
                self.stop_audio()
                path.unlink()
                self.refresh_media()
            except OSError as error:
                self.info(str(error))

    def play_audio(self):
        path = self.selected_media()
        if not path:
            return
        if path.suffix.lower() not in SOUND_EXTENSIONS:
            self.info("Wähle eine Sounddatei.")
            return
        self.stop_audio()
        try:
            self.audio_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "thonnycontrib.miniworlds.audio",
                    str(path),
                    str(self.volume.get() / 100),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
            )
            self.audio_path = path
            self.media_info.configure(text=f"Wiedergabe: {path.name}")
            process = self.audio_process
            self.after(100, lambda: self.poll_audio(process))
        except OSError as error:
            self.info(str(error))

    def set_volume(self, value):
        process = self.audio_process
        if process and process.poll() is None:
            try:
                process.stdin.write(str(float(value) / 100) + "\n")
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

    def poll_audio(self, process):
        if self.audio_process is not process:
            return
        if process.poll() is None:
            self.after(100, lambda: self.poll_audio(process))
            return
        output = process.stdout.read()
        error = ""
        for line in output.splitlines():
            try:
                error = json.loads(line).get("error", "")
            except (ValueError, AttributeError):
                pass
        self.stop_audio()
        self.media_info.configure(
            text=f"Tonvorschau fehlgeschlagen: {error}"
            if error
            else "Wiedergabe beendet."
        )

    def stop_audio(self):
        process = self.audio_process
        self.audio_process = None
        if process:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
            for stream in (process.stdin, process.stdout):
                if stream:
                    stream.close()

    def build_checks(self):
        self.check_tab = self.tab("Prüfung")
        self.note(
            self.check_tab,
            "Fehler sind konkret feststellbar. Hinweise können durch weitere Dateien oder dynamischen Code erklärt sein.",
        )
        self.button(self.check_tab, "Aktuellen Code prüfen", self.check)
        self.findings = ttk.Treeview(
            self.check_tab, columns=("line", "severity"), height=6, selectmode="browse"
        )
        self.findings.heading("#0", text="Ergebnis")
        self.findings.heading("line", text="Zeile")
        self.findings.heading("severity", text="Art")
        self.findings.column("#0", width=260)
        self.findings.column("line", width=45, stretch=False)
        self.findings.column("severity", width=70, stretch=False)
        self.findings.pack(fill="both", expand=True)
        self.findings.bind("<<TreeviewSelect>>", self.show_finding)
        self.button(self.check_tab, "Zur Codezeile", self.goto_finding)
        self.fix_button = self.button(
            self.check_tab, "Korrekturvorschau …", self.preview_fix
        )
        self.fix_button.configure(state="disabled")
        self.check_output = self.output(self.check_tab)

    def check(self):
        editor = self.editor()
        if not editor:
            return
        filename = editor.get_filename()
        project = (
            Path(filename).parent if filename and Path(filename).is_file() else None
        )
        self.checked_editor = editor
        self.checked_code = editor.get_content()
        self.check_results = check_code(self.checked_code, project, self.mode_key)
        self.findings.delete(*self.findings.get_children())
        self.fix_button.configure(state="disabled")
        for index, finding in enumerate(self.check_results):
            self.findings.insert(
                "",
                "end",
                iid=str(index),
                text=finding.message,
                values=(finding.line, finding.severity),
            )
        self.display(
            self.check_output,
            "Wähle ein Ergebnis für Erklärung und mögliche Korrektur."
            if self.check_results
            else "Keine Hinweise aus den miniworlds-Prüfregeln. Dies ist keine vollständige Korrektheitsprüfung.",
        )

    def selected_finding(self):
        selection = self.findings.selection()
        return self.check_results[int(selection[0])] if selection else None

    def show_finding(self, event=None):
        finding = self.selected_finding()
        if finding:
            self.display(
                self.check_output,
                f"{MODES[self.mode_key]} · {finding.severity} · Zeile {finding.line}\n\n{finding.message}\n\n{finding.explanation or 'Prüfe diese Stelle im Zusammenhang mit dem restlichen Projekt.'}",
            )
            self.fix_button.configure(state="normal" if finding.fix else "disabled")
            self.goto_finding()

    def goto_finding(self):
        finding = self.selected_finding()
        if finding:
            if self.checked_editor.get_content() != self.checked_code:
                self.info("Der Code wurde geändert. Bitte erneut prüfen.")
                return
            self.goto(self.checked_editor, finding.line)

    def preview_fix(self):
        finding = self.selected_finding()
        if finding and finding.fix:
            self.review_edit(
                self.checked_editor, self.checked_code, finding.fix, "Korrektur prüfen"
            )

    def build_status(self):
        self.status_tab = self.tab("Installation")
        self.note(
            self.status_tab,
            "Das Plugin gehört zu Thonny selbst. Die Bibliothek gehört zum ausgewählten Ausführungsinterpreter. Eine Projekt-venv ändert Thonnys eigene Umgebung nicht.",
        )
        self.button(self.status_tab, "Status aktualisieren", self.refresh_status)
        self.button(
            self.status_tab,
            "Bibliothek installieren / aktualisieren …",
            install_library,
        )
        self.button(
            self.status_tab,
            "Interpreter auswählen …",
            lambda: get_workbench().show_options("interpreter"),
        )
        self.status_output = self.output(self.status_tab)

    def show_status(self):
        self.tabs.select(self.status_tab)
        self.refresh_status()

    def refresh_status(self):
        self.status_generation += 1
        generation = self.status_generation
        self.stop_status()
        try:
            distribution = importlib.metadata.distribution("thonny-miniworlds")
            plugin = f"{distribution.version}\nInstallationsort: {distribution.locate_file('')}"
        except importlib.metadata.PackageNotFoundError:
            plugin = "Entwicklungsstand (ohne installierte Paketmetadaten)"
        self.frontend_status = (
            f"Plugin in Thonny:\n{plugin}\nThonny-Python: {sys.executable}\n\n"
        )
        self.frontend_status += (
            "Thonny läuft in einer venv: "
            + ("Ja" if sys.prefix != sys.base_prefix else "Nein")
            + "\n"
        )
        if (
            sys.prefix == sys.base_prefix
            and (Path(sysconfig.get_path("stdlib")) / "EXTERNALLY-MANAGED").exists()
        ):
            self.frontend_status += "Plugin-Updates sind hier durch PEP 668 eingeschränkt. Starte Thonny aus einer eigenen venv.\n"
        self.frontend_status += "\n"
        runner = get_runner()
        proxy = runner.get_backend_proxy() if runner else None
        from thonny.plugins.cpython_frontend.cp_front import LocalCPythonProxy

        if not isinstance(proxy, LocalCPythonProxy):
            self.display(
                self.status_output,
                self.frontend_status
                + "Bitte einen lokalen Python-Interpreter auswählen.",
            )
            return
        executable = proxy.get_target_executable()
        if not executable:
            self.display(
                self.status_output,
                self.frontend_status
                + "Der Ausführungsinterpreter startet noch. Bitte erneut prüfen.",
            )
            return
        self.display(
            self.status_output,
            self.frontend_status
            + f"Ausführungsinterpreter: {executable}\nBibliotheksstatus wird gelesen …",
        )
        source = """import sys, json, sysconfig
from pathlib import Path
import importlib.metadata as m
result = {'executable': sys.executable, 'python': sys.version.split()[0],
          'venv': sys.prefix != sys.base_prefix,
          'managed': (Path(sysconfig.get_path('stdlib')) / 'EXTERNALLY-MANAGED').exists()}
try:
    d = m.distribution('miniworlds')
    result.update(version=d.version, location=str(d.locate_file('')))
except m.PackageNotFoundError:
    result.update(version=None, location=None)
print(json.dumps(result))"""
        try:
            self.status_process = subprocess.Popen(
                [executable, "-I", "-c", source],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            self.status_started = time.monotonic()
            self.after(100, lambda: self.poll_status(generation, executable))
        except OSError as error:
            self.display(self.status_output, self.frontend_status + str(error))

    def poll_status(self, generation, executable):
        if generation != self.status_generation or not self.status_process:
            return
        process = self.status_process
        runner = get_runner()
        proxy = runner.get_backend_proxy() if runner else None
        if not proxy or proxy.get_target_executable() != executable:
            self.stop_status()
            self.display(
                self.status_output,
                self.frontend_status
                + "Interpreter wurde gewechselt. Bitte erneut prüfen.",
            )
            return
        if process.poll() is None:
            if time.monotonic() - self.status_started > 10:
                self.stop_status()
                self.display(
                    self.status_output,
                    self.frontend_status
                    + "Zeitüberschreitung beim Lesen des Interpreters.",
                )
            else:
                self.after(100, lambda: self.poll_status(generation, executable))
            return
        output, error = process.communicate()
        self.status_process = None
        try:
            if process.returncode:
                raise ValueError(
                    error.strip() or "Interpreter konnte nicht abgefragt werden."
                )
            data = json.loads(output)
            text = f"Ausführungsinterpreter:\n{data['executable']}\nPython {data['python']}\nVirtuelle Umgebung: {'Ja' if data['venv'] else 'Nein'}\n\n"
            text += (
                f"miniworlds: {data['version']}\nInstallationsort: {data['location']}"
                if data["version"]
                else "miniworlds ist hier noch nicht installiert."
            )
            if tuple(map(int, data["python"].split(".")[:2])) < (3, 10):
                text += "\nPython ist zu alt; miniworlds benötigt mindestens 3.10."
            if data["managed"] and not data["venv"]:
                text += "\n\nDiese Python-Umgebung wird vom Betriebssystem verwaltet (PEP 668). Wähle für die Bibliothek eine venv. Für Plugins muss auch Thonny selbst aus einer eigenen venv gestartet werden."
            self.display(self.status_output, self.frontend_status + text)
        except (ValueError, KeyError) as error:
            self.display(
                self.status_output,
                self.frontend_status + f"Status konnte nicht gelesen werden: {error}",
            )

    def stop_status(self):
        process = self.status_process
        self.status_process = None
        if process:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=2)

    def cleanup(self, event):
        if event.widget is self:
            if hasattr(self, "sync_job"):
                self.after_cancel(self.sync_job)
            self.stop_audio()
            self.stop_status()
            if self.lab_dialog and self.lab_dialog.winfo_exists():
                self.lab_dialog.close()
