import miniworlds.actors.widgets.label as label
import miniworlds.actors.widgets.widget_base as widget_base
import miniworlds.worlds.gui.toolbar as toolbar


class Console(toolbar.Toolbar):
    """A scrolling text console that can be docked to a world.

    Use `console.newline(text)` to append lines of text. The console is a
    special `Toolbar` that is typically docked below or beside the main world
    using `world.camera.add_bottom(console)` or `world.camera.add_right(console)`.

    Only the last ``max_lines`` lines are kept: when the console is full,
    the oldest line is removed, so the console's memory use stays constant
    even if `newline` is called every frame.

    Examples:
        ::

            console = Console()
            world.camera.add_bottom(console)

            @world.register
            def act(self):
                console.newline("Frame: " + str(world.frame))
    """

    def __init__(self):
        """Creates a console toolbar with compact text rows.

        The console starts with a small default height and is intended for short
        log messages such as score changes, instructions, or debug output.
        """
        super().__init__()
        self.max_lines = 2
        self.text_size = 13
        self.row_margin = 5

    def newline(self, text) -> "label.Label":
        """Appends a new line of text to the console.

        Each call adds one label row. When more than ``max_lines`` lines
        exist, the oldest line is removed and the remaining lines move up.

        Args:
            text: The text string to display on the new line.

        Returns:
            The `Label` actor that was created for this line.

        Examples:
            ::

                console.newline("Player position: " + str(player.position))
        """
        line = label.Label(text)
        self.add(line)
        return line

    def _add_widget(
        self,
        widget: "widget_base.BaseWidget",
        key=None,
    ) -> "widget_base.BaseWidget":
        widget.margin_bottom = self.row_margin
        widget.margin_top = 0
        super()._add_widget(widget, key)
        self._trim_old_lines()
        return widget

    def _trim_old_lines(self):
        """Removes the oldest lines until at most ``max_lines`` remain."""
        trimmed = False
        while len(self.widgets) > self.max_lines:
            oldest_key = next(iter(self.widgets))
            oldest_widget = self.widgets.pop(oldest_key)
            self._unregister_widget(oldest_widget)
            oldest_widget.remove()
            trimmed = True
        if trimmed:
            self.reorder()
            total_height = self._widgets_total_height()
            self.camera.world_size_y = max(self.camera.height, total_height)
            self.camera.y = max(0, total_height - self.camera.height)
