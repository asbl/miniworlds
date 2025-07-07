from typing import Tuple
import miniworlds.actors.parent_actor as parent_actor
import miniworlds.actors.texts.text as text
import miniworlds.actors.shapes.shapes as shapes


class TextBox(parent_actor.ParentActor):
    def __init__(
        self, position: Tuple[float, float], width: float, height: float, **kwargs
    ):
        """Generates a textbox with fixed width and height

        Args:
            position (Tuple[float, float]): The topleft position of textbox
            width (float): The width of the textbox
            height (float): The height of the textbox
            **border (bool): Does the textbox has a border?
            **font_size (int): The font size
        """
        super().__init__([])
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
        """Creates a new text-line

        Args:
            position (_type_): position of line
            txt (str, optional): Text of line. Defaults to "".

        Returns:
            text.Text: A Text-Actor
        """
        lineText = text.Text(position, txt)
        if self.font_size != 0:
            lineText.font_size = self.font_size
        lineText.topleft = position
        return lineText

    def create_line_actors(self):
        """creates the lines actor - One actor per line.
        Split long lines after words.
        """
        dummy = self.create_line((0, 0))
        font = dummy.costume.font_manager.font
        words = [
            world.split(" ") for word in self.text.splitlines()
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
                    self.children.append(line_actor)
                    x = self.position[0]
                    y += word_height  # Start on new row.
                    line_text = word
                line_text += " "
            if y > self.lines_height:
                break
            line_actor = self.create_line((x, y), line_text)
            self.children.append(line_actor)
            x = self.position[0]  # Reset the x.
            y += line_actor.height  # Start on new row
        dummy.remove()
