from typing import Tuple, Union

class Color:
    """Represents an RGB or RGBA color as a tuple of float values."""

    def __init__(self, value: Tuple[float, ...]) -> None:
        """
        Initialize a Color object with an RGB or RGBA tuple.

        Args:
            value: A tuple of 3 (RGB) or 4 (RGBA) float values.

        Raises:
            ValueError: If the tuple does not have 3 or 4 elements.
        """
        if len(value) not in (3, 4):
            raise ValueError("Color tuple must contain 3 (RGB) or 4 (RGBA) float values.")
        self.color_tuple: Tuple[float, ...] = value

    @classmethod
    def create(cls, value: Union[float, Tuple[float, ...]]) -> "Color":
        """
        Create a Color object from a float or a tuple of floats.

        - Single float → grayscale RGB
        - Tuple with 1 value → grayscale RGB
        - Tuple with 3 values → RGB
        - Tuple with 4 values → RGBA

        Args:
            value: A float or a tuple with 1, 3, or 4 float values.

        Returns:
            A Color object.

        Raises:
            ValueError: If the tuple length is not 1, 3, or 4.
            TypeError: If the input type is invalid.
        """
        if isinstance(value, tuple):
            if len(value) == 1:
                value = (value[0], value[0], value[0])
            elif len(value) not in (3, 4):
                raise ValueError("Tuple must contain 1, 3, or 4 float values.")
        elif isinstance(value, float):
            value = (value, value, value)
        else:
            raise TypeError("Value must be a float or a tuple of 1, 3, or 4 float values.")

        return cls(tuple(float(v) for v in value))

    def get(self) -> Tuple[float, ...]:
        """
        Return the RGB or RGBA tuple representing the color.

        Returns:
            A tuple of 3 or 4 float values representing the color.
        """
        return self.color_tuple
