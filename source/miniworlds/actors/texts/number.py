import miniworlds.actors.texts.text as text
import miniworlds.appearances.costume as costume_mod
from typing import Union


class Number(text.Text):
    """
    A number actor that displays a numeric value (integer or float).

    You must manually set the size of the actor with `self.size()` 
    to ensure the text fits the screen.

    Args:
        position (tuple): Top-left position of the number actor.
        number (int or float): The initial number to display.
        **kwargs: Additional arguments passed to the base class.

    Example:
        Create and update a Number actor::

            score = Number(position=(0, 0), number=0)
            score.set_number(3)
            print(score.get_number())
    """

    def __init__(self, position=(0, 0), number=0, **kwargs):
        if isinstance(position, (int, float)):
            raise TypeError(
                "Invalid position type. Expected a tuple, got int or float."
            )
        if not isinstance(number, (int, float)):
            raise TypeError("Number must be an int or float.")
        self.number = 0
        super().__init__(position, **kwargs)
        self.set_number(number)
        self.is_static = True
        self.set_number(self.number)

    def set_value(self, number):
        """
        Set the number to display.

        Args:
            number (int or float): The number to set.

        Example::

            number_actor.set_number(3)
        """
        self.number = number
        self.update_text()

    set_number = set_value

    def get_value(self) -> int:
        """
        Get the current number.

        Returns:
            int: The currently displayed number.

        Example::

            current = number_actor.get_number()
        """
        return int(self.costume.text)

    get_number = get_value

    def inc(self):
        """
        Increase the number by 1.

        Example::

            number_actor.inc()
        """
        self.number += 1
        self.update_text()

    def sub(self, value):
        """
        Subtract a value from the current number.

        Args:
            value (int or float): The value to subtract.

        Example::

            number_actor.sub(5)
        """
        self.number -= value
        self.update_text()

    def add(self, value):
        """
        Add a value to the current number.

        Args:
            value (int or float): The value to add.

        Example::

            number_actor.add(2)
        """
        self.number += value
        self.update_text()

    def update_text(self):
        """
        Update the visual text display to match the current number.
        """
        self.set_text(str(self.number))
        self.costume.set_dirty("write_text", costume_mod.Costume.LOAD_NEW_IMAGE)

    @property
    def value(self):
        """
        Get or set the value of the number.

        Returns:
            int: The current number.
        """
        return self.get_value()

    @value.setter
    def value(self, new_value):
        self.set_value(new_value)

    def __neg__(self):
        """
        Return the negated value of the number.

        Returns:
            int: The negated number.
        """
        return -self.value

    def __mul__(self, other: Union[int, float, "Number"]):
        """
        Multiply this number with another number.

        Args:
            other (int, float, or Number): Value to multiply with.

        Returns:
            Number: The updated self.
        """
        if isinstance(other, (int, float)):
            self.value *= other
        elif isinstance(other, Number):
            self.value *= other.value
        return self

    def __add__(self, other: Union[int, float, "Number"]):
        """
        Add another number to this number.

        Args:
            other (int, float, or Number): Value to add.

        Returns:
            Number: The updated self.
        """
        if isinstance(other, (int, float)):
            self.value += other
        elif isinstance(other, Number):
            self.value += other.value
        return self

    def __sub__(self, other: Union[int, float, "Number"]):
        """
        Subtract another number from this number.

        Args:
            other (int, float, or Number): Value to subtract.

        Returns:
            Number: The updated self.
        """
        if isinstance(other, (int, float)):
            self.value -= other
        elif isinstance(other, Number):
            self.value -= other.value
        return self
