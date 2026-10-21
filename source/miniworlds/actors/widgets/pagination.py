import miniworlds.actors.widgets.button as button
import miniworlds.actors.widgets.container_widget as container_widget


class PagerButtonsHorizontal(container_widget.ContainerWidget):
    """Two buttons (up/down) that scroll the observed GUI by 10 pixels.

    Args:
        gui: The toolbar or console that is scrolled by the buttons.
        up_text: Label of the scroll-up button.
        down_text: Label of the scroll-down button.
    """

    def __init__(self, gui, up_text="↑", down_text="↓"):
        self.up = button.Button(up_text)
        self.down = button.Button(down_text)
        super().__init__([self.up, self.down])
        self.gui = gui
        self.up.gui = gui
        self.down.gui = gui

        @self.up.register
        def on_clicked_left(self, pos):
            self.gui.scroll_up(10)

        # Both buttons must use the same event handler name; they are
        # registered on different widgets, so the redefinition is safe.
        @self.down.register
        def on_clicked_left(self, pos):  # noqa: F811
            self.gui.scroll_down(10)
