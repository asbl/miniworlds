from typing import Tuple
import miniworlds.actors.parent_actor as parent_actor
import miniworlds.actors.texts.text as text
import miniworlds.actors.shapes.shapes as shapes
import miniworlds.base.api_validation as api_validation


def _ensure_real(value, parameter_name: str) -> None:
    api_validation.ensure_real(
        value,
        parameter_name,
        api_validation.with_try_hint,
        f"{parameter_name} = 100",
    )


def _ensure_position(value, parameter_name: str = "position") -> None:
    api_validation.ensure_position_tuple(
        value,
        parameter_name,
        _ensure_real,
        api_validation.with_try_hint,
    )


class TextBox(parent_actor.ParentActor):
    """A multi-line text box with fixed width and height.

    Long lines are automatically word-wrapped to fit within the given width.
    Each line is rendered as a separate `Text` actor.

    Args:
        position: Top-left position of the text box.
        width: Width of the text box in pixels.
        height: Maximum height of the text box in pixels.
        text: Initial text to display (keyword argument).
        font_size: Font size for all lines (keyword argument, default 18).
        border: If truthy, a rectangle outline is drawn around the box.

    Examples:
        ::

            box = TextBox((10, 10), 380, 200, text="Hello World!")
            box.font_size = 16
    """

    def __init__(
        self, position: Tuple[float, float], width: float, height: float, **kwargs
    ):
        """Creates a text box with fixed width and height.

        Args:
            position: Top-left position of the text box.
            width: Maximum width in pixels before text is wrapped.
            height: Maximum height in pixels.
            border: Optional keyword argument. If truthy, draw a rectangle
                around the text box.
            font_size: Optional keyword argument. Font size used for all lines.
        """
        _ensure_position(position)
        _ensure_real(width, "width")
        _ensure_real(height, "height")
        if width <= 0:
            raise ValueError(f"width must be > 0, got {width}")
        if height <= 0:
            raise ValueError(f"height must be > 0, got {height}")

        super().__init__(position)
        self._visible: bool = False
        self.line_width = width
        self.lines_height = height
        text = kwargs.get("text")
        self.text = text if text else ""
        self.position = position
        font_size = kwargs.get("font_size")
        self.font_size = 18 if not font_size else font_size
        self.create_line_actors()
        border = kwargs.get("border")
        if border:
            shapes.Rectangle(position, width, height)

    def create_line(self, position, txt="") -> text.Text:
        """Create a single `Text` actor for one rendered line.

        Args:
            position: Top-left position of the line.
            txt: Text content of the line.

        Returns:
            The created text actor.
        """
        lineText = text.Text(position, txt)
        if self.font_size != 0:
            lineText.font_size = self.font_size
        lineText.topleft = position
        return lineText

    def create_line_actors(self):
        """Build visible text lines for the current text box content.

        The text is split line by line and then wrapped after words so that no
        rendered line becomes wider than `self.line_width`. Each line is
        stored as a child `Text` actor.

        Examples:
            ::

                box.text = "New text"
                box.create_line_actors()
        """
        dummy = self.create_line((0, 0))
        font = dummy.costume.font_manager.font
        words = [
            line.split(" ") for line in self.text.splitlines()
        ]  # 2D array where each row is a list of words.
        x, y = self.position
        for line in words:
            line_text = ""
            for word in line:
                old_text = line_text
                line_text = line_text + word
                word_size = font.size(line_text)
                word_width, word_height = word_size
                if x + word_width >= self.line_width:
                    line_actor = self.create_line((x, y), old_text)
                    self.children.add(line_actor)
                    x = self.position[0]
                    y += word_height  # Start on new row.
                    line_text = word
                line_text += " "
            if y > self.lines_height:
                break
            line_actor = self.create_line((x, y), line_text)
            self.children.add(line_actor)
            x = self.position[0]  # Reset the x.
            y += line_actor.height  # Start on new row
        dummy.remove()
