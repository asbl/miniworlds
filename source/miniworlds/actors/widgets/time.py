import miniworlds.actors.widgets.buttonwidget as widget


class TimeLabel(widget.ButtonWidget):
    def __init__(self, world, text, img_path=None):
        super().__init__()
        if img_path:
            self.set_image(img_path)
        self.world = world
        self.value = self.world.frame
        self.text = text
        self.set_text("{0} : {1}".format(self.text, str(self.value)))
        self.data = str(0)
        self.timed = True

    def update(self):
        self.value = self.world.frame
        self.set_text("{0} : {1}".format(self.text, str(self.value)))
