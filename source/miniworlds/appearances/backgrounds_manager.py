from typing import Union

import miniworlds.appearances.appearances_manager as appearances_manager
import miniworlds.appearances.background as background_mod
import miniworlds.appearances.appearance as appearance_mod


class BackgroundsManager(appearances_manager.AppearancesManager):
    def __init__(self, parent):
        super().__init__(parent)
        self.repaint_all: int = 1

    @property
    def background(self):
        return self.appearance

    @background.setter
    def background(self, value):
        self.appearance = value

    @property
    def world(self):
        return self.parent

    @world.setter
    def world(self, value):
        self.parent = value

    def get_background_at_index(self, index):
        return super().get_appearance_at_index(index)

    def add_background(self, source):
        new_background = self.add_new_appearance(source)
        return new_background

    def set_background(self, source):
        new_background = self.set_new_appearance(source)
        return new_background

    def create_appearance(self) -> "background_mod.Background":
        new_background = background_mod.Background(self.world)
        return new_background

    def switch_appearance(self, source: Union[int, "appearance_mod.Appearance"]) -> "appearance_mod.Appearance":
        bg = super().switch_appearance(source)
        for actor in self.world.actors:
            actor.dirty = 1
        return bg

    switch_background = switch_appearance

    @property
    def backgrounds(self):
        return self.appearances_list

    def get_world(self):
        return self.parent
