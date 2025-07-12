import pygame
from typing import Optional, Tuple


class MouseManager:
    """
    Manages mouse input for a given world. Provides access to current mouse position,
    click states, and previous mouse state.

    Usage:
        >>> world.mouse.get_position()
        >>> world.mouse.is_left()
    """

    def __init__(self, world) -> None:
        """
        Initialize the MouseManager.

        Args:
            world: The world instance this mouse belongs to.
        """
        self.world = world
        self._mouse_position: Optional[Tuple[int, int]] = None
        self._prev_mouse_position: Optional[Tuple[int, int]] = None

    def _update_positions(self) -> None:
        """
        Updates the current and previous mouse positions.
        Should be called once per frame.

        Examples:
            >>> world.mouse.update()
        """
        self._prev_mouse_position = self._mouse_position
        self._mouse_position = self.get_position()

    def get_position(self) -> Optional[Tuple[int, int]]:
        """
        Gets the current mouse position if the mouse is over this world.

        Returns:
            Tuple of (x, y) coordinates or None if mouse is not on this world.

        Examples:
            >>> pos = world.mouse.get_position()
            >>> if pos:
            ...     print("Mouse over world at", pos)
        """
        pos = pygame.mouse.get_pos()
        detected_world = self.world.app.worlds_manager.get_world_by_pixel(pos[0], pos[1])
        if detected_world == self.world:
            return pos
        return None

    @property
    def position(self) -> Optional[Tuple[int, int]]:
        """
        Property version of get_position()

        Examples:
            >>> if world.mouse.position:
            ...     print("Mouse is on world!")
        """
        return self.get_position()

    @property
    def last_position(self) -> Optional[Tuple[int, int]]:
        """
        Returns the mouse position from the previous frame.

        Examples:
            >>> prev = world.mouse.last_mouse_position
            >>> if prev:
            ...     print("Mouse was at:", prev)
        """
        return self._prev_mouse_position

    def left(self) -> bool:
        """
        Returns True if the left mouse button is currently pressed.

        Examples:
            >>> if world.mouse.mouse_left_is_clicked():
            ...     print("Left button is down")
        """
        return pygame.mouse.get_pressed()[0]

    def right(self) -> bool:
        """
        Returns True if the right mouse button is currently pressed.

        Examples:
            >>> if world.mouse.mouse_right_is_clicked():
            ...     print("Right button is down")
        """
        return pygame.mouse.get_pressed()[2]

    def x(self) -> int:
        """
        Returns the x-coordinate of the mouse if over the world, otherwise 0.

        Examples:
            >>> x = world.mouse.x()
        """
        if self.position:
            return self.position[0]
        return 0

    def y(self) -> int:
        """
        Returns the y-coordinate of the mouse if over the world, otherwise 0.

        Examples:
            >>> y = world.mouse.get_mouse_y()
        """
        if self.position:
            return self.position[1]
        return 0

    def get_last_position(self) -> Optional[Tuple[int, int]]:
        """
        Returns the mouse position from the last frame (if available).

        Examples:
            >>> last = world.mouse.get_last_mouse_position()
        """
        return self._prev_mouse_position

    def is_mouse_pressed(self) -> bool:
        """
        Returns True if any mouse button (left or right) is currently pressed.

        Examples:
            >>> if world.mouse.is_mouse_pressed():
            ...     print("Mouse is down")
        """
        return (
            self.mouse_left_is_clicked()
            or self.mouse_right_is_clicked()
        )

    def is_mouse_left_pressed(self) -> bool:
        """
        Returns True if the left mouse button is pressed.

        Examples:
            >>> if world.mouse.is_mouse_left_pressed():
            ...     print("Left click detected")
        """
        return self.mouse_left_is_clicked()

    def is_mouse_right_pressed(self) -> bool:
        """
        Returns True if the right mouse button is pressed.

        Examples:
            >>> if world.mouse.is_mouse_right_pressed():
            ...     print("Right click detected")
        """
        return self.mouse_right_is_clicked()

    