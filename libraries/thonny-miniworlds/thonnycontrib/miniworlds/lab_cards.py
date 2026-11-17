"""Keyboard-accessible object cards; no game engine imports in the frontend."""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


class ObjectCards(ttk.Frame):
    CARD_HEIGHT = 76

    def __init__(self, master):
        super().__init__(master)
        self.rows = {}
        self.chosen = None
        self.images = {}
        self.query = tk.StringVar()
        self.filter_bar = ttk.Frame(self)
        self.filter_bar.pack(fill="x", pady=(0, 4))
        self.search_entry = ttk.Entry(
            self.filter_bar, textvariable=self.query, width=12
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(
            self.filter_bar, text="×", width=2, command=lambda: self.query.set("")
        ).pack(side="right")
        self.search_entry.bind("<Escape>", self.clear_filter)
        self.count = tk.StringVar()
        self.count_label = ttk.Label(self, textvariable=self.count)
        self.count_label.pack(fill="x")
        self.canvas = tk.Canvas(
            self, width=195, height=180, highlightthickness=1, takefocus=True
        )
        scroll = ttk.Scrollbar(self, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.redraw)
        self.canvas.bind("<<ThemeChanged>>", self.redraw)
        self.canvas.bind("<Button-1>", self.clicked)
        for sequence in ("<Up>", "<Down>", "<Home>", "<End>"):
            self.canvas.bind(sequence, self.navigate)
        self.canvas.bind(
            "<MouseWheel>", lambda e: self.scroll(-1 if e.delta > 0 else 1)
        )
        self.canvas.bind("<Button-4>", lambda e: self.scroll(-1))
        self.canvas.bind("<Button-5>", lambda e: self.scroll(1))
        self.query.trace_add("write", self.filter_changed)
        self.filter_bar.pack_forget()

    def visible_handles(self):
        query = self.query.get().strip().casefold()
        return tuple(
            handle
            for handle, row in self.rows.items()
            if query in (" ".join(row["aliases"]) + " " + row["type"]).casefold()
        )

    def clear_filter(self, event=None):
        self.query.set("")
        self.canvas.focus_set()
        self.reveal_selection()
        return "break"

    def filter_changed(self, *unused):
        self.canvas.yview_moveto(0)
        self.redraw()

    def scroll(self, delta):
        self.canvas.yview_scroll(delta, "units")
        return "break"

    def get_children(self):
        return tuple(self.rows)

    def exists(self, handle):
        return handle in self.rows

    def selection(self):
        return (self.chosen,) if self.chosen in self.rows else ()

    def selection_set(self, handle):
        if handle not in self.rows or self.chosen == handle:
            return
        self.chosen = handle
        self.redraw()
        self.reveal_selection()
        self.event_generate("<<ObjectSelected>>")

    def clear(self):
        self.query.set("")
        self.set_objects([])

    def set_objects(self, rows):
        updated = {row["handle"]: row for row in rows}
        if updated == self.rows:
            return
        self.rows = updated
        if self.chosen not in self.rows:
            self.chosen = None
        self.images = {
            key: value for key, value in self.images.items() if key in self.rows
        }
        self.redraw()

    def reveal_selection(self):
        handles = self.visible_handles()
        if self.chosen not in handles:
            return
        top = handles.index(self.chosen) * self.CARD_HEIGHT
        current = self.canvas.canvasy(0)
        if top < current:
            self.canvas.yview_moveto(top / (len(handles) * self.CARD_HEIGHT))
        elif top + self.CARD_HEIGHT > current + self.canvas.winfo_height():
            self.canvas.yview_moveto(
                max(0, top + self.CARD_HEIGHT - self.canvas.winfo_height())
                / (len(handles) * self.CARD_HEIGHT)
            )

    def preview(self, row):
        data = row.get("thumbnail")
        if not isinstance(data, str) or not data or len(data) > 20000:
            return None
        handle = row["handle"]
        cached = self.images.get(handle)
        if cached and cached[0] == data:
            return cached[1]
        try:
            image = tk.PhotoImage(master=self, data=data)
            if image.width() > 64 or image.height() > 64:
                return None
        except tk.TclError:
            return None
        self.images[handle] = (data, image)
        return image

    def redraw(self, event=None):
        canvas = self.canvas
        style = ttk.Style(self)
        background = style.lookup("TFrame", "background") or "#ededed"
        surface = style.lookup("TEntry", "fieldbackground") or "white"
        foreground = style.lookup("TLabel", "foreground") or "#222222"
        accent = style.lookup("Treeview", "background", ("selected",)) or "#397548"
        selected_text = style.lookup("Treeview", "foreground", ("selected",)) or "white"
        canvas.configure(background=background, highlightbackground=background)
        canvas.delete("all")
        width = max(120, canvas.winfo_width())
        handles = self.visible_handles()
        if len(self.rows) > 6 or self.query.get():
            self.filter_bar.pack(fill="x", pady=(0, 4), before=self.count_label)
        else:
            self.filter_bar.pack_forget()
        self.count.set(
            (
                f"{len(handles)} / {len(self.rows)}"
                if self.query.get()
                else f"{len(self.rows)} Objekte"
            )
            + (
                " · Auswahl ausgeblendet"
                if self.chosen and self.chosen not in handles
                else ""
            )
        )
        for index, handle in enumerate(handles):
            row = self.rows[handle]
            y = index * self.CARD_HEIGHT + 4
            selected = handle == self.chosen
            tag = f"card_{index}"
            canvas.create_rectangle(
                5,
                y,
                width - 6,
                y + 66,
                fill=accent if selected else surface,
                outline=foreground if selected else background,
                width=2 if selected else 1,
                tags=tag,
            )
            text_color = selected_text if selected else foreground
            image = self.preview(row)
            if image:
                canvas.create_image(34, y + 33, image=image, tags=tag)
            else:
                canvas.create_oval(
                    16, y + 15, 50, y + 49, outline=text_color, width=2, tags=tag
                )
                canvas.create_text(
                    33,
                    y + 32,
                    text=row["type"][:1],
                    fill=text_color,
                    font="TkHeadingFont",
                    tags=tag,
                )
            canvas.create_text(
                66,
                y + 10,
                anchor="nw",
                text=self.short_text(
                    ("✓ " if selected else "") + row["aliases"][0],
                    max(45, width - 80),
                    "TkHeadingFont",
                ),
                fill=text_color,
                font="TkHeadingFont",
                tags=tag,
            )
            canvas.create_text(
                66,
                y + 40,
                anchor="nw",
                text=self.short_text(row["type"], max(45, width - 80)),
                fill=text_color,
                tags=tag,
            )
        if not handles:
            canvas.create_text(
                12,
                16,
                anchor="nw",
                width=max(100, width - 24),
                text="Keine Treffer.\nSuche mit × leeren."
                if self.rows
                else "Noch keine Figuren.\nLade dein Programm, um loszulegen.",
                fill=foreground,
            )
        canvas.configure(
            scrollregion=(0, 0, width, max(1, len(handles) * self.CARD_HEIGHT))
        )

    def short_text(self, text, width, font="TkDefaultFont"):
        measure = tkfont.nametofont(font, root=self).measure
        if measure(text) <= width:
            return text
        shortened = text[:100]
        while shortened and measure(shortened + "…") > width:
            shortened = shortened[:-1]
        return shortened + "…"

    def clicked(self, event):
        self.canvas.focus_set()
        index = int(self.canvas.canvasy(event.y)) // self.CARD_HEIGHT
        handles = self.visible_handles()
        if 0 <= index < len(handles):
            self.selection_set(handles[index])

    def navigate(self, event):
        handles = self.visible_handles()
        if not handles:
            return "break"
        index = handles.index(self.chosen) if self.chosen in handles else 0
        index = {"Home": 0, "End": len(handles) - 1}.get(
            event.keysym, index + (1 if event.keysym == "Down" else -1)
        )
        index = max(0, min(len(handles) - 1, index))
        self.selection_set(handles[index])
        self.reveal_selection()
        return "break"
