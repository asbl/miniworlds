import logging
from collections import defaultdict
from typing import Any, Callable, Optional, Union, Tuple
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.world as world_mod
import miniworlds.tools.actor_class_inspection as actor_class_inspection
import miniworlds.tools.inspection as inspection
import miniworlds.tools.color as color


logger = logging.getLogger(__name__)

class DrawManager:
    def __init__(self, world):
        self.world = world  
        self._default_is_filled = False
        self._default_fill_color = None
        self._default_border_color = None
        self._default_border = None
        self._is_filled: bool = False
 
    
    @property
    def default_fill_color(self):
        """Set default fill color for borders and lines"""
        return self._default_fill_color

    @default_fill_color.setter
    def default_fill_color(self, value: int|Tuple):
        self._default_fill_color = color.Color.create(value).get()
        logger.debug(
            "Updated default fill color from %s to normalized %s",
            value,
            self._default_fill_color,
        )

    def default_fill(self, value):
        """Set default fill color for borders and lines"""
        self._is_filled = value
        if self.default_is_filled is not None and self.default_is_filled:
            self._default_fill_color = color.Color.create(value).get()

    @property
    def default_is_filled(self):
        return self._default_is_filled

    def fill(self, value):
        self.default_fill_color = value

    @default_is_filled.setter
    def default_is_filled(self, value):
        self.default_fill(value)

    @property
    def default_stroke_color(self):
        """Set default stroke color for borders and lines. (equivalent to border-color)"""
        return self.default_border_color

    @default_stroke_color.setter
    def default_stroke_color(self, value):
        """Set default stroke color for borders and lines. (equivalent to border-color)"""
        self.default_border_color = value

    def stroke(self, value):
        self.default_stroke_color = value

    @property
    def default_border_color(self):
        """tuple: Default border color for actors and lines.

        Set `world.default_border` to a value greater than `0` to make the
        border visible.

        Examples:
            ::

                world.draw.default_border_color = (0, 0, 255)
                world.draw.default_border = 1
                actor = Actor((10, 10))
        """
        return self._default_border_color

    @default_border_color.setter
    def default_border_color(self, value):
        self._default_border_color = value

    @property
    def default_border(self):
        """int: Default border width for actors.

        Examples:
            ::

                world.draw.default_border = 1
                world.draw.default_border_color = (0, 0, 255)
        """
        return self._default_border

    @default_border.setter
    def default_border(self, value):
        self._default_border = value


    @property
    def fill_color(self):
        return self.world.background.fill_color

    @fill_color.setter
    def fill_color(self, value):
        self.world.background.fill(value)

    # Alias
    color = fill_color

    def get_color_from_pixel(self, position: Tuple[float, float]) -> tuple:
        """Return the background color at a pixel position.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            Color tuple at the pixel.

        Examples:
            ::

                world.add_background((255, 0, 0))
                color = world.draw.get_color_from_pixel((5, 5))
        """
        return self.world.background.image.get_at((int(position[0]), int(position[1])))
