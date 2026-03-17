from __future__ import annotations

import tkinter as tk
from tkinter import filedialog
from typing import TYPE_CHECKING

import miniworlds.actors.widgets.button as widget

if TYPE_CHECKING:
    from miniworlds.worlds.world import World


class LoadButton(widget.Button):
    """Button widget that loads a world from a sqlite database file."""

    def __init__(
        self,
        world: "World",
        text: str,
        filename: str | None = None,
        img_path: str | None = None,
    ) -> None:
        super().__init__()
        if img_path:
            self.set_image(img_path)
        self.set_text(text)
        self.file = filename
        self.app = world.app

    def on_mouse_left_down(self, mouse_pos: tuple[int, int]) -> None:
        """Open a file dialog if needed and load the selected database file."""

        if self.file is None:
            # Keep the file dialog usable without showing a separate Tk root window.
            dialog_root = tk.Tk()
            dialog_root.withdraw()
            try:
                self.file = filedialog.askopenfilename(
                    initialdir="./",
                    title="Select file",
                    filetypes=(("db files", "*.db"), ("all files", "*.*")),
                )
            finally:
                dialog_root.destroy()
        current_world = self.app.get_running_world()
        if not self.file or current_world is None:
            return
        current_world.load_world_from_db(self.file)
