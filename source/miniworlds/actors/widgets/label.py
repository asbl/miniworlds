import miniworlds.actors.widgets.button as widget


class Label(widget.Button):
    def __init__(self, text, image=None):
        super().__init__(text, image)
        self.event = "label"
        self.data = text
        self.background_color = (255, 255, 255, 0)