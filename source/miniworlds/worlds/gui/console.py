import miniworlds.worlds.gui.toolbar as toolbar
import miniworlds.actors.widgets.label as label
import miniworlds.actors.widgets as widgets


class Console(toolbar.Toolbar):
    """A scrolling text console that can be docked to a world.

    Use ``console.newline(text)`` to append lines of text. The console is a
    special ``Toolbar`` that is typically docked below or beside the main world
    using ``world.camera.add_bottom(console)`` or
    ``world.camera.add_right(console)``.

    Examples:

        .. code-block:: python

            from miniworlds import *
            world = World(200, 200)
            console = Console()
            world.camera.add_bottom(console)

            @world.register
            def act(self):
                console.newline("Frame: " + str(world.frame))

            world.run()
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
        self.rows = (
            (self.max_lines) * (self.row_height + self.row_margin)
            + self.padding_top
            + self.padding_bottom
        )

    def newline(self, text) -> "label.Label":
        """Appends a new line of text to the console.

        Each call adds one label row. Older lines scroll up when the console
        is full.

        Args:
            text: The text string to display on the new line.

        Returns:
            The ``Label`` actor that was created for this line.

        Examples:

            .. code-block:: python

                console.newline("Player position: " + str(player.position))
        """
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
