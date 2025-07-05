import miniworlds.actors.texts.text as text
import miniworlds.appearances.costume as costume_mod
from typing import Union

class Number(text.Text):
    """
    A number actor shows a Number.

    You have to set the size of the actor with self.size() manually so that
    the complete text can be seen.

    Args:
        position: Top-Left position of Number.
        number: The initial number
        font-size: The size of the font (default: 80)

    Examples:
        Sets a new NumberActor to display the score.::

            self.score = NumberActor(position = (0, 0) number=0)

        Gets the number stored in the NumberActor::

            number = self.score.get_number()

        Sets the number stored in the NumberActor::

            self.score.set_number(3)

    """

    def __init__(self, position=(0, 0), number=0, **kwargs):
        if type(position) == int or type(position) == float:
            raise TypeError(
                f"Error on creating Number. Position is int - Should be a position"
            )
        if type(number) not in [int, float]:
            raise TypeError(f"Error on creating Number. Number should be int or float")
        self.number = 0
        super().__init__(position, **kwargs)
        self.set_number(number)
        self.is_static = True
        self.set_number(self.number)

    def set_value(self, number):
        """Sets the number

        Args:
            number: The number which should be displayed

        Examples:

            Sets the number stored in the NumberActor::

                self.number_actor.set_number(3)

        """
        self.number = number
        self.update_text()

    set_number = set_value

    def get_value(self) -> int:
        """

        Returns:
            The current number

        Examples:

            Gets the number stored in the NumberActor::

                number = self.number_actor.get_number()

        """
        return int(self.costume.text)

    get_number = get_value

    def inc(self):
        """Increases the number by one"""
        self.number += 1
        self.update_text()

    def update_text(self):
        self.set_text(str(self.number))
        self.costume.set_dirty("write_text", costume_mod.Costume.LOAD_NEW_IMAGE)

    def sub(self, value):
        self.number -= value
        self.update_text()

    def add(self, value):
        self.number += value
        self.update_text()

    @property
    def value(self):
        return self.get_value()

    @value.setter
    def value(self, new_value):
        self.set_value(new_value)

    def __neg__(self):
        return - self.value

    def __mul__(self, other: Union[int, float, "Number"]):
        if type(other) in [int, float]:
            self.value = self.value * other
        if type(other) == "Number":
            self.value = self.value * other.value
        return self
    def __add__(self, other: Union[int, float, "Number"]):
        if type(other) in [int, float]:
            self.value = self.value + other
        if type(other) == "Number":
            self.value = self.value + other.value
        return self


    def __sub__(self, other: Union[int, float, "Number"]):
        if type(other) in [int, float]:
            self.value = self.value - other
        if type(other) == "Number":
            self.value = self.value - other.value
        return self