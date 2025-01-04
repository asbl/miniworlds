from typing import Union

import miniworlds.actors.widgets.single_widget as single_widget


class Button(single_widget.SingleWidget):
    def __init__(self, text="", image=""):
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
            raise TypeError("Argument 1 must be of type str, got", type(text), text)
        # additional layout 2
        self.set_background_color((60, 60, 60))

    def on_clicked_left(self, mouse_pos):
        """This event is called when the button is clicked -

        By default, a message with the button text is then sent to the world.

        Examples:

            Send a event on button-click:

            .. code-block:: python

                toolbar = Toolbar()
                button = Button("Start Rocket")
                button.world = toolbar
                world.add_right(toolbar)

                @world.register
                def on_message(self, message):
                    if message == "Start Rocket":
                        rocket.started = True
        """
        if self.cooldown == 0:
            self.send_message(self.get_text())
            self.cooldown = 5

    def act(self):
        if self.cooldown > 0:
            self.cooldown -= 1
