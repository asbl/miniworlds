import miniworlds.actors.widgets.single_widget as single_widget


class Label(single_widget.SingleWidget):
    """Text label for use in a `Toolbar`.

    `Label` is usually used for headings, status text, scores, or other
    information that should be shown inside a toolbar. Unlike `Button`,
    a label is not clickable and does not send messages.

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
        super().__init__(text=text)
        if image:
            self.set_image(image)
        # Same background as Button; kept explicit because Label no longer
        # inherits from Button.
        self.set_background_color((60, 60, 60))
