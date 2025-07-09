import miniworlds.actors.widgets.buttonwidget as widget
class SaveButton(widget.ButtonWidget):
    def __init__(
            self,
            world,
            text,
            filename: str = None,
            img_path: str = None,
    ):
        super().__init__()
        if img_path:
            self.set_image(img_path)
        self.set_text(text)
        self.event = "label"
        self.data = text
        self.app = world.app
        self.file = filename
        self.actors = None

    def on_mouse_left_down(self, mouse_pos):
        if self.file is None:
            tk.Tk().withdraw()
            self.file = filedialog.asksaveasfilename(
                initialdir="./", title="Select file", filetypes=(("db files", "*.db"), ("all files", "*.*"))
            )
            self.app.running_world.save_to_db(self.file)
            self.app.running_world.send_message("Saved new world", self.file)
        else:
            self.app.running_world.save_to_db(self.file)
            self.app.running_world.send_message("Saved new world", self.file)
            print("World was saved to file:", self.file)