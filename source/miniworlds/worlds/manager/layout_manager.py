import pygame
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from miniworlds.worlds.world import World
    from miniworlds.base.app import App


class LayoutManager:
    """
    LayoutManager handles the positioning and management of World objects within an application window.

    It is accessed via `world.layout` and delegates layout behavior (e.g., docking, switching, removing)
    to the underlying `App` and `WorldsManager`.
    """

    def __init__(self, world: "World", app: "App") -> None:
        """
        Initialize a LayoutManager for a given world and application.

        Args:
            world: The World instance that owns this layout manager.
            app: The application instance managing all worlds.

        Example:
            >>> world.layout = LayoutManager(world, app)
        """
        self.world: "World" = world
        self.app: "App" = app
        self.docking_position: Optional[str] = None  # e.g., "right", "bottom"

    def add_right(self, world: "World", size: int = 100) -> "World":
        """
        Adds a new world to the right side of the current world.

        Args:
            world: The World instance to dock.
            size: Width of the added world in pixels (default: 100).

        Returns:
            The newly added World instance.

        Example:
            >>> world.layout.add_right(Toolbar(), size=150)
        """
        return self.app.worlds_manager.add_world(world, dock="right", size=size)

    def add_bottom(self, world: "World", size: int = 100) -> "World":
        """
        Adds a new world below the current world.

        Args:
            world: The World instance to dock.
            size: Height of the added world in pixels (default: 100).

        Returns:
            The newly added World instance.

        Example:
            >>> world.layout.add_bottom(Console(), size=200)
        """
        return self.app.worlds_manager.add_world(world, dock="bottom", size=size)

    def remove_world(self, world: "World") -> None:
        """
        Removes a world from the current layout.

        Args:
            world: The World instance to remove.

        Example:
            >>> world.layout.remove_world(toolbar)
        """
        self.app.worlds_manager.remove_world(world)

    def switch_world(self, new_world: "World", reset: bool = False) -> None:
        """
        Switches focus to another world.

        Args:
            new_world: The World instance to activate.
            reset: Whether to reset the world state (default: False).

        Example:
            >>> world.layout.switch_world(main_scene, reset=True)
        """
        self.app.worlds_manager.switch_world(self.world, new_world, reset)

    @property
    def window_docking_position(self) -> Optional[str]:
        """
        Returns the docking position of this world in the window layout.

        Returns:
            A string such as "right" or "bottom", or None if undocked.

        Example:
            >>> world.layout.window_docking_position
            'right'
        """
        return self.docking_position

    def _add_to_window(self, app: "App", dock: str, size: int = 100) -> None:
        """
        Internal method to integrate this world into the window system.

        This is typically called by the WorldsManager during world addition.

        Args:
            app: The application instance.
            dock: The docking position ("right", "bottom", etc.).
            size: The pixel size of the world in the layout.

        Example (not called manually):
            >>> world.layout._add_to_window(app, dock="bottom", size=150)
        """
        self.world._app = app
        self.app = app
        self.world._window = self.world._app.window
        self.docking_position = dock
        self.world._image = pygame.Surface((self.world.width, self.world.height))
