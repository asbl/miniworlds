from typing import Tuple
import miniworlds.actors.actor as actor
import miniworlds.actors.texts.text_costume as text_costume


class Text(actor.Actor):
    """
    A Text-Actor is a actor which contains a Text.

    You have to set the size of the actor with self.size() manually so that
    the complete text can be seen.

    Args:
        position: Top-Left position of Text.
        text: The initial text

    Examples:

        Create a new texts::

            self.text = TextActor((1,1), "Hello World")
    """

    def __init__(
        self, position: Tuple[float, float] = (0, 0), text: str = "", **kwargs
    ):
        """Creates a text actor.

        Args:
            position: Top-left position of the text actor, e.g. ``(100, 50)``.
            text: The initial text to display.

        Examples:

            Show the current score in the top-left corner:

            .. code-block:: python

                score_text = Text((10, 10), "Score: 0")

                @world.register
                def act(self):
                    score_text.text = "Score: " + str(player.score)
        """
        self._max_width = 0
        super().__init__(position, **kwargs)
        self.font_size = 24
        self.costume.is_scaled = True
        self.is_static: bool = True
        self.fixed_size = False
        self.set_text(text)
        self.costume._update_draw_shape()
        self.costume.set_dirty("write_text", self.costume.RELOAD_ACTUAL_IMAGE)

    def new_costume(self):
        """Creates the text-specific costume used to draw the string.

        Returns:
            A ``TextCostume`` instance for this actor.
        """
        return text_costume.TextCostume(self)

    @property
    def font_size(self):
        """Gets or sets the font size in pixels.

        Examples:

            Sets the font size to ``10``::

                text.font_size = 10

        Returns:
            The current font size.
        """
        return self.costume.font_size

    @font_size.setter
    def font_size(self, value):
        if self.costume:
            self.costume.font_size = value
            self.costume._update_draw_shape()
            self.costume.set_dirty("write_text", self.costume.RELOAD_ACTUAL_IMAGE)

    def font_by_size(self, width=None, height=None):
        """Chooses a font size that fits into a target width or height.

        This is useful when the text should stay inside a fixed box.

        Args:
            width: Maximum width the text should fit into.
            height: Maximum height the text should fit into.

        Examples:

            Fit a headline into a 200 pixel wide box:

            .. code-block:: python

                headline = Text((20, 20), "Miniworlds")
                headline.font_by_size(width=200)
        """
        self.font_size = self.costume.scale_to_size(width, height)

    @property
    def max_width(self):
        """Maximum width used for text rendering and wrapping logic.

        Set this value when the text should stay within a fixed width.

        Returns:
            The current maximum width in pixels. ``0`` means no limit.
        """
        return self._max_width

    @max_width.setter
    def max_width(self, value):
        self._max_width = value
        self.dirty = 1
        self.costume._update_draw_shape()
        self.costume.set_dirty("write_text", self.costume.RELOAD_ACTUAL_IMAGE)

    def get_text_width(self):
        """Returns the width of the currently rendered text in pixels.

        Returns:
            Width of the text in pixels.

        Examples:

            .. code-block:: python

                if title.get_text_width() > 200:
                    title.font_size = 18
        """
        return self.costume.get_text_width()

    def get_text(self):
        """Gets the currently displayed text

        Returns:
            The currently displayed text

        """
        return self.costume.text

    @property
    def text(self):
        """The displayed text string.

        Set this property to update what is shown:

        .. code-block:: python

            label.text = "Game Over"
        """
        return self.get_text()

    @text.setter
    def text(self, value):
        if value == "":
            value = " "
        self.set_text(value)
        self.costume.set_dirty("all", self.costume.RELOAD_ACTUAL_IMAGE)

    def set_text(self, text):
        """Sets the displayed text and redraws the actor.

        Args:
            text: The new text to show.

        Examples:

            .. code-block:: python

                message.set_text("Press space to start")
        """
        self.position_manager.store_origin()
        self.costume.text = text
        self.costume._update_draw_shape()
        self.costume.set_dirty("write_text", self.costume.RELOAD_ACTUAL_IMAGE)
        self.position_manager.restore_origin()
        
    def on_shape_change(self):
        """Updates the text layout after the actor shape has changed.

        This hook is called internally when size-related properties change.
        """
        self.costume._update_draw_shape()

    @property
    def value(self):
        """Alias for ``text``.

        This property is useful when a text actor should behave like a simple
        value display, for example a score or timer.

        Examples:

            .. code-block:: python

                score.value = "Score: " + str(points)
        """
        return self.get_text()

    @value.setter
    def value(self, new_value):
        self.set_text(new_value)

    def get_costume_class(self) -> type["text_costume.TextCostume"]:
        """Returns the costume class used by ``Text`` actors.

        Returns:
            The ``TextCostume`` class.
        """
        return text_costume.TextCostume
    
    @classmethod
    def from_topleft(
        cls, position: Tuple[float, float] = (0, 0), text: str = "", **kwargs
    ):
        """Creates a text actor whose origin is interpreted as the top-left corner.

        Args:
            position: Top-left position of the text actor.
            text: Initial text to display.

        Returns:
            A new ``Text`` actor.
        """
        text = cls(position, text, **kwargs)
        text.origin = "topleft"
        return text