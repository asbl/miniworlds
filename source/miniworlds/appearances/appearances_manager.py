from typing import Union, Tuple, List
from abc import ABC, abstractmethod


import miniworlds
import miniworlds.appearances.appearance as appearance_mod
import miniworlds.appearances.costume as costume
import miniworlds.base.exceptions as miniworlds_exception
from miniworlds.base.exceptions import MiniworldsError
import pygame



class AppearancesManager(ABC):
    """Abstract base class for managing a collection of costume or background appearances.

    Subclasses ``CostumesManager`` (for actors) and ``BackgroundsManager`` (for worlds)
    extend this class with their own factory methods and convenience helpers.

    Typical use via the public API:

    .. code-block:: python

        # Switching between costumes
        actor.switch_costume(1)
        actor.next_costume()

        # Switching between backgrounds
        world.switch_background(1)
        world.next_background()
    """
    def __init__(self, parent):
        self.appearances_list = []
        self.parent = parent
        self.appearance = None
        self._rect = None
        self.is_animated = None
        self.animation_speed = 10
        self.is_upscaled = None
        self.is_scaled = None
        self.is_scaled_to_width = None
        self.is_scaled_to_height = None
        self.has_appearance = False
        self._iter_index = 0
        self._is_display_initialized = False
        # defaults
        self._border = None

    def _init_display(self):
        if not self._is_display_initialized:
            self._is_display_initialized = True
            self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)

    @property
    def image(self) -> pygame.Surface:
        """Image surface of the currently active appearance.

        Returns:
            pygame.Surface: Active appearance image, or a 1x1 fallback surface
            if no appearance has been created yet.
        """
        if self.appearance:
            return self.appearance.image
        else:
            return pygame.Surface((1, 1))

    def _create_appearance_from_source(self, source) -> "appearance_mod.Appearance":
        if isinstance(source, costume.Costume):
            return source
        if source is None:
            appearance = self.create_appearance()
        elif type(source) in [str, pygame.Surface, tuple]:
            appearance = self.create_appearance()
            appearance.add_image(source)
        else:
            raise MiniworldsError(
                f"Wrong type in _create_appearance_from_source got {type(source)}",
            )
        return appearance

    def add_new_appearance(
        self, source: Union[str, pygame.Surface, "costume.Costume", Tuple, None]
    ) -> "appearance_mod.Appearance":
        """Adds a new Appearance (costume or background) to manager.

        called by ``add_costume`` and ``add_background`` in subclasses.
        """
        appearance: "appearance_mod.Appearance" = self._create_appearance_from_source(
            source
        )
        if not self.has_appearance and source:
            self.has_appearance = True
            return self._add_first_appearance(appearance)
        elif not self.has_appearance and not source:
            self.has_appearance = False
            return self._add_default_appearance()
        elif source:
            return self._add_appearance_to_manager(appearance)
        else:
            raise MiniworldsError(
                f"""Error: Got wrong type for appearance. 
                Expected: str, pygame.Surface, Costume, tuple;  got {type(source)}, {source}"""
            )

    def set_new_appearance(
        self, source: Union[str, pygame.Surface, "costume.Costume", Tuple, None]
    ):
        """Replaces the current appearance with a new one.

        If no appearance exists yet, this behaves like ``add_new_appearance``.

        Args:
            source: Image source, color tuple, surface, costume instance, or
                ``None`` for a default appearance.

        Returns:
            The newly active appearance.
        """
        if not self.has_appearance:
            return self.add_new_appearance(source)
        else:
            self.remove_appearance(self.appearance)
            return self.add_new_appearance(source)

    def add_new_appearances(self, sources: List) -> None:
        if type(sources) in [list]:
            for appearance in sources:
                self.add_new_appearance(appearance)
        else:
            raise MiniworldsError(f"Appearances must be list, got {type(sources)}")

    def add_new_appearance_from_list(
        self, sources: List
    ) -> "appearance_mod.Appearance":
        head = sources[0]
        tail = sources[1:]
        appearance = self.add_new_appearance(head)
        for source in tail:
            appearance.add_image(source)
        return appearance

    @abstractmethod
    def create_appearance(self) -> "appearance_mod.Appearance":
        """Returns a new appearance (Background instance or Costume instance)"""
        pass

    def _add_default_appearance(self) -> "appearance_mod.Appearance":
        appearance = self.create_appearance()
        return self._add_first_appearance(appearance)

    def _add_first_appearance(
        self, appearance: "appearance_mod.Appearance"
    ) -> "appearance_mod.Appearance":
        self.appearances_list = []
        self._add_appearance_to_manager(appearance)
        return appearance

    def _add_appearance_to_manager(
        self, appearance: "appearance_mod.Appearance"
    ) -> "appearance_mod.Appearance":
        self.appearance = appearance
        self.appearances_list.append(appearance)
        self._set_appearance_defaults()
        self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)
        return appearance

    def _set_appearance_defaults(self):
        self.appearance._set_defaults(
            is_animated=self.is_animated,
            animation_speed=self.animation_speed,
            is_upscaled=self.is_upscaled,
            is_scaled_to_width=self.is_scaled_to_width,
            is_scaled_to_height=self.is_scaled_to_height,
            is_scaled=self.is_scaled,
            border=self.border,
        )

    def next_appearance(self) -> "appearance_mod.Appearance":
        """Switches to next appearance

        Returns:
            appearance_mod.Appearance: the switched appearance
        """
        index = self.find_appearance(self.appearance)
        if index < self.length() - 1:
            index += 1
        else:
            index = 0
        return self.switch_appearance(index)

    def length(self) -> int:
        """Returns the number of appearances currently managed.

        Returns:
            int: Number of costumes or backgrounds in the manager.
        """
        if self.has_appearance:
            return len(self.appearances_list)
        else:
            return 0

    def __len__(self) -> int:
        return self.length()

    def get_appearance_at_index(
        self, index: int
    ) -> Union["appearance_mod.Appearance", None]:
        if -len(self.appearances_list) <= index < len(self.appearances_list):
            return self.appearances_list[index]
        else:
            return None

    def find_appearance(self, appearance: "appearance_mod.Appearance") -> int:
        """Searches for appearance; returns index of appearance

        Returns:
            int: Index of found appearance; -1 if appearance was not found.
        """
        for index, a_appearance in enumerate(self.appearances_list):
            if a_appearance == appearance:
                return index
        return -1

    def _set_all(self, attribute, value):
        """Sets attribute for all appearance in manager."""
        for appearance in self.appearances_list:
            setattr(appearance, attribute, value)

    def set_border(self, value):
        """Sets the border width for all managed appearances.

        Args:
            value: Border width in pixels.
        """
        self._border = value
        self._set_all("border", value)

    def set_animated(self, value):
        """Enables or disables animation for all managed appearances.

        Args:
            value: ``True`` to animate appearances, otherwise ``False``.
        """
        self.is_animated = value
        self._set_all("is_animated", value)

    def set_animation_speed(self, value):
        """Sets the animation speed for all managed appearances.

        Args:
            value: Number of frames between image changes.
        """
        self.animation_speed = value
        self._set_all("animation_speed", value)

    def set_upscaled(self, value):
        """Sets whether small images may be scaled up.

        Args:
            value: ``True`` to allow upscaling.
        """
        self.is_upscaled = value
        self._set_all("is_upscaled", value)

    def set_scaled_to_width(self, value):
        """Sets whether appearances should scale to the parent width.

        Args:
            value: ``True`` to scale to width.
        """
        self.is_scaled_to_width = value
        self._set_all("is_scaled_to_width", value)

    def set_scaled_to_height(self, value):
        """Sets whether appearances should scale to the parent height.

        Args:
            value: ``True`` to scale to height.
        """
        self.is_scaled_to_height = value
        self._set_all("is_scaled_to_height", value)

    def set_scaled(self, value):
        """Sets whether appearances should scale to the parent size.

        Args:
            value: ``True`` to scale managed appearances.
        """
        self.is_scaled = value
        self._set_all("is_scaled", value)

    def list(self) -> List[appearance_mod.Appearance]:
        """Returns all appearances in manager as list.

        Returns:
            List[appearance_mod.Appearance]: All appearances in manager as list
        """
        return self.appearances_list

    def __str__(self):
        return f"#Appearance-Manager : {str(len(self.appearances_list))} Appearances: {str(self.appearances_list)}, ID: {self.__hash__()}#"

    def _remove_appearance_from_manager(self, appearance: "appearance_mod.Appearance"):
        """Removes an appearance from the manager.

        If the removed appearance is the only one, a default appearance is created
        to keep the actor/world renderable.

        Args:
            appearance: The appearance instance to remove.

        Returns:
            bool: True, if an appearance was removed.
        """
        if not (self.has_appearance and self.length() > 0):
            return False
        if appearance not in self.appearances_list:
            return False

        if self.length() == 1:
            self.appearances_list.remove(appearance)
            self.appearance = None
            self._add_default_appearance()
            self.has_appearance = False
            return True

        was_active = appearance == self.appearance
        self.appearances_list.remove(appearance)
        if was_active:
            self.switch_appearance(self.appearances_list[0])
        return True
        return False

    def remove_appearance(self, source: Union[int, "appearance_mod.Appearance"] = -1):
        """Removes an appearance (costume or background) from manager

        Defaults:
            Removes last costume.

        Args:
            source: The index of the new appearance or the Appearance which should be removed Defaults to -1
            (last costume)
        """
        if isinstance(source, int):
            source = self.get_appearance_at_index(source)
        if source and isinstance(source, appearance_mod.Appearance):
            return self._remove_appearance_from_manager(source)
        else:
            raise MiniworldsError(
                f"Expected type int or Appearance (Costume or Background), got {type(source)}"
            )

    def reset(self):
        """Removes all managed appearances and resets the manager state.

        This is useful when an actor or world should receive a completely new
        set of costumes or backgrounds.
        """
        for appearance in list(self.appearances_list):
            self.remove_appearance(appearance)

    def switch_appearance(
        self, source: Union[int, "appearance_mod.Appearance"]
    ) -> "appearance_mod.Appearance":
        """Switches the active costume or background.

        Args:
            source: Either the appearance index or the appearance instance.

        Returns:
            The newly active appearance.
        """
        if isinstance(source, int):
            if source >= self.length():
                raise miniworlds_exception.CostumeOutOfBoundsError(
                    self.parent, self.length(), source
                )
            new_appearance = self.get_appearance_at_index(source)
        elif isinstance(source, appearance_mod.Appearance) or isinstance(
            source, miniworlds.Appearance
        ):
            new_appearance = source
        else:
            raise MiniworldsError(
                f"Wrong type in switch_appearance, got {type(source)}"
            )
        self.appearance = new_appearance
        self.appearance.image_manager.end_animation(new_appearance)
        self.appearance.set_image(0)
        self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)
        return self.appearance

    def animate(self, speed: int):
        """Starts animating the currently active appearance.

        Args:
            speed: Number of frames between image changes.
        """
        self.appearance.animation_speed = speed
        self.appearance.animate()

    def animate_appearance(self, appearance: "appearance_mod.Appearance", speed: int):
        """Switches to a specific appearance and starts animating it.

        Args:
            appearance: The appearance to animate.
            speed: Number of frames between image changes.
        """
        if appearance is None:
            raise miniworlds_exception.CostumeIsNoneError()
        self.switch_appearance(appearance)
        self.appearance.animation_speed = speed
        self.appearance.animate()

    def self_remove(self) -> None:
        """Implemented in subclasses"""
        pass

    def __iter__(self):
        self._iter_index = 0
        return self

    def __next__(self):
        if self._iter_index < len(self.appearances_list):
            appearance_at_position = self.get_appearance_at_index(self._iter_index)
            self._iter_index += 1
            return appearance_at_position
        else:
            raise StopIteration

    @property
    def orientation(self):
        """Returns the orientation values of all managed appearances."""
        return [appearance.orientation for appearance in self.appearances_list]

    @orientation.setter
    def orientation(self, value):
        for appearance in self.appearances_list:
            appearance.orientation = value

    @property
    def animation_speed(self):
        """Returns the animation speed of the active appearance."""
        return self.appearance.animation_speed

    @animation_speed.setter
    def animation_speed(self, value):
        for appearance in self.appearances_list:
            appearance.animation_speed = value

    @property
    def border(self):
        """Returns the shared border width for managed appearances."""
        return self._border

    @border.setter
    def border(self, value):
        self._border = value
        for appearance in self.appearances_list:
            appearance.border = value

    def get_actual_appearance(self) -> "appearance_mod.Appearance":
        """Returns the currently active appearance.

        If no appearance exists yet, a default one is created first.
        """
        if not self.appearance:
            self._add_default_appearance()
        return self.appearance