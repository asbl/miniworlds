from typing import Union

import miniworlds.actors.widgets.single_widget as single_widget


class Button(single_widget.SingleWidget):
    """A clickable button widget for use inside a ``Toolbar``.

    When clicked, the button broadcasts its label text as a message to the
    world. The world (or any actor) can react to this message via
    ``on_message``.

    Args:
        text: The label text shown on the button.  This same text is sent as
            a message when the button is clicked.
        image: Optional path to an image shown on the button.

    Examples:

        .. code-block:: python

            from miniworlds import *
            world = World(200, 300)
            toolbar = Toolbar()
            start_btn = Button("Start")
            toolbar.add(start_btn)
            world.camera.add_right(toolbar)

            @world.register
            def on_message(self, message):
                if message == "Start":
                    print("Game started!")

            world.run()
    """

    def __init__(self, text: str = "", image: str = "") -> None:
        """Creates a toolbar button.

        Args:
            text: The button label and the message that will be sent on click.
            image: Optional image path for the button.
        """
        # constructors
        super().__init__()
        self.overflow = False
        self.cooldown = 0
        if image:
            self.set_image(image)
        # text attributes
        try:
            self.set_text(text)
        except TypeError:
            raise TypeError(
                f"Button text must be a string like 'Click me', got {type(text).__name__}: {repr(text)}"
            )
        # additional layout 2
        self.set_background_color((60, 60, 60))

    def on_clicked_left(self, mouse_pos: tuple[int, int]) -> None:
        """Called when the button is clicked.

        By default, a message with the button text is then sent to the world.

        Examples:

            Send a event on button-click:

            .. code-block:: python

                toolbar = Toolbar()
                button = Button("Start Rocket")
                button.world = toolbar
                world.camera.add_right(toolbar)

                @world.register
                def on_message(self, message):
                    if message == "Start Rocket":
                        rocket.started = True
        """
        if self.cooldown == 0:
            self.send_message(self.get_text())
            self.cooldown = 5

    def act(self) -> None:
        """Counts down the short click cooldown.

        The cooldown prevents the button from sending the same message several
        times in a few frames while the mouse button is still held down.
        """
        if self.cooldown > 0:
            self.cooldown -= 1
