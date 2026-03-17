from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import miniworlds.actors.actor as actor_mod


class ActorSizeFacade:
    """Internal facade: delegates Actor size, origin, and state-history logic to position_manager."""

    def __init__(self, actor: actor_mod.Actor) -> None:
        self.actor = actor

    # --- size ---

    def get_size(self) -> tuple:
        return self.actor.position_manager.get_size()

    def set_size(self, value: tuple) -> None:
        self.actor.position_manager.set_size(value)

    # --- width ---

    def get_width(self) -> float:
        return self.actor.position_manager.get_size()[0]

    def set_width(self, value) -> None:
        self.actor.position_manager.set_width(value)
        self.actor.on_shape_change()

    def scale_width(self, value) -> None:
        old_width = self.actor.size[0]
        old_height = self.actor.size[1]
        if old_width == 0:
            self.actor.size = (value, old_height)
            return
        scale_factor = value / old_width
        self.actor.size = (value, old_height * scale_factor)

    # --- height ---

    def get_height(self) -> float:
        return self.actor.position_manager.get_size()[1]

    def set_height(self, value) -> None:
        self.actor.position_manager.set_height(value)
        self.actor.on_shape_change()

    def scale_height(self, value) -> None:
        old_width = self.actor.size[0]
        old_height = self.actor.size[1]
        if old_height == 0:
            self.actor.size = (old_width, value)
            return
        scale_factor = value / old_height
        self.actor.size = (old_width * scale_factor, value)

    # --- origin ---

    def get_origin(self) -> str:
        return self.actor.position_manager.origin

    def set_origin(self, value: str) -> None:
        self.actor.position_manager.origin = value

    def switch_origin(self, value: str) -> None:
        self.actor.position_manager.switch_origin(value)

    # --- history ---

    def get_last_center(self):
        return self.actor.position_manager.last_center

    def get_last_direction(self) -> int:
        return self.actor.position_manager.last_direction
