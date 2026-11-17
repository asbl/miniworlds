"""A labelled value/reference form with an explicit Python-entry fallback."""

import tkinter as tk
from tkinter import ttk

from .lab_model import arguments, form_arguments


class ParameterForm(ttk.Frame):
    def __init__(self, master, code_variable, changed, compact=False):
        super().__init__(master)
        self.code_variable = code_variable
        self.changed = changed
        self.compact = compact
        self.parameters = []
        self.references = {}
        self.rows = {}
        self.selectors = {}
        self.key = None
        self.updating = False
        self.generated = ""
        self.problem = ""
        self.invalid_fields = {}
        self.error_labels = {}
        style = ttk.Style(self)
        background = style.lookup("TFrame", "background") or "white"
        red, green, blue = self.winfo_rgb(background)
        error_color = "#ffb4a8" if red + green + blue < 3 * 32768 else "#a52620"
        style.configure("Lab.Error.TLabel", foreground=error_color)
        style.map("LabInvalid.TCombobox", bordercolor=[("!disabled", error_color)])
        self.saved = {}
        self.submit = None
        self.optional = tk.BooleanVar(value=False)
        self.optional_rows = []
        self.fields = ttk.Frame(self)
        self.fields.pack(fill="x")
        self.options_bar = ttk.Frame(self)
        self.options_bar.pack(fill="x")
        self.optional_toggle = ttk.Checkbutton(
            self.options_bar,
            text="Weitere Parameter",
            variable=self.optional,
            command=self.show_optional,
        )
        self.advanced = tk.BooleanVar(value=False)
        self.advanced_toggle = ttk.Checkbutton(
            self.options_bar,
            text="Python-Eingabe",
            variable=self.advanced,
            command=self.toggle,
        )
        if not self.compact:
            self.advanced_toggle.pack(anchor="w")
        self.raw = ttk.Entry(self, textvariable=code_variable)
        self.note = ttk.Label(self, text="", wraplength=440, justify="left")
        self.note.pack(fill="x")
        self.note.bind(
            "<Configure>",
            lambda e: self.note.configure(wraplength=max(80, e.width - 8)),
        )
        self.trace = code_variable.trace_add("write", self.raw_changed)
        self.bind("<Destroy>", self.cleanup, add=True)

    def choices(self, name):
        parameter = next((p for p in self.parameters or [] if p["name"] == name), {})
        if parameter.get("hint") == "boolean":
            return ["True", "False"]
        if parameter.get("hint") == "direction":
            return ["right", "left", "up", "down", "0", "90", "180", "270", "None"]
        return []

    def configure_parameters(self, key, parameters, references):
        self.references = references
        if key == self.key:
            for name, (_, mode, entry) in self.rows.items():
                entry.configure(
                    values=list(references)
                    if mode.get() == "Objekt"
                    else self.choices(name)
                )
            self.show_reference_selectors()
            self.update_code()
            return
        if self.key is not None:
            self.saved[self.key] = (
                {
                    name: (value.get(), mode.get())
                    for name, (value, mode, _) in self.rows.items()
                },
                self.advanced.get(),
                self.code_variable.get(),
            )
        saved_values, saved_advanced, saved_code = self.saved.get(
            key, ({}, parameters is None, "")
        )
        self.key = key
        self.parameters = parameters
        self.updating = True
        for child in self.fields.winfo_children():
            child.destroy()
        self.rows = {}
        self.selectors = {}
        self.error_labels = {}
        self.optional_rows = []
        self.optional.set(False)
        for index, parameter in enumerate(parameters or []):
            name = parameter["name"]
            frame = ttk.Frame(self.fields, padding=(0, 3))
            if parameter["required"] or index == 0:
                frame.pack(fill="x")
            else:
                self.optional_rows.append(frame)
            optional = "" if parameter["required"] else " · optional"
            label = {
                "distance": "Entfernung",
                "degrees": "Winkel",
                "direction": "Richtung",
                "position": "Position",
                "color": "Farbe",
            }.get(name)
            ttk.Label(
                frame, text=(f"{label} · {name}" if label else name) + optional
            ).pack(anchor="w")
            saved_value, saved_mode = saved_values.get(
                name, (parameter["default"] or "", "Wert")
            )
            value = tk.StringVar(value=saved_value)
            mode = tk.StringVar(value=saved_mode)
            inputs = ttk.Frame(frame)
            inputs.pack(fill="x")
            selector = ttk.Combobox(
                inputs,
                state="readonly",
                width=6,
                textvariable=mode,
                values=["Wert", "Objekt"],
            )
            selector.pack(side="left", padx=(0, 5))
            entry = ttk.Combobox(inputs, textvariable=value, width=22)
            entry.pack(side="left", fill="x", expand=True)
            entry.bind("<Return>", self.enter)
            self.rows[name] = (value, mode, entry)
            self.selectors[name] = selector
            error_label = ttk.Label(frame, style="Lab.Error.TLabel", wraplength=300)
            error_label.bind(
                "<Configure>",
                lambda e, label=error_label: label.configure(
                    wraplength=max(80, e.width)
                ),
            )
            self.error_labels[name] = error_label
            value.trace_add("write", self.update_code)
            mode.trace_add("write", self.update_code)
        self.advanced.set(saved_advanced)
        self.code_variable.set(saved_code)
        self.updating = False
        self.toggle()
        self.show_reference_selectors()

    def show_reference_selectors(self):
        for parameter in self.parameters or []:
            name = parameter["name"]
            _, mode, entry = self.rows[name]
            selector = self.selectors[name]
            if (
                parameter.get("hint") == "literal" and self.references
            ) or mode.get() == "Objekt":
                selector.pack(side="left", padx=(0, 5), before=entry)
            else:
                selector.pack_forget()

    def enter(self, event=None):
        if self.submit:
            self.submit()
        return "break"

    def valid(self):
        try:
            self.code()
            return True
        except (ValueError, SyntaxError):
            return False

    def focus_problem(self):
        if self.advanced.get():
            self.raw.focus_set()
            return
        if self.invalid_fields:
            name = next(iter(self.invalid_fields))
            entry = self.rows[name][2]
            if entry.master.master in self.optional_rows:
                self.optional.set(True)
                self.show_optional()
            entry.focus_set()
            entry.selection_range(0, "end")

    def show_optional(self):
        for frame in self.optional_rows:
            if self.optional.get():
                frame.pack(fill="x")
            else:
                frame.pack_forget()

    def toggle(self):
        self.raw.pack_forget()
        self.fields.pack_forget()
        self.optional_toggle.pack_forget()
        if self.advanced.get():
            self.raw.pack(fill="x", before=self.options_bar)
            self.raw.bind("<Return>", self.enter)
            self.problem = ""
            self.note.configure(
                text="Python-Literale und Namen aus der Objektbank; keine Funktionsaufrufe."
            )
            self.note.pack(fill="x")
        else:
            self.fields.pack(fill="x", before=self.options_bar)
            if self.optional_rows:
                self.optional_toggle.pack(anchor="w")
            self.update_code()
        self.changed()

    def update_code(self, *unused):
        if self.updating or self.advanced.get():
            return
        self.updating = True
        try:
            values = {}
            for name, (value, mode, entry) in self.rows.items():
                kind = "object" if mode.get() == "Objekt" else "value"
                entry.configure(
                    values=list(self.references)
                    if kind == "object"
                    else self.choices(name)
                )
                values[name] = (value.get(), kind)
            self.invalid_fields = {}
            for parameter in self.parameters or []:
                name = parameter["name"]
                try:
                    form_arguments([parameter], values, self.references)
                except ValueError as error:
                    self.invalid_fields[name] = str(error)
                label = self.error_labels[name]
                entry = self.rows[name][2]
                entry.configure(
                    style="LabInvalid.TCombobox"
                    if name in self.invalid_fields
                    else "TCombobox"
                )
                if name in self.invalid_fields:
                    label.configure(text="! " + self.invalid_fields[name])
                    label.pack(fill="x", pady=(2, 0))
                else:
                    label.pack_forget()
            self.generated = form_arguments(
                self.parameters or [], values, self.references
            )
            self.problem = ""
            self.note.configure(
                text="" if self.parameters else "Keine Parameter nötig."
            )
            if self.parameters:
                self.note.pack_forget()
            else:
                self.note.pack(fill="x")
        except ValueError as error:
            self.generated = ""
            self.problem = str(error)
            self.note.configure(text=self.problem)
            if self.invalid_fields:
                self.note.pack_forget()
            else:
                self.note.pack(fill="x")
        self.code_variable.set(self.generated)
        self.updating = False
        self.changed()

    def raw_changed(self, *unused):
        if self.updating:
            return
        if not self.advanced.get() and self.code_variable.get() != self.generated:
            self.advanced.set(True)
            self.toggle()
        self.changed()

    def code(self):
        if not self.advanced.get() and self.problem:
            raise ValueError(self.problem)
        code = self.code_variable.get()
        arguments(code, self.references)
        return code

    def cleanup(self, event):
        if event.widget is self:
            self.code_variable.trace_remove("write", self.trace)
