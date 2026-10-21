import miniworlds.actors.widgets.button as button
import miniworlds.actors.widgets.container_widget as container_widget


class YesNoButton(container_widget.ContainerWidget):
    """A widget with a yes and a no button side by side.

    Use ``get_yes_button()`` and ``get_no_button()`` to access the two
    buttons, e.g. to style them or to register custom click handlers.

    Args:
        yes_text: Label of the yes button.
        no_text: Label of the no button.

    Examples:
        ::

            toolbar = Toolbar()
            choice = YesNoButton("Yes", "No")
            choice.get_yes_button().background_color = (0, 255, 0)
            toolbar.add(choice)
    """

    def __init__(self, yes_text, no_text):
        self.yes = button.Button(yes_text)
        self.no = button.Button(no_text)
        super().__init__([self.yes, self.no])
        self.row_height = 80

    def get_yes_button(self):
        return self.yes

    def get_no_button(self):
        return self.no
