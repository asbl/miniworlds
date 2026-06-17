from typing import Tuple
import miniworlds.actors.actor as actor
import miniworlds.actors.texts.text_costume as text_costume


class Text(actor.Actor):
    """Actor that displays text.

    Set `size`, `font_size`, or `max_width` when the complete text should fit
    into a fixed area.

    Args:
        position: Top-left position of the text.
        text: Initial text.

    Examples:
        ::

            score_text = Text((10, 10), "Score: 0")
            score_text.font_size = 24
    """

    def __init__(
        self, position: Tuple[float, float] = (0, 0), text: str = "", **kwargs
    ):
        """Create a text actor.

        Args:
            position: Top-left position as `(x, y)`.
            text: Initial text.

        Examples:
            ::

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
        """Create the text-specific costume.

        Returns:
            A `TextCostume` instance for this actor.
        """
        return text_costume.TextCostume(self)

    @property
    def font_size(self):
        """float: Font size in pixels.

        Examples:
            ::

                text.font_size = 18
        """
        return self.costume.font_size

    @font_size.setter
    def font_size(self, value):
        self._ensure_real(value, "font_size")
        if value < 0:
            raise ValueError(f"font_size must be >= 0, got {value}")
        if self.costume:
            self.costume.font_size = value
            self.costume._update_draw_shape()
            self.costume.set_dirty("write_text", self.costume.RELOAD_ACTUAL_IMAGE)

    def font_by_size(self, width=None, height=None):
        """Choose a font size that fits into a target width or height.

        This is useful when the text should stay inside a fixed box.

        Args:
            width: Maximum width the text should fit into.
            height: Maximum height the text should fit into.

        Examples:
            ::

                headline = Text((20, 20), "Miniworlds")
                headline.font_by_size(width=200)
        """
        self.font_size = self.costume.scale_to_size(width, height)

    @property
    def max_width(self):
        """float: Maximum width used for text rendering and wrapping.

        A value of `0` means no limit.

        Examples:
            ::

                text.max_width = 200
        """
        return self._max_width

    @max_width.setter
    def max_width(self, value):
        self._ensure_real(value, "max_width")
        if value < 0:
            raise ValueError(f"max_width must be >= 0, got {value}")
        self._max_width = value
        self.dirty = 1
        self.costume._update_draw_shape()
        self.costume.set_dirty("write_text", self.costume.RELOAD_ACTUAL_IMAGE)

    def get_text_width(self):
        """Return the rendered text width.

        Returns:
            Width of the text in pixels.

        Examples:
            ::

                if title.get_text_width() > 200:
                    title.font_size = 18
        """
        return self.costume.get_text_width()

    def get_text(self):
        """Return the displayed text.

        Returns:
            Current text.
        """
        return self.costume.text

    @property
    def text(self):
        """str: Displayed text string.

        Examples:
            ::

                if player.lives == 0:
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
        """Set the displayed text and redraw the actor.

        Args:
            text: The new text to show.

        Examples:
            ::

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
        """str: Alias for `text`.

        This property is useful when a text actor should behave like a simple
        value display, for example a score or timer.

        Examples:
            ::

                score.value = "Score: " + str(player.score)
        """
        return self.get_text()

    @value.setter
    def value(self, new_value):
        self.set_text(new_value)

    def get_costume_class(self) -> type["text_costume.TextCostume"]:
        """Return the costume class used by `Text` actors.

        Returns:
            The `TextCostume` class.
        """
        return text_costume.TextCostume
    
    @classmethod
    def from_topleft(
        cls, position: Tuple[float, float] = (0, 0), text: str = "", **kwargs
    ):
        """Create a text actor positioned by its top-left corner.

        Args:
            position: Top-left position of the text actor.
            text: Initial text to display.

        Returns:
            A new `Text` actor.

        Examples:
            ::

                label = Text.from_topleft((10, 10), "Ready")
        """
        text = cls(position, text, **kwargs)
        text.origin = "topleft"
        return text
