import pygame
from typing import Optional


class MouseManager:
    def __init__(self, world):
        self.world = world
        self._mouse_position = None
        self._prev_mouse_position = None

    def _update_positions(self):
        self._prev_mouse_position = self._mouse_position
        self._mouse_position = self.get_mouse_position()

    def get_mouse_position(self):
        pos = pygame.mouse.get_pos()
        clicked_container = self.world.app.worlds_manager.get_world_by_pixel(pos[0], pos[1])
        if clicked_container == self.world:
            return pos
        else:
            return None

    @property
    def mouse_position(self):
        return self.get_mouse_position()

    @property
    def prev_mouse_position(self):
        return self._prev_mouse_position

    def mouse_left_is_clicked(self):
        return pygame.mouse.get_pressed()[0]

    def mouse_right_is_clicked(self):
        return pygame.mouse.get_pressed()[0]


    def get_mouse_position(self) -> Optional[tuple]:
        """
        Gets the current mouse_position

        Returns:
            Returns the mouse position if mouse is on the world. Returns None otherwise

        Examples:

            Create circles at current mouse position:


            .. code-block:: python

                from miniworlds import *

                world = PixelWorld()

                @world.register
                def act(self):
                    c = Circle(world.get_mouse_position(), 40)
                    c.color = (255,255,255, 100)
                    c.border = None

                world.run()

            Output:

            .. image:: ../_images/mousepos.png
                :width: 200px
                :alt: Circles at mouse-position


        """
        return self._mouse_position

    def get_mouse_x(self) -> int:
        """Gets x-coordinate of mouse-position"""
        if self.mouse_position:
            return self.mouse_position[0]
        else:
            return 0

    def get_mouse_y(self) -> int:
        """Gets y-coordinate of mouse-position"""
        if self.mouse_position:
            return self.mouse_position[1]
        else:
            return 0

    def get_prev_mouse_position(self):
        """gets mouse-position of last frame"""
        return self.mouse_manager.prev_mouse_position

    def is_mouse_pressed(self) -> bool:
        """Returns True, if mouse is pressed"""
        return (
            self.mouse_left_is_clicked()
            or self.mouse_left_is_clicked()
        )

    def is_mouse_left_pressed(self) -> bool:
        """Returns True, if mouse left button is pressed"""
        return self.mouse_left_is_clicked()

    def is_mouse_right_pressed(self) -> bool:
        """Returns True, if mouse right button is pressed"""
        return self.mouse_right_is_clicked()