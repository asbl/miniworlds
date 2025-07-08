from typing import Union, List, cast, TYPE_CHECKING

import miniworlds.appearances.appearance as appearance_mod
import miniworlds.appearances.appearances_manager as appearances_manager
import miniworlds.appearances.costume as costume_mod

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod
    import miniworlds.actors.actor as actor_mod

class CostumesManager(appearances_manager.AppearancesManager):
    def __init__(self, parent):
        super().__init__(parent)
        self.is_rotatable = None

    @property
    def actor(self) -> "actor_mod.Actor":
        return self.parent

    @actor.setter
    def actor(self, value: "actor_mod.Actor"):
        self.parent = value

    def get_costume_at_index(self, index):
        return super().get_appearance_at_index(index)

    def add_new_appearance(
        self, source: Union[str, List[str], "appearance_mod.Appearance"] = None
    ) -> "costume_mod.Costume":
        """
        Adds a new costume to actor.
        The costume can be switched with self.switch_costume(index)

        Args:
            source: Path to the first image of new costume

        Returns:
            The new costume.

        """
        new_costume = super().add_new_appearance(source)
        self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)
        return cast("costume_mod.Costume", new_costume)

    def create_appearance(self) -> "costume_mod.Costume":
        """Creates a new costume

        Returns:
            costume_mod-Costume: the new created costume.
        """
        world_connector = self.actor.world.get_world_connector(self.actor)
        new_costume = world_connector.create_costume()
        return new_costume

    @property
    def costumes(self):
        return self.appearances_list

    def switch_costume(self, source):
        self.switch_appearance(source)

    def animate_costume(self, costume, speed):
        super().animate_appearance(costume, speed)

    @property
    def has_costume(self):
        return self.has_appearance

    @has_costume.setter
    def has_costume(self, value):
        self.has_appearance = value

    def next_costume(self) -> "costume_mod.Costume":
        return cast("costume_mod.Costume", self.next_appearance())

    def _add_appearance_to_manager(self, appearance):
        return super()._add_appearance_to_manager(appearance)

    def remove_from_world(self):
        for costume in self.appearances_list:
            costume.parent = None
            costume.actor = None
            del costume

    @property
    def is_flipped(self):
        return self.appearance._is_flipped

    @is_flipped.setter
    def is_flipped(self, value):
        for costume in self.appearances_list:
            costume.is_flipped = value

    def set_rotatable(self, value):
        self.is_rotatable = value
        self._set_all("is_rotatable", value)

    def _set_appearance_defaults(self):
        self.appearance._set_defaults(
            rotatable=self.is_rotatable,
            is_animated=self.is_animated,
            animation_speed=self.animation_speed,
            is_upscaled=self.is_upscaled,
            is_scaled_to_width=self.is_scaled_to_width,
            is_scaled_to_height=self.is_scaled_to_height,
            is_scaled=self.is_scaled,
            border=self.border,
            is_flipped=self.is_flipped
        )

