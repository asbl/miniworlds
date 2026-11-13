"""A labelled value/reference form with an explicit Python-entry fallback."""
import tkinter as tk
from tkinter import ttk

from .lab_model import arguments, form_arguments


class ParameterForm(ttk.Frame):
    def __init__(self, master, code_variable, changed):
        super().__init__(master)
        self.code_variable = code_variable
        self.changed = changed
        self.parameters = []
        self.references = {}
        self.rows = {}
        self.key = None
        self.updating = False
        self.generated = ''
        self.problem = ''
        self.fields = ttk.Frame(self)
        self.fields.pack(fill='x')
        self.advanced = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text='Python-Eingabe verwenden', variable=self.advanced, command=self.toggle).pack(anchor='w')
        self.raw = ttk.Entry(self, textvariable=code_variable)
        self.note = ttk.Label(self, text='', wraplength=440, justify='left')
        self.note.pack(fill='x')
        self.trace = code_variable.trace_add('write', self.raw_changed)
        self.bind('<Destroy>', self.cleanup, add=True)

    def configure_parameters(self, key, parameters, references):
        self.references = references
        if key == self.key:
            for _, mode, entry in self.rows.values():
                entry.configure(values=list(references) if mode.get()=='object' else [])
            return
        self.key = key
        self.parameters = parameters
        self.updating = True
        for child in self.fields.winfo_children():
            child.destroy()
        self.rows = {}
        for parameter in parameters or []:
            name = parameter['name']
            frame = ttk.Frame(self.fields, padding=(0,3))
            frame.pack(fill='x')
            optional = '' if parameter['required'] else ' · optional'
            ttk.Label(frame, text=name+optional).pack(anchor='w')
            value = tk.StringVar(value=parameter['default'] or '')
            mode = tk.StringVar(value='value')
            selector = ttk.Combobox(frame, state='readonly', width=8, textvariable=mode, values=['Wert','Objekt'])
            # Internal values remain stable across translated display labels.
            selector.configure(values=['Wert','Objekt'])
            mode.set('Wert')
            selector.pack(side='left', padx=(0,5))
            entry = ttk.Combobox(frame, textvariable=value, width=22)
            entry.pack(side='left', fill='x', expand=True)
            self.rows[name] = (value, mode, entry)
            value.trace_add('write', self.update_code)
            mode.trace_add('write', self.update_code)
        self.advanced.set(parameters is None)
        self.code_variable.set('')
        self.updating = False
        self.toggle()

    def toggle(self):
        self.raw.pack_forget()
        self.fields.pack_forget()
        if self.advanced.get():
            self.raw.pack(fill='x', before=self.note)
            self.problem = ''
            self.note.configure(text='Python-Literale und Namen aus der Objektbank; keine Funktionsaufrufe.')
        else:
            self.fields.pack(fill='x', before=self.raw if self.raw.winfo_manager() else self.note)
            self.update_code()
        self.changed()

    def update_code(self, *unused):
        if self.updating or self.advanced.get():
            return
        self.updating = True
        try:
            values = {}
            for name,(value,mode,entry) in self.rows.items():
                kind = 'object' if mode.get()=='Objekt' else 'value'
                entry.configure(values=list(self.references) if kind=='object' else [])
                values[name]=(value.get(),kind)
            self.generated=form_arguments(self.parameters or [],values,self.references)
            self.problem=''
            self.note.configure(text='Optionale Felder dürfen leer bleiben. Texte ohne Anführungszeichen eingeben, wenn ein Text erwartet wird.')
        except ValueError as error:
            self.generated=''
            self.problem=str(error)
            self.note.configure(text=self.problem)
        self.code_variable.set(self.generated)
        self.updating=False
        self.changed()

    def raw_changed(self, *unused):
        if self.updating:
            return
        if not self.advanced.get() and self.code_variable.get()!=self.generated:
            self.advanced.set(True)
            self.toggle()
        self.changed()

    def code(self):
        if not self.advanced.get():
            if self.problem:
                raise ValueError(self.problem)
        code=self.code_variable.get()
        arguments(code,self.references)
        return code

    def cleanup(self,event):
        if event.widget is self:
            self.code_variable.trace_remove('write',self.trace)
