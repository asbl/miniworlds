from typing import Union, TYPE_CHECKING

import miniworlds.appearances.appearances_manager as appearances_manager
import miniworlds.appearances.background as background_mod
import miniworlds.appearances.appearance as appearance_mod

if TYPE_CHECKING:
    from miniworlds.base.world import World


class BackgroundsManager(appearances_manager.AppearancesManager):
    """
    Manages background appearances in a world.

    This manager is typically accessed via the `backgrounds` attribute of a `World` instance.

    Example:
        world.backgrounds.set_background("assets/backgrounds/forest.png")
        bg = world.backgrounds.background
        world.backgrounds.switch_background(2)
    """

    def __init__(self, parent: "World") -> None:
        """
        Initializes the BackgroundsManager.

        Args:
            parent: The world instance that owns this manager.
        """
        super().__init__(parent)
        self.repaint_all: bool = True  # Used to trigger full redraws

    @property
    def background(self) -> "appearance_mod.Appearance":
        """
        Returns the currently active background.

        Example:
            current = world.backgrounds.background
        """
        return self.appearance

    @background.setter
    def background(self, value: "appearance_mod.Appearance") -> None:
        """
        Sets the current background appearance.

        Args:
            value: The new background appearance.

        Example:
            world.backgrounds.background = some_background
        """
        self.appearance = value

    @property
    def world(self) -> "World":
        """
        Shortcut for accessing the owning world.

        Example:
            world = world.backgrounds.world
        """
        return self.parent

    @world.setter
    def world(self, value: "World") -> None:
        self.parent = value

    def get_background_at_index(self, index: int) -> "background_mod.Background":
        """
        Returns the background at a specific index.

        Args:
            index: Index of the background in the manager.

        Returns:
            The background at the given index.

        Example:
            bg = world.backgrounds.get_background_at_index(0)
        """
        return super().get_appearance_at_index(index)

    def add_background(self, source: str) -> "background_mod.Background":
        """
        Adds a new background from a given source path.

        Args:
            source: Path to the background resource.

        Returns:
            The newly added background instance.

        Example:
            world.backgrounds.add_background("assets/bg/mountain.png")
        """
        new_background = self.add_new_appearance(source)
        return new_background

    def set_background(self, source: str) -> "background_mod.Background":
        """
        Sets the background to the one specified by the source.

        Args:
            source: Path to the new background.

        Returns:
            The background that has been set.

        Example:
            world.backgrounds.set_background("assets/bg/sea.png")
        """
        new_background = self.set_new_appearance(source)
        return new_background

    def create_appearance(self) -> "background_mod.Background":
        """
        Creates a new background appearance instance.

        Returns:
            A new Background object linked to the world.

        Example:
            bg = world.backgrounds.create_appearance()
        """
        new_background = background_mod.Background(self.world)
        return new_background

    def switch_appearance(self, source: Union[int, "appearance_mod.Appearance"]) -> "appearance_mod.Appearance":
        """
        Switches to a different background by index or reference.

        Marks all actors in the world as dirty for redrawing.

        Args:
            source: Index of background or background instance.

        Returns:
            The newly activated background.

        Example:
            world.backgrounds.switch_appearance(1)
            world.backgrounds.switch_appearance(other_bg)
        """
        bg = super().switch_appearance(source)

        if hasattr(self.world, "actors"):
            for actor in self.world.actors:
                actor.dirty = 1

        return bg

    switch_background = switch_appearance  # Alias for semantic clarity

    @property
    def backgrounds(self) -> list["background_mod.Background"]:
        """
        Returns the list of all loaded backgrounds.

        Example:
            for bg in world.backgrounds.backgrounds:
                print(bg.name)
        """
        return self.appearances_list
