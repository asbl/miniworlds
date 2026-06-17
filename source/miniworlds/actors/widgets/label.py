import miniworlds.actors.widgets.button as widget


class Label(widget.Button):
    """Text label for use in a `Toolbar`.

    `Label` is usually used for headings, status text, scores, or other
    information that should be shown inside a toolbar.

    Args:
        text: The text to display in the label.
        image: Optional path to an image to show instead of (or alongside) text.

    Examples:
        ::

            toolbar = Toolbar()
            score_label = Label("Score: 0")
            toolbar.add(score_label)
            world.camera.add_right(toolbar)
    """

    def __init__(self, text, image=None):
        """Create a label widget.

        Args:
            text: The text displayed by the label.
            image: Optional image path.
        """
        super().__init__(text, image)
        self.event = "label"
        self.data = text
        self.background_color = (255, 255, 255, 0)
