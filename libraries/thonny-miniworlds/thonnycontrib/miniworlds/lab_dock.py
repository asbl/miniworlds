"""Wide laboratory view in Thonny's bottom notebook."""

from tkinter import ttk

from thonny import get_workbench


class MiniworldsLabView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        from .live_view import ConnectedLabDialog

        owner = get_workbench().get_view("MiniworldsView")
        self.lab = ConnectedLabDialog(owner, parent=self)
        self.lab.pack(fill="both", expand=True)
        owner.lab_dialog = self.lab
        self.started = False
        self.sized = False

    def open(self):
        self.after_idle(self.ensure_initial_height)
        if not self.started:
            self.started = True
            if not getattr(self.lab, "loaded_revision", None) and not getattr(
                self.lab, "busy", False
            ):
                self.lab.start()

    def on_show(self):
        self.after_idle(self.ensure_initial_height)

    def ensure_initial_height(self):
        """Give the lab room once; subsequent sash adjustments belong to the user."""
        if self.sized or not hasattr(self, "home_widget"):
            return
        notebook = self.home_widget.master
        container = notebook.master
        panes = [str(pane) for pane in container.panes()]
        if str(notebook) not in panes or container.winfo_height() < 100:
            return
        index = panes.index(str(notebook))
        if index > 0:
            target = min(480, int(container.winfo_height() * 0.65))
            if notebook.winfo_height() < target:
                notebook.preferred_size_in_pw = target
                container.sash_place(index - 1, 0, container.winfo_height() - target)
        self.sized = True

    def destroy(self):
        if self.lab.winfo_exists():
            self.lab.close()
        super().destroy()
