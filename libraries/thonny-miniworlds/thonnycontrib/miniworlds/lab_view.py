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
from typing import ClassVar

from thonny import get_runner

from .lab_model import classes_in, export_calls, revision


class LabDialog(ttk.Frame):
    def __init__(self, owner, parent=None):
        super().__init__(parent if parent is not None else owner)
        self.owner = owner
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
        self.comparison_before = {}
        self.comparison_after = {}
        self.pending_action = None
        self.chosen_methods = {}
        self.status = tk.StringVar(
            value="Noch nicht geladen · Starte zuerst dein Programm im Labor."
        )
        self.state_title = tk.StringVar(value="Noch nicht geladen")
        # The simulation controls stay visible even when the form is scrolled.
        self.toolbar = ttk.Frame(self, padding=(8, 6))
        self.toolbar.pack(side="bottom", fill="x")
        self.toolbar_actions = ttk.Frame(self.toolbar)
        self.load_button = ttk.Button(
            self.toolbar_actions, text="↻ Laden", command=self.start
        )
        self.load_button.pack(side="left")
        self.stop_button = ttk.Button(
            self.toolbar_actions, text="■ Stopp", command=self.stop_program
        )
        self.stop_button.pack(side="left", padx=5)
        self.world_controls = ttk.Frame(self.toolbar_actions)
        self.world_controls.pack(side="left")
        self.hide_button = ttk.Button(
            self.toolbar, text="Ausblenden", command=self.back
        )
        self.state_label = ttk.Label(
            self.toolbar, textvariable=self.state_title, font="TkHeadingFont"
        )
        self.toolbar.columnconfigure(0, weight=1)
        self.toolbar.bind("<Configure>", self.layout_toolbar)
        self.world_controls.bind("<Configure>", self.layout_toolbar)
        self.layout_toolbar()
        header = ttk.Frame(self, padding=(8, 5))
        header.pack(fill="x")
        ttk.Label(header, text="Objektlabor", font="TkHeadingFont").pack(side="left")
        self.mode_label = ttk.Label(header)
        self.mode_label.pack(side="right")
        self.classes_visible = tk.BooleanVar(value=True)
        self.classes_toggle = ttk.Checkbutton(
            header,
            text="Klassen anzeigen",
            variable=self.classes_visible,
            command=self.toggle_classes,
            style="Toolbutton",
        )
        self.notice_label = ttk.Label(self, textvariable=self.status, padding=(8, 2))
        self.workspace = ttk.Panedwindow(self, orient="horizontal")
        self.workspace.pack(fill="both", expand=True)
        left = ttk.Frame(self.workspace, padding=6, width=220)
        right_host = ttk.Frame(self.workspace, padding=6)
        self.classes_host = ttk.Frame(self.workspace, padding=6, width=220)
        self.workspace.add(left, weight=1)
        self.workspace.add(right_host, weight=4)
        self._viewed_handle = None
        self.class_header = ttk.Label(
            self.classes_host, text="Klassen", font="TkHeadingFont"
        )
        self.class_header.pack(anchor="w", pady=4)
        self.diagram = tk.Canvas(
            self.classes_host, height=180, highlightthickness=0, width=195
        )
        self.diagram.pack(fill="both", expand=True)
        self.diagram_scroll = ttk.Scrollbar(
            self.classes_host, orient="horizontal", command=self.diagram.xview
        )
        self.diagram_scroll.pack(fill="x")
        self.diagram_y = ttk.Scrollbar(self.classes_host, command=self.diagram.yview)
        self.diagram_y.pack(side="right", fill="y", before=self.diagram)
        self.diagram.configure(
            xscrollcommand=self.diagram_scroll.set, yscrollcommand=self.diagram_y.set
        )
        ttk.Label(
            self.classes_host, text="Klick: Instanz erzeugen\nDoppelklick: Code öffnen"
        ).pack(fill="x")
        self.bank_heading = ttk.Label(left, font="TkHeadingFont")
        self.bank_heading.pack(anchor="w", pady=4)
        from .lab_cards import ObjectCards

        self.bank = ObjectCards(left)
        self.bank.pack(fill="both", expand=True)
        self.bank.bind("<<ObjectSelected>>", self.select_object)
        self.create_visible = tk.BooleanVar(value=False)
        self.create_toggle = ttk.Checkbutton(
            left, variable=self.create_visible, command=self.toggle_create
        )
        self.create_toggle.pack(anchor="w", pady=4)
        self.action_canvas, right = self.scroll_area(right_host)
        self.action_content = right
        self.receiver = tk.StringVar(value="Wähle links eine Figur aus.")
        ttk.Label(right, textvariable=self.receiver, font="TkHeadingFont").pack(
            fill="x", pady=(0, 6)
        )
        self.shortcuts = ttk.Frame(right)
        self.shortcuts.pack(fill="x")
        self.shortcuts.columnconfigure(0, weight=1)
        self.quick_actions = ttk.Frame(self.shortcuts)
        self.quick_buttons = []
        self.methods_visible = tk.BooleanVar(value=False)
        self.methods_toggle = ttk.Checkbutton(
            self.shortcuts,
            text="▸ Weitere Methoden",
            variable=self.methods_visible,
            command=self.toggle_methods,
            style="Toolbutton",
        )
        self.shortcuts.bind("<Configure>", self.layout_actions)
        self.quick_actions.bind("<Configure>", self.layout_actions)
        self.method_filters = ttk.Frame(right, padding=(0, 4))
        self.method_search = tk.StringVar()
        ttk.Label(self.method_filters, text="Suchen:").pack(side="left")
        self.search_entry = ttk.Entry(
            self.method_filters, textvariable=self.method_search, width=12
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(
            self.method_filters,
            text="×",
            width=2,
            command=lambda: self.method_search.set(""),
        ).pack(side="left")
        self.search_entry.bind("<Escape>", lambda e: self.method_search.set(""))
        self.method_group = tk.StringVar(value="Alle Methoden")
        ttk.Combobox(
            self.method_filters,
            state="readonly",
            width=16,
            textvariable=self.method_group,
            values=["Alle Methoden", "Bewegen", "Aussehen", "Eigene Methoden"],
        ).pack(side="left")
        self.method_search.trace_add("write", lambda *args: self.filter_methods())
        self.method_group.trace_add("write", lambda *args: self.filter_methods())
        self.method_row = ttk.Frame(right, padding=(0, 5))
        self.method_row.pack(fill="x")
        ttk.Label(self.method_row, text="Methode").pack(side="left", padx=(0, 6))
        self.method = tk.StringVar()
        self.method_box = ttk.Combobox(
            self.method_row, textvariable=self.method, state="readonly"
        )
        self.method_box.pack(side="left", fill="x", expand=True)
        self.method_box.bind("<<ComboboxSelected>>", lambda e: self.method_changed())
        self.method_help = tk.StringVar()
        self.args = tk.StringVar()
        from .lab_forms import ParameterForm

        self.method_form = ParameterForm(
            right, self.args, self.update_preview, compact=True
        )
        self.method_form.submit = self.invoke
        self.method_form.pack(fill="x", pady=4)
        self.call_bar = ttk.Frame(right, padding=(0, 4))
        self.call_bar.pack(fill="x")
        self.call_bar.columnconfigure(0, weight=1)
        self.call_bar.bind("<Configure>", self.layout_call)
        self.preview = tk.StringVar(value="Wähle zuerst ein Objekt und eine Methode.")
        self.preview_label = ttk.Label(
            self.call_bar, textvariable=self.preview, font="TkFixedFont"
        )
        self.preview_label.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.invoke_button = ttk.Button(
            self.call_bar, text="Ausführen ↵", command=self.invoke
        )
        self.invoke_button.grid(row=0, column=1, sticky="e")
        self.action_hint = tk.StringVar()
        self.action_hint_label = ttk.Label(right, textvariable=self.action_hint)
        self.result_panel = ttk.LabelFrame(right, text="Ergebnis", padding=8)
        self.result_panel.pack(fill="x", pady=5)
        self.feedback = tk.StringVar()
        ttk.Label(self.result_panel, textvariable=self.feedback).pack(fill="x")
        self.last_call = tk.StringVar(value="Noch kein Aufruf.")
        ttk.Label(
            self.result_panel, textvariable=self.last_call, font="TkFixedFont"
        ).pack(fill="x")
        self.result_summary = tk.StringVar()
        self.result_label = ttk.Label(
            self.result_panel, textvariable=self.result_summary
        )
        self.result_label.pack(fill="x")
        self.result_bar = ttk.Frame(self.result_panel)
        self.result_bar.pack(fill="x")
        self.export_button = ttk.Button(
            self.result_bar, text="Aufrufe in Code übernehmen …", command=self.export
        )
        self.more_visible = tk.BooleanVar(value=False)
        self.more_toggle = ttk.Checkbutton(
            right,
            text="▸ Mehr",
            variable=self.more_visible,
            command=self.toggle_more,
            style="Toolbutton",
        )
        self.more_toggle.pack(anchor="w", pady=3)
        self.more_frame = ttk.Frame(right, padding=(2, 6))
        self.prediction = tk.StringVar()
        self.prediction_visible = tk.BooleanVar(value=False)
        prediction_bar = ttk.Frame(self.more_frame)
        prediction_bar.pack(fill="x")
        prediction_entry = ttk.Entry(prediction_bar, textvariable=self.prediction)
        ttk.Checkbutton(
            prediction_bar,
            text="Vorhersage",
            variable=self.prediction_visible,
            command=lambda: (
                prediction_entry.pack(side="left", fill="x", expand=True)
                if self.prediction_visible.get()
                else prediction_entry.pack_forget()
            ),
        ).pack(side="left")
        ttk.Checkbutton(
            self.more_frame,
            text="Argumente als Python eingeben",
            variable=self.method_form.advanced,
            command=self.method_form.toggle,
        ).pack(anchor="w", pady=3)
        self.properties_visible = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.more_frame,
            text="Alle Eigenschaften",
            variable=self.properties_visible,
            command=self.toggle_properties,
        ).pack(anchor="w", pady=3)
        self.properties_frame = ttk.Frame(self.more_frame)
        self.fields = self.tree(self.properties_frame, ("before", "value"), height=4)
        self.fields.heading("#0", text="Attribut")
        self.fields.heading("before", text="Vorher")
        self.fields.heading("value", text="Nachher")
        for column in ("#0", "before", "value"):
            self.fields.column(column, width=120, minwidth=50)
        self.fields.tag_configure("changed", font="TkHeadingFont")
        self.field_detail = tk.StringVar()
        ttk.Label(self.properties_frame, textvariable=self.field_detail).pack(fill="x")
        self.fields.bind("<<TreeviewSelect>>", self.describe_field)
        self.history_visible = tk.BooleanVar(value=False)
        self.history_toggle = ttk.Checkbutton(
            self.more_frame,
            text="Verlauf",
            variable=self.history_visible,
            command=self.toggle_history,
        )
        self.history_toggle.pack(anchor="w", pady=3)
        self.history_frame = ttk.Frame(self.more_frame)
        self.repeat_button = ttk.Button(
            self.history_frame,
            text="Letzten Aufruf wiederholen",
            command=self.repeat_last,
        )
        self.repeat_button.pack(anchor="w", pady=3)
        self.log = self.text_output(self.history_frame)
        self.details_visible = tk.BooleanVar(value=False)
        self.details_toggle = ttk.Checkbutton(
            self.more_frame,
            text="Fehlerdetails",
            variable=self.details_visible,
            command=self.toggle_details,
        )
        self.details_frame = ttk.Frame(self.more_frame)
        self.details = self.text_output(self.details_frame)
        ttk.Label(self.more_frame, textvariable=self.status).pack(fill="x", pady=3)
        self.create_frame = ttk.LabelFrame(left, text="Neue Figur")
        _, create_content = self.scroll_area(self.create_frame)
        self.class_name = tk.StringVar()
        ttk.Label(create_content, text="Klasse").pack(anchor="w")
        self.class_box = ttk.Combobox(
            create_content, textvariable=self.class_name, state="readonly", width=15
        )
        self.class_box.pack(fill="x")
        self.class_box.bind(
            "<<ComboboxSelected>>", lambda e: self.constructor_changed()
        )
        self.name = tk.StringVar(
            value="figur2" if owner.mode_key == "E2" else "instanz2"
        )
        ttk.Label(create_content, text="Name").pack(anchor="w")
        ttk.Entry(create_content, textvariable=self.name, width=15).pack(fill="x")
        self.constructor_args = tk.StringVar()
        self.constructor_form = ParameterForm(
            create_content, self.constructor_args, self.update_preview
        )
        self.constructor_form.submit = self.create
        self.constructor_form.pack(fill="x")
        self.create_button = ttk.Button(
            create_content, text="Erzeugen", command=self.create
        )
        self.create_button.pack(fill="x", pady=4)
        self.methods = {}
        self.method_info = {}
        self.classes = {}
        self.class_info = {}
        self.ui_mode = None
        self.apply_mode()

        def wrap_labels(parent):
            for child in parent.winfo_children():
                fills_width = (
                    child.winfo_manager() == "pack"
                    and child.pack_info().get("fill") in {"x", "both"}
                ) or (
                    child.winfo_manager() == "grid"
                    and "ew" in str(child.grid_info().get("sticky", ""))
                )
                if (
                    isinstance(child, ttk.Label)
                    and fills_width
                    and not child.bind("<Configure>")
                ):
                    child.configure(wraplength=150)
                    child.bind(
                        "<Configure>",
                        lambda event, label=child: label.configure(
                            wraplength=max(80, event.width - 8)
                        ),
                    )
                wrap_labels(child)

        wrap_labels(self)
        self.draw_classes()
        self.poll_job = self.after(100, self.poll)
        self.controls()

    def apply_mode(self):
        if self.ui_mode == self.owner.mode_key:
            return
        self.ui_mode = self.owner.mode_key
        elementary = self.ui_mode == "E2"
        self.mode_label.configure(text="Objekte · E2" if elementary else "Klassen · Q1")
        self.bank_heading.configure(text="Figuren" if elementary else "Instanzen")
        self.create_toggle.configure(
            text="+ Neue Figur" if elementary else "+ Neue Instanz"
        )
        self.create_frame.configure(text="Neue Figur" if elementary else "Konstruktor")
        if elementary:
            self.classes_toggle.pack_forget()
            self.diagram.pack_forget()
            if str(self.classes_host) in [str(pane) for pane in self.workspace.panes()]:
                self.workspace.forget(self.classes_host)
        else:
            self.classes_toggle.pack(side="right", padx=8)
            self.toggle_classes()
        self._viewed_handle = None
        if self.data:
            self.select_object()

    def toggle_classes(self):
        present = str(self.classes_host) in [
            str(pane) for pane in self.workspace.panes()
        ]
        if self.owner.mode_key == "Q1" and self.classes_visible.get():
            if not present:
                self.workspace.add(self.classes_host, weight=1)
            self.diagram.pack(fill="both", expand=True, before=self.diagram_scroll)
        elif present:
            self.workspace.forget(self.classes_host)

    def layout_toolbar(self, event=None):
        required = (
            self.toolbar_actions.winfo_reqwidth()
            + self.state_label.winfo_reqwidth()
            + self.hide_button.winfo_reqwidth()
            + 30
        )
        compact = self.toolbar.winfo_width() < required
        if compact == getattr(self, "_toolbar_compact", None):
            return
        self._toolbar_compact = compact
        self.toolbar_actions.grid(
            row=0, column=0, columnspan=2 if compact else 1, sticky="w"
        )
        self.state_label.grid(
            row=1 if compact else 0,
            column=0 if compact else 1,
            sticky="w",
            padx=6,
            pady=3,
        )
        self.hide_button.grid(
            row=1 if compact else 0, column=1 if compact else 2, sticky="e"
        )

    def layout_actions(self, event=None):
        separate = self.shortcuts.winfo_width() < 520
        if separate != getattr(self, "_shortcuts_compact", None):
            self._shortcuts_compact = separate
            self.quick_actions.grid(
                row=0, column=0, columnspan=2 if separate else 1, sticky="ew"
            )
            self.methods_toggle.grid(row=1 if separate else 0, column=1, sticky="e")
        width = self.quick_actions.winfo_width()
        cell = max(
            (button.winfo_reqwidth() + 6 for button in self.quick_buttons), default=100
        )
        columns = max(1, min(3, width // cell))
        for index, button in enumerate(self.quick_buttons):
            button.grid(
                row=index // columns,
                column=index % columns,
                sticky="w",
                padx=(0, 4),
                pady=2,
            )

    def layout_call(self, event=None):
        compact = self.call_bar.winfo_width() < 420
        if compact == getattr(self, "_call_compact", None):
            return
        self._call_compact = compact
        self.preview_label.grid(
            row=0, column=0, columnspan=2 if compact else 1, sticky="ew", padx=(0, 8)
        )
        self.invoke_button.grid(
            row=1 if compact else 0,
            column=0 if compact else 1,
            sticky="w" if compact else "e",
            pady=3,
        )

    def toggle_methods(self):
        self.methods_toggle.configure(
            text="▾ Weitere Methoden"
            if self.methods_visible.get()
            else "▸ Weitere Methoden"
        )
        if self.methods_visible.get():
            self.method_filters.pack(fill="x", before=self.method_row)
            self.search_entry.focus_set()
        else:
            self.method_filters.pack_forget()
            self.method_search.set("")
            self.method_group.set("Alle Methoden")

    def toggle_more(self):
        self.more_toggle.configure(
            text="▾ Mehr" if self.more_visible.get() else "▸ Mehr"
        )
        if self.more_visible.get():
            self.more_frame.pack(fill="x")
        else:
            self.more_frame.pack_forget()

    def scroll_area(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0, width=180, height=180)
        scroll = ttk.Scrollbar(parent, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        content = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfigure(window, width=e.width)
        )

        # Bind only this area's descendants, so editor scrolling is unaffected.
        def scroll_event(event):
            delta = (
                -1
                if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0
                else 1
            )
            canvas.yview_scroll(delta, "units")
            return "break"

        def bind_children():
            def visit(widget):
                for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                    widget.bind(sequence, scroll_event)
                for child in widget.winfo_children():
                    visit(child)

            visit(content)

        content.bind("<Map>", lambda e: bind_children(), add=True)
        content.bind("<Configure>", lambda e: bind_children(), add=True)
        return canvas, content

    def toggle_properties(self):
        if self.properties_visible.get():
            self.properties_frame.pack(fill="x", before=self.history_toggle)
        else:
            self.properties_frame.pack_forget()

    def toggle_history(self):
        if self.history_visible.get():
            self.history_frame.pack(fill="both", expand=True)
        else:
            self.history_frame.pack_forget()

    def toggle_details(self):
        if self.details_visible.get():
            self.details_frame.pack(fill="x")
        else:
            self.details_frame.pack_forget()

    def last_method_call(self):
        for item in reversed((self.data or {}).get("history", [])):
            if item.get("result") == "Objektreferenz":
                continue
            try:
                node = ast.parse(item["code"]).body[0]
                call = node.value if isinstance(node, (ast.Expr, ast.Assign)) else None
            except (SyntaxError, IndexError):
                return None
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
            ):
                return call
            return None
        return None

    def repeat_last(self):
        if (
            not self.data
            or not self.data.get("history")
            or self.busy
            or self.stale
            or not self.data.get("paused", True)
        ):
            return
        # Reuse the regular, validated method form. Constructors are not repeated.
        call = self.last_method_call()
        if call is None:
            return
        row = next(
            (r for r in self.data["objects"] if call.func.value.id in r["aliases"]),
            None,
        )
        if not row:
            return
        self._updating_snapshot = True
        self.bank.selection_set(row["handle"])
        self.select_object()
        self._updating_snapshot = False
        label = next((k for k, v in self.methods.items() if v == call.func.attr), None)
        if label:
            self.choose_method(label)
            self.args.set(ast.unparse(call)[ast.unparse(call).index("(") + 1 : -1])
            self.invoke()

    METHOD_HINTS: ClassVar[dict] = {
        "move": ("Bewegen", "bewegen"),
        "move_forward": ("Bewegen", "vorwärts bewegen"),
        "move_back": ("Bewegen", "rückwärts bewegen"),
        "move_to": ("Bewegen", "zu einer Position bewegen"),
        "move_towards": ("Bewegen", "zu einem Ziel bewegen"),
        "move_in_direction": ("Bewegen", "in eine Richtung bewegen"),
        "move_vector": ("Bewegen", "um einen Vektor bewegen"),
        "move_away": ("Bewegen", "von einem Ziel wegbewegen"),
        "turn": ("Bewegen", "drehen"),
        "turn_left": ("Bewegen", "nach links drehen"),
        "turn_right": ("Bewegen", "nach rechts drehen"),
        "set_direction": ("Bewegen", "Richtung ändern"),
        "set_position": ("Bewegen", "Position setzen"),
        "add_costume": ("Aussehen", "Kostüm hinzufügen"),
        "set_costume": ("Aussehen", "Kostüm wechseln"),
        "set_size": ("Aussehen", "Größe ändern"),
        "set_background_color": ("Aussehen", "Hintergrundfarbe ändern"),
    }

    def filter_methods(self):
        if not hasattr(self, "method_info"):
            return
        query = self.method_search.get().strip().casefold()
        group = self.method_group.get()
        labels = []
        for label, info in self.method_info.items():
            category, hint = self.METHOD_HINTS.get(info["name"], ("Weitere", ""))
            matches = (
                group == "Alle Methoden"
                or group == category
                or (group == "Eigene Methoden" and not info["inherited"])
            )
            if matches and query in (label + " " + hint).casefold():
                labels.append(label)
        self.method_box.configure(values=labels)
        if self.method.get() not in labels:
            self.method.set(next(iter(labels), ""))
            self.method_changed()
        self.controls()

    def choose_method(self, label):
        self.method_search.set("")
        self.method_group.set("Alle Methoden")
        self.method.set(label)
        self.method_changed()
        self.action_canvas.yview_moveto(0)

    def tree(self, parent, columns, height):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, height=height, selectmode="browse")
        y = ttk.Scrollbar(frame, command=tree.yview)
        x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        y.pack(side="right", fill="y")
        x.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        return tree

    def text_output(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, height=4, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        return text

    def toggle_create(self):
        if self.create_visible.get():
            self.create_frame.pack(fill="both", expand=True, pady=4)
        else:
            self.create_frame.pack_forget()

    def stop_program(self):
        self.stop()

    def references(self):
        return {
            alias: None
            for row in (self.data or {}).get("objects", [])
            for alias in row["aliases"]
        }

    def method_changed(self):
        if getattr(self, "_switching_object", False):
            return
        row = self.selected()
        info = self.method_info.get(self.method.get())
        if row and info:
            self.chosen_methods[row["handle"]] = info["name"]
            self.method_help.set(self.METHOD_HINTS.get(info["name"], ("", ""))[1])
            self.method_form.pack(fill="x", pady=4, before=self.call_bar)
            self.method_form.configure_parameters(
                (row["handle"], info["name"]), info.get("parameters"), self.references()
            )
        else:
            self.method_form.pack_forget()
            self.method_help.set("Keine passende Methode." if self.methods else "")
        self.update_preview()
        self.controls()

    def constructor_changed(self):
        info = self.class_info.get(self.class_name.get())
        if info:
            self.constructor_form.configure_parameters(
                info["name"], info.get("parameters"), self.references()
            )

    def update_preview(self):
        if not hasattr(self, "preview"):
            return
        row = self.selected()
        method = (
            self.methods.get(self.method.get()) if hasattr(self, "methods") else None
        )
        if row and method:
            try:
                code = self.method_form.code()
                self.preview.set(f"{row['aliases'][0]}.{method}({code})")
            except (ValueError, SyntaxError):
                self.preview.set("Bitte die markierten Parameter ergänzen.")
        else:
            self.preview.set("Wähle zuerst ein Objekt und eine Methode.")
        if hasattr(self, "methods"):
            self.controls()

    def begin_action(self, command):
        self.pending_action = command.get("action")
        selected = self.selected()
        self.pending_receiver = command.get("handle") or (
            selected["handle"] if selected and self.pending_action == "invoke" else None
        )
        self.pending_name = command.get("name")
        if self.pending_action in {"invoke", "create", "resume"}:
            self.comparison_before = {
                row["handle"]: row["fields"].copy()
                for row in (self.data or {}).get("objects", [])
            }
            self.comparison_after = {}

    def display_fields(self, row):
        previous = self.comparison_before.get(row["handle"], row["fields"])
        after = self.comparison_after.get(row["handle"], row["fields"])
        self.fields.delete(*self.fields.get_children())
        changed_id = None
        self.field_detail.set("")
        for name, value in after.items():
            old = previous.get(name, "—")
            changed = old != value
            item_id = self.fields.insert(
                "",
                "end",
                text=("● " if changed else "") + name,
                values=(old, value),
                tags=("changed",) if changed else (),
            )
            if changed and changed_id is None:
                changed_id = item_id
        if changed_id:
            self.fields.selection_set(changed_id)
            self.describe_field()

    def summarize_changes(self, row):
        previous = self.comparison_before.get(row["handle"], row["fields"])
        after = self.comparison_after.get(row["handle"], row["fields"])
        changes = [
            f"{name}: {previous.get(name, '—')} → {value}"
            for name, value in after.items()
            if previous.get(name, "—") != value
        ]
        return "\n".join(changes[:5]) + (
            "\nWeitere Änderungen unter Alle Eigenschaften." if len(changes) > 5 else ""
        )

    def set_outcome(self, response):
        if self.pending_action in {"invoke", "create"}:
            row = next(
                (
                    r
                    for r in (self.data or {}).get("objects", [])
                    if r["handle"] == self.pending_receiver
                    or self.pending_name in r["aliases"]
                ),
                None,
            )
            self.result_panel.configure(
                text="Letzter Aufruf" + (" · " + row["aliases"][0] if row else "")
            )
            self.result_summary.set(self.summarize_changes(row) if row else "")
        if response.get("ok"):
            if (
                self.pending_action in {"invoke", "create", "resume"}
                or not self.last_error
            ):
                self.feedback.set("")
                self.last_error = None
                self.details_toggle.pack_forget()
                self.details_frame.pack_forget()
                self.details_visible.set(False)
            if (
                self.pending_action in {"invoke", "create"}
                and self.data
                and self.data.get("history")
            ):
                item = next(
                    (
                        entry
                        for entry in reversed(self.data["history"])
                        if entry.get("result") != "Objektreferenz"
                    ),
                    self.data["history"][-1],
                )
                self.last_call.set(f"✓ {item['code']} → {item['result']}")
                self.reveal_result()
        else:
            error = response.get("error", "Unbekannter Fehler")
            self.last_error = error
            if error.startswith("TypeError"):
                explanation = "Der Aufruf passt nicht zu den Parametern. Prüfe die Felder und versuche es erneut."
            elif error.startswith("ValueError"):
                explanation = "Ein Wert passt nicht zur Methode. Prüfe die Eingaben. Änderungen vor dem Fehler können erhalten bleiben."
            else:
                explanation = "Die Methode konnte nicht vollständig ausgeführt werden. Prüfe deinen Code an der angegebenen Stelle."
            self.feedback.set(explanation + "\n" + error)
            self.last_call.set("")
            self.details_toggle.pack(anchor="w")
            self.details.configure(state="normal")
            self.details.delete("1.0", "end")
            self.details.insert("end", response.get("traceback", error))
            self.details.configure(state="disabled")
            self.reveal_result()
        self.pending_action = None

    def reveal_result(self):
        """Scroll only as far as needed to keep the immediate result in sight."""
        self.update_idletasks()
        bounds = self.action_canvas.bbox("all")
        if not bounds or bounds[3] <= 0:
            return
        bottom = self.result_panel.winfo_y() + self.result_panel.winfo_height()
        visible_top = self.action_canvas.canvasy(0)
        height = self.action_canvas.winfo_height()
        if bottom > visible_top + height:
            self.action_canvas.yview_moveto(max(0, bottom - height + 8) / bounds[3])

    def back(self):
        if hasattr(self.owner, "show_main"):
            self.owner.show_main()

    def describe_field(self, event=None):
        selection = self.fields.selection()
        if selection:
            item = self.fields.item(selection[0])
            before, after = item["values"]
            self.field_detail.set(f"{item['text']}\nVorher: {before}\nNachher: {after}")

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
        style = ttk.Style(self)
        background = style.lookup("TFrame", "background") or "#ededed"
        surface = style.lookup("TEntry", "fieldbackground") or "white"
        foreground = style.lookup("TLabel", "foreground") or "#222222"
        self.diagram.configure(background=background)
        try:
            _, _, source = self.source()
            rows = classes_in(source)
        except (ValueError, SyntaxError):
            rows = []
        self.class_lines = {r["name"]: r["line"] for r in rows}
        names = list(
            dict.fromkeys(
                [b for r in rows for b in r["bases"]] + [r["name"] for r in rows]
            )
        )
        # Include constructible imports as cards even in a file without subclasses.
        names.extend(name for name in self.classes if name not in names)
        positions = {name: (10, 10 + i * 90) for i, name in enumerate(names)}
        for row in rows:
            x, y = positions[row["name"]]
            for base in row["bases"]:
                bx, by = positions[base]
                self.diagram.create_line(
                    x + 160,
                    y + 25,
                    x + 178,
                    y + 25,
                    bx + 178,
                    by + 25,
                    bx + 160,
                    by + 25,
                    arrow="last",
                    fill=foreground,
                )
        for name, (x, y) in positions.items():
            tag = "class_" + name
            self.diagram.create_rectangle(
                x, y, x + 160, y + 66, fill=surface, outline=foreground, tags=tag
            )
            row = next(
                (r for r in (self.data or {}).get("objects", []) if r["type"] == name),
                None,
            )
            image = self.bank.preview(row) if row else None
            if image:
                self.diagram.create_image(x + 28, y + 33, image=image, tags=tag)
            else:
                self.diagram.create_text(
                    x + 28,
                    y + 32,
                    text=name[:1],
                    font="TkHeadingFont",
                    fill=foreground,
                    tags=tag,
                )
            self.diagram.create_text(
                x + 57,
                y + 16,
                anchor="nw",
                text=self.bank.short_text(name, 96, "TkHeadingFont"),
                font="TkHeadingFont",
                fill=foreground,
                tags=tag,
            )
            self.diagram.create_text(
                x + 57, y + 42, anchor="nw", text="Klasse", fill=foreground, tags=tag
            )
            self.diagram.tag_bind(
                tag, "<Button-1>", lambda e, n=name: self.choose_class(n)
            )
            self.diagram.tag_bind(
                tag, "<Double-Button-1>", lambda e, n=name: self.goto_class(n)
            )
        if not names:
            self.diagram.create_text(
                12,
                16,
                anchor="nw",
                width=165,
                text="Deine Klassen erscheinen hier. Lade dein Programm oder definiere eine Klasse.",
                fill=foreground,
            )
        self.diagram.configure(scrollregion=self.diagram.bbox("all"))
        self.diagram.bind(
            "<MouseWheel>",
            lambda e: self.diagram.yview_scroll(-1 if e.delta > 0 else 1, "units"),
        )
        self.diagram.bind(
            "<Button-4>", lambda e: self.diagram.yview_scroll(-1, "units")
        )
        self.diagram.bind("<Button-5>", lambda e: self.diagram.yview_scroll(1, "units"))

    def choose_class(self, name):
        if name not in self.classes:
            return
        self.class_name.set(name)
        self.constructor_changed()
        self.create_visible.set(True)
        self.toggle_create()

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

    def action_ready(self, ready):
        return (
            ready
            and bool(self.bank.selection())
            and self.method.get() in self.methods
            and self.method_form.valid()
        )

    def common_controls(self, ready):
        if self.stale:
            self.state_title.set("Code geändert")
        elif self.busy:
            self.state_title.set("Aufruf läuft …" if self.data else "Lädt …")
        elif self.last_error:
            self.state_title.set("Fehler beim Aufruf")
        elif self.data:
            self.state_title.set(
                "Pausiert" if self.data.get("paused", True) else "Läuft"
            )
        else:
            self.state_title.set(
                "Bereit zum Laden" if not self.loaded_revision else "Gestoppt"
            )
        if self.stale or not self.data:
            self.notice_label.pack(fill="x", before=self.workspace)
        else:
            self.notice_label.pack_forget()
        hint = ""
        if self.data:
            if self.stale:
                hint = "Code geändert. Setze die Welt zurück, um den neuen Stand zu verwenden."
            elif self.busy:
                hint = "Aufruf läuft. Bitte kurz warten."
            elif not self.data.get("paused", True):
                hint = "Pausiere die Welt, um Methoden auszuprobieren."
            elif not self.bank.selection():
                hint = "Wähle links eine Figur aus."
            elif self.method.get() not in self.methods:
                hint = "Keine passende Methode. Leere die Suche oder wähle eine andere Gruppe."
            elif not self.method_form.valid():
                hint = "Korrigiere die markierten Eingaben."
        self.action_hint.set(hint)
        if hint:
            self.action_hint_label.pack(fill="x", before=self.call_bar, pady=3)
        else:
            self.action_hint_label.pack_forget()
        self.layout_toolbar()
        self.load_button.configure(
            text="↻ Zurücksetzen" if self.loaded_revision else "↻ Laden",
            state="disabled" if self.busy else "normal",
        )
        active = bool(
            getattr(self, "connection", None)
            or self.process
            or getattr(self, "reload_job", None)
        )
        self.stop_button.configure(state="normal" if active else "disabled")
        exportable = bool(
            ready
            and self.data
            and self.data.get("history")
            and self.data.get("replay_complete", True)
        )
        self.export_button.configure(state="normal" if exportable else "disabled")
        if self.data and self.data.get("history"):
            self.export_button.pack(side="left", pady=3)
        else:
            self.export_button.pack_forget()
        repeatable = exportable and self.last_method_call() is not None
        self.repeat_button.configure(state="normal" if repeatable else "disabled")

    def send(self, command):
        if self.busy or not self.process or self.process.poll() is not None:
            return
        try:
            self.begin_action(command)
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
        changed_object = self._viewed_handle != row["handle"]
        self._viewed_handle = row["handle"]
        self._switching_object = True
        self.receiver.set(" = ".join(row["aliases"]) + " · " + row["type"])
        self.display_fields(row)
        self.method_info = {
            (
                (
                    m["name"]
                    + m.get("signature", "")
                    + f" · {m['owner']}"
                    + (" (geerbt)" if m["inherited"] else "")
                )
                if self.owner.mode_key == "Q1"
                else m["name"]
                + (
                    " · " + self.METHOD_HINTS[m["name"]][1]
                    if m["name"] in self.METHOD_HINTS
                    else ""
                )
            ): m
            for m in row["methods"]
        }
        self.methods = {label: info["name"] for label, info in self.method_info.items()}
        if changed_object:
            self.method_search.set("")
            self.method_group.set("Alle Methoden")
            preferred = next(
                (
                    label
                    for label, name in self.methods.items()
                    if name == self.chosen_methods.get(row["handle"])
                ),
                "",
            ) or next(
                (
                    label
                    for label, info in self.method_info.items()
                    if (self.owner.mode_key == "E2" and info["name"] == "move")
                    or (self.owner.mode_key == "Q1" and not info["inherited"])
                ),
                "",
            )
            self.method.set(preferred)
        self.filter_methods()
        self._switching_object = False
        if changed_object:
            self.action_canvas.yview_moveto(0)
        quick = [
            (name, next((k for k, v in self.methods.items() if v == name), None))
            for name in ("move", "turn_left", "turn_right")
        ]
        if quick != getattr(self, "_quick_key", None):
            self._quick_key = quick
            for child in self.quick_actions.winfo_children():
                child.destroy()
            self.quick_buttons = []
            for name, label in quick:
                if not label:
                    continue
                self.quick_buttons.append(
                    ttk.Button(
                        self.quick_actions,
                        text=name + "(…)",
                        command=lambda key=label: self.choose_method(key),
                    )
                )
            self.layout_actions()
        self.method_changed()
        self.controls()
        if (
            not getattr(self, "_updating_snapshot", False)
            and not self.busy
            and self.highlighted != row["handle"]
        ):
            self.highlighted = row["handle"]
            self.send({"action": "select", "handle": row["handle"]})

    def use_reference(self):
        # References are chosen per parameter, independently of the receiver.
        self.feedback.set(
            "Wähle beim gewünschten Parameter „Objekt“ und dann den Namen aus der Objektbank."
        )

    def invoke(self):
        row = self.selected()
        if (
            row
            and self.data.get("paused", True)
            and not self.stale
            and not self.busy
            and self.method.get() in self.methods
        ):
            try:
                code = self.method_form.code()
                self.send(
                    {
                        "action": "invoke",
                        "handle": row["handle"],
                        "method": self.methods[self.method.get()],
                        "arguments": code,
                        "prediction": self.prediction.get(),
                    }
                )
            except (ValueError, SyntaxError) as error:
                self.action_hint.set(str(error))
                self.method_form.focus_problem()
                self.action_canvas.yview_moveto(0)

    def create(self):
        if (
            self.data
            and self.data.get("paused", True)
            and not self.stale
            and not self.busy
            and self.class_name.get() in self.classes
        ):
            try:
                code = self.constructor_form.code()
                self.send(
                    dict(
                        action="create",
                        name=self.name.get(),
                        **{"class": self.classes[self.class_name.get()]},
                        arguments=code,
                        prediction=self.prediction.get(),
                    )
                )
            except (ValueError, SyntaxError) as error:
                self.feedback.set(str(error))

    def show_data(self, data):
        self._updating_snapshot = True
        selection = self.bank.selection()
        self.data = data
        if self.pending_action in {"invoke", "create", "resume"}:
            self.comparison_after = {
                row["handle"]: row["fields"].copy() for row in data["objects"]
            }
        self.bank.set_objects(data["objects"])
        self.class_info = {c["name"]: c for c in data["classes"]}
        self.classes = {c["name"]: c["name"] for c in data["classes"]}
        self.class_box.configure(values=list(self.classes))
        if self.class_name.get() not in self.classes:
            preferred = (
                next(
                    (
                        label
                        for label, name in self.classes.items()
                        if name in self.class_lines
                    ),
                    None,
                )
                if self.owner.mode_key == "Q1"
                else None
            )
            self.class_name.set(
                preferred
                or next(
                    (label for label, name in self.classes.items() if name == "Actor"),
                    next(iter(self.classes), ""),
                )
            )
        self.constructor_changed()
        self.draw_classes()
        if selection and self.bank.exists(selection[0]):
            self.bank.selection_set(selection[0])
            self.select_object()
        elif data["objects"]:
            preferred = next(
                (
                    r
                    for r in data["objects"]
                    if r["type"] not in {"World", "TiledWorld"}
                ),
                data["objects"][0],
            )
            self.bank.selection_set(preferred["handle"])
            self.select_object()
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        for item in data["history"]:
            self.log.insert(
                "end",
                f"Vorhersage: {item['prediction'] or '—'}\n{item['code']} → {item['result']}\n",
            )
        self.log.configure(state="disabled")
        self._updating_snapshot = False

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
                    self.set_outcome(response)
                    self.select_object()
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
                    self.bank.clear()
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
        self.poll_job = self.after(350, self.poll)

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
        self.last_error = None
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
        self.busy = False
        self.status.set("Experiment beendet. Die Objektbank wurde geleert.")
        self.controls()

    def close(self):
        if hasattr(self, "poll_job"):
            self.after_cancel(self.poll_job)
        self.stop()
        self.destroy()
