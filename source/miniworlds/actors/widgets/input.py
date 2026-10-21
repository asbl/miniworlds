import logging
from typing import Union
import miniworlds.actors.shapes.shapes as shapes
import miniworlds.actors.widgets.button as widget


logger = logging.getLogger(__name__)


class Input(widget.Button):
    """Text input field for use inside a `Toolbar`.

    Click into the field to focus it, then type to enter text. The
    text cursor can be moved with the arrow keys; BACKSPACE deletes
    the character left of the cursor. At most ``max_chars`` characters
    can be entered.

    While the input has focus, the text cursor blinks; without focus,
    the cursor is hidden.

    Examples:
        ::

            toolbar = Toolbar()
            name_input = Input((0, 0))
            name_input.max_chars = 20
            toolbar.add(name_input)
            world.camera.add_right(toolbar)
    """

    def __init__(self, position):
        super().__init__("")
        self.background_color = (255, 255, 255, 0)
        self.position = position
        self._max_chars = 10
        self.current_input = ""
        self._cursor_position = 0
        self.cursor_x = self.x
        self.cursor = shapes.Line((0, 0), (100, 100))  # set in update_cursor
        self.cursor.border_color = (255, 255, 255, 255)
        self.fixed_width = True
        self.is_focusable = True
        cursor = self.cursor  # for decorator

        @cursor.register
        def act(self):
            if self._parent.has_focus:
                if self.world.frame % 20 == 0 and not self.world.frame % 40 == 0:
                    self.hide()
                if self.world.frame % 40 == 0:
                    self.show()
            else:
                self.hide()

        self.update_cursor()
        self.add_child(self.cursor)

    @property
    def max_chars(self):
        return self._max_chars

    @max_chars.setter
    def max_chars(self, value):
        self._max_chars = value
        self.resize()

    def update_cursor(self):
        font_size = self.text.font_size
        if self.cursor_position == 0:
            self.cursor_x = self.x
        else:
            self.cursor_x = self.x + self.text.costume.font_manager.get_text_width(
                self.current_input[0 : self.cursor_position]
            )
        self.cursor.start_position = (self.cursor_x + font_size / 2, self.y)
        self.cursor.end_position = (self.cursor_x + font_size / 2, self.y + self.height)

    @property
    def cursor_position(self):
        return self._cursor_position

    @cursor_position.setter
    def cursor_position(self, value):
        self._cursor_position = value
        self.update_cursor()

    def set_text(self, text: Union[str, int, float]):
        self.current_input = text
        super().set_text(text)

    def on_key_down(self, keys):
        if self.has_focus:
            if "LEFT" in keys and self.cursor_position > 0:
                self.cursor_position -= 1
            elif "RIGHT" in keys and self.cursor_position < len(self.current_input):
                self.cursor_position += 1
            elif "BACKSPACE" in keys:
                if 0 < self.cursor_position <= len(self.current_input):
                    self.cursor_position -= 1
                    self.set_text(
                        self.current_input[0 : self.cursor_position]
                        + self.current_input[self.cursor_position + 1 :]
                    )

    def on_text_input(self, text):
        """Inserts composed text (including umlauts and spaces) at the cursor.

        Printable characters arrive through the ``text_input`` event, so key
        names like "SPACE" are never inserted as literal text.
        """
        if not self.has_focus or not text:
            return
        if len(self.current_input) >= self.max_chars:
            return
        self.set_text(
            self.current_input[0 : self.cursor_position]
            + text
            + self.current_input[self.cursor_position :]
        )
        self.cursor_position += 1
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Updated input cursor to x=%s y=%s width=%s height=%s",
                self.cursor.x,
                self.cursor.y,
                self.cursor.width,
                self.cursor.height,
            )

    def on_focus(self):
        logger.debug("Input widget gained focus")

    def on_focus_lost(self):
        logger.debug("Input widget lost focus")
