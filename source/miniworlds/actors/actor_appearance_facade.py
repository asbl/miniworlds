from __future__ import annotations

import sys
from typing import TYPE_CHECKING, List, Tuple, Union, cast

import pygame

import miniworlds.appearances.appearance as appearance
import miniworlds.appearances.costume as costume_mod
import miniworlds.appearances.costumes_manager as costumes_manager
from miniworlds.base.exceptions import MiniworldsError

if TYPE_CHECKING:
    from miniworlds.actors.actor import Actor


class ActorAppearanceFacade:
    def __init__(self, actor: "Actor"):
        self.actor = actor

    @property
    def costume_count(self) -> int:
        return self.actor.costume_manager.length()

    @property
    def is_flipped(self) -> bool:
        return self.actor.costume.is_flipped

    @is_flipped.setter
    def is_flipped(self, value: bool) -> None:
        self.actor.costume.is_flipped = value

    def flip_x(self) -> int:
        return self.actor.position_manager.flip_x()

    def add_costume(
        self, source: Union[None, Tuple, str, List, appearance.Appearance] = None
    ) -> costume_mod.Costume:
        try:
            if source is None or type(source) in [str, tuple] or isinstance(source, appearance.Appearance):
                return self.actor.costume_manager.add_new_appearance(source)
            if isinstance(source, list):
                return cast(
                    costume_mod.Costume,
                    self.actor.costume_manager.add_new_appearance_from_list(source),
                )
            raise MiniworldsError(
                f"Wrong type for appearance. Expected: list, tuple, str or Appearance, got {type(source)}"
            )
        except FileNotFoundError:
            _, exc_value, _ = sys.exc_info()
            raise exc_value.with_traceback(None)

    def add_costumes(self, sources: list) -> costume_mod.Costume:
        return self.actor.costume_manager.add_new_appearances(sources)

    def remove_costume(
        self, source: Union[int, costume_mod.Costume, None] = None
    ):
        if source is None:
            source = self.actor.costume
        return self.actor.costume_manager.remove_appearance(source)

    def switch_costume(
        self, source: Union[int, appearance.Appearance]
    ) -> costume_mod.Costume:
        return self.actor.costume_manager.switch_costume(source)

    def set_costume(
        self, costume: Union[str, tuple, int, appearance.Appearance]
    ) -> None:
        if isinstance(costume, int) or isinstance(costume, appearance.Appearance):
            self.switch_costume(costume)
        elif type(costume) in [str, tuple]:
            new_costume = self.add_costume(costume)
            self.switch_costume(new_costume)

    def reset_costumes(self) -> None:
        self.actor.costume_manager.reset()

    def set_background_color(self, color: tuple) -> None:
        self.set_costume(color)

    def next_costume(self):
        self.actor.costume_manager.next_costume()

    @property
    def costume(self) -> costume_mod.Costume:
        cm = getattr(self.actor, "costume_manager", None)
        if cm is not None:
            return cm.get_actual_appearance()

    @costume.setter
    def costume(self, value) -> None:
        self.actor.costume_manager.appearance = value

    def has_costume(self) -> bool:
        cm = getattr(self.actor, "costume_manager", None)
        if not cm or not cm.has_appearance:
            return False
        return True

    @property
    def costumes(self) -> costumes_manager.CostumesManager:
        return self.actor.costume_manager

    @property
    def orientation(self) -> float:
        return self.actor.costume.orientation

    @orientation.setter
    def orientation(self, value: float) -> None:
        value = self.actor.position_manager.validate_direction(value)
        self.actor.costume.orientation = value

    @property
    def fill_color(self):
        return self.actor.costume.fill_color

    @fill_color.setter
    def fill_color(self, value) -> None:
        self.actor.costume.fill(value)

    def fill(self, value) -> None:
        self.actor.costume.fill(value)

    @property
    def is_filled(self):
        return self.actor.costume.is_filled

    @is_filled.setter
    def is_filled(self, value) -> None:
        self.actor.costume.fill(value)

    @property
    def border_color(self):
        return self.actor.costume.border_color

    @border_color.setter
    def border_color(self, value) -> None:
        self.actor.costume.border_color = value

    @property
    def border(self):
        return self.actor.costume.border

    @border.setter
    def border(self, value) -> None:
        self.actor.costume.border = value

    @property
    def visible(self):
        return self.actor._visible

    @visible.setter
    def visible(self, value) -> None:
        self.actor._visible = value
        self.actor.costume.visibility_changed()

    def hide(self) -> None:
        self.visible = False

    def show(self) -> None:
        self.visible = True

    def new_costume(self):
        return self.actor.world.get_world_connector(self.actor).create_costume()

    @property
    def image(self) -> pygame.Surface:
        return self.actor.costume_manager.image