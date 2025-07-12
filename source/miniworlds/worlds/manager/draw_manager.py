from collections import defaultdict
from typing import Any, Callable, Optional, Union, Tuple
from collections import defaultdict
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.world as world_mod
import miniworlds.tools.actor_class_inspection as actor_class_inspection
import miniworlds.tools.inspection as inspection
import miniworlds.tools.color as color

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
        print(value, self._default_fill_color)

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
        """Set default border color for borders and lines.

        .. note::

          ``world.default_border_color`` does not have an effect, if no border is set.

            You must also set ``world.border`` > 0.

        Examples:

            Create actors with and without with border

            .. code-block:: python

                from miniworlds import *

                world = World(210,80)
                world.default_border_color = (0,0, 255)
                world.default_border = 1

                t = Actor((10,10))

                t2 = Actor ((60, 10))
                t2.border_color = (0,255, 0)
                t2.border = 5 # overwrites default border

                t3 = Actor ((110, 10))
                t3.border = None # removes border

                t4 = Actor ((160, 10))
                t4.add_costume("images/player.png") # border for sprite

                world.run()

            Output:

            .. image:: ../_images/border_color.png
                :width: 200px
                :alt: borders

        """
        return self._default_border_color

    @default_border_color.setter
    def default_border_color(self, value):
        self._default_border_color = value

    @property
    def default_border(self):
        """Sets default border color for actors

        .. note::

          You must also set a border for actor.

        Examples:

            Set default border for actors:

            .. code-block:: python

                from miniworlds import *

                world = World(210,80)
                world.default_border_color = (0,0, 255)
                world.default_border = 1

                t = Actor((10,10))

                world.run()
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
        """
        Returns the color at a specific position

        Examples:

            .. code-block:: python

                from miniworlds import *

                world = World(100,60))

                @world.register
                def on_setup(self):
                    self.add_background((255,0,0))
                    print(self.get_color_from_pixel((5,5)))

                world.run()

            Output: (255, 0, 0, 255)

            .. image:: ../_images/get_color.png
                :width: 100px
                :alt: get color of red screen

        Args:
            position: The position to search for

        Returns:
            The color

        """
        return self.world.background.image.get_at((int(position[0]), int(position[1])))