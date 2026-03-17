from __future__ import annotations

import logging
import tkinter as tk
from tkinter import filedialog
from typing import TYPE_CHECKING

import miniworlds.actors.widgets.button as widget

if TYPE_CHECKING:
    from miniworlds.worlds.world import World


logger = logging.getLogger(__name__)


class SaveButton(widget.Button):
    """Button widget that saves the active world to a sqlite database file."""

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
        self.event = "label"
        self.data = text
        self.world_reference = world
        self.app = world.app
        self.file = filename
        self.actors = None

    def on_mouse_left_down(self, mouse_pos: tuple[int, int]) -> None:
        """Open a save dialog if needed and store the active world in a database file."""

        current_world = self.app.get_running_world()
        if self.file is None:
            # Keep the file dialog usable without showing a separate Tk root window.
            dialog_root = tk.Tk()
            dialog_root.withdraw()
            try:
                self.file = filedialog.asksaveasfilename(
                    initialdir="./",
                    title="Select file",
                    filetypes=(("db files", "*.db"), ("all files", "*.*")),
                )
            finally:
                dialog_root.destroy()
        if not self.file or current_world is None:
            return
        current_world.save_to_db(self.file)
        current_world.send_message("Saved new world", self.file)
        logger.info("Saved active world to database file %s", self.file)