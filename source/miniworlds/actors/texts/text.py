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
        """_summary_

        Args:
            position (tuple, optional): _description_. Defaults to (0,0).
            text (Optional[int]): The text (otherwise empty string "")
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
        return text_costume.TextCostume(self)

    @property
    def font_size(self):
        """Set font size to a value, e.g. 10, 12, ...

        Examples:

        Sets size of actor to 10::

            text.font_size = 10
        """
        return self.costume.font_size

    @font_size.setter
    def font_size(self, value):
        if self.costume:
            self.costume.font_size = value
            self.costume._update_draw_shape()
            self.costume.set_dirty("write_text", self.costume.RELOAD_ACTUAL_IMAGE)

    def font_by_size(self, width=None, height=None):
        self.font_size = self.costume.scale_to_size(width, height)

    @property
    def max_width(self):
        return self._max_width

    @max_width.setter
    def max_width(self, value):
        self._max_width = value
        self.dirty = 1
        self.costume._update_draw_shape()
        self.costume.set_dirty("write_text", self.costume.RELOAD_ACTUAL_IMAGE)

    def get_text_width(self):
        return self.costume.get_text_width()

    def get_text(self):
        """Gets the currently displayed text

        Returns:
            The currently displayed text

        """
        return self.costume.text

    @property
    def text(self):
        """changes the text."""
        return self.get_text()

    @text.setter
    def text(self, value):
        if value == "":
            value = " "
        self.set_text(value)
        self.costume.set_dirty("all", self.costume.RELOAD_ACTUAL_IMAGE)

    def set_text(self, text):
        """
        Sets the text of the actor

        Args:
            text: The text
        """
        self.position_manager.store_origin()
        self.costume.text = text
        self.costume._update_draw_shape()
        self.costume.set_dirty("write_text", self.costume.RELOAD_ACTUAL_IMAGE)
        self.position_manager.restore_origin()
        
    def on_shape_change(self):
        self.costume._update_draw_shape()

    @property
    def value(self):
        return self.get_text()

    @value.setter
    def value(self, new_value):
        self.set_text(new_value)

    def get_costume_class(self) -> type["text_costume.TextCostume"]:
        return text_costume.TextCostume
    
    @classmethod
    def from_topleft(
        cls, position: Tuple[float, float] = (0, 0), text: str = "", **kwargs
    ):
        """Creates a circle with topleft at position"""
        text = cls(position, text, **kwargs)
        text.origin = "topleft"
        return text