import pygame

class LayoutManager:

    def __init__(self, world, app):
        self.world = world  
        self.app = app  
        self.docking_position = None  # Set in add_to_window
    
    def add_right(self, world: "World", size: int = 100):
        """Adds a world to the right of the current world.

        Args:
            world: The world instance to add.
            size: Width of the new world in pixels (default: 100).

        Returns:
            The added world.
        """
        return self.app.worlds_manager.add_world(world, "right", size)


    def add_bottom(self, world: "World", size: int = 100):
        """Adds a world below the current world.

        Args:
            world: The world instance to add.
            size: Height of the new world in pixels (default: 100).

        Returns:
            The added world.
        """
        return self.app.worlds_manager.add_world(world, "bottom", size)


    def remove_world(self, world: "World"):
        """Removes a world from the layout and updates the window.

        Args:
            world: The world instance to remove.

        Returns:
            None
        """
        return self.app.worlds_manager.remove_world(world)


    def switch_world(self, new_world: "World", reset: bool = False):
        """Switches to another world

        Args:
            new_world (World): _description_
        """
        self.app.worlds_manager.switch_world(new_world, reset)

    @property
    def window_docking_position(self):
        return self.docking_position

    def _add_to_window(self, app, dock, size: int = 100):
        self.world._app = app
        self.app = app
        self.world._window = self.world._app.window
        self.docking_position = dock
        self.world._image = pygame.Surface((self.world.width, self.world.height))