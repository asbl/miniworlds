import miniworlds.actors.widgets.buttonwidget as widget


class LoadButton(widget.ButtonWidget):
    def __init__(
        self,
        world,
        text,
        filename,
        img_path=None,
    ):
        super().__init__()
        if img_path:
            self.set_image(img_path)
        self.set_text(text)
        self.file = filename
        self.app = world.app

    def on_mouse_left_down(self, mouse_pos):
        tk.Tk().withdraw()
        if self.file is None:
            self.file = filedialog.askopenfilename(
                initialdir="./",
                title="Select file",
                filetypes=(("db files", "*.db"), ("all files", "*.*")),
            )
        self.app.running_world.load_world_from_db(self.file)
