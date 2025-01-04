from typing import Tuple, Optional

import miniworlds.actors.widgets.button as button
import miniworlds.actors.widgets.container_widget as container_widget


class PagerButtonsHorizontal(container_widget.ContainerWidget):
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

        @self.down.register
        def on_clicked_left(self, pos):
            self.gui.scroll_down(10)

