import miniworlds.worlds.gui.toolbar as toolbar
import miniworlds.actors.widgets.label as label
import miniworlds.actors.widgets as widgets


class Console(toolbar.Toolbar):
    """
    A console.

    You can write text into the console
    """

    def __init__(self):
        super().__init__()
        self.max_lines = 2
        self.text_size = 13
        self.row_margin = 5
        self.rows = (
            (self.max_lines) * (self.row_height + self.row_margin)
            + self.padding_top
            + self.padding_bottom
        )

    def newline(self, text) -> "label.Label":
        line = label.Label(text)
        self.add(line)
        return line

    def _add_widget(
        self,
        widget: "widgets.ButtonWidget",
        key: str = None,
    ) -> "widgets.ButtonWidget":
        widget.margin_bottom = self.row_margin
        widget.margin_top = 0
        super()._add_widget(widget, key)
        return widget
