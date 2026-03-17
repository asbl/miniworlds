from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Tuple

import pygame

import miniworlds.actors.actor_appearance_facade as actor_appearance_facade
import miniworlds.base.app as app
from miniworlds.base.exceptions import NoWorldError

if TYPE_CHECKING:
    import miniworlds.actors.actor as actor_mod
    import miniworlds.worlds.world as world_mod


logger = logging.getLogger(__name__)


class ActorInitializationFacade:
    """Builds Actor internals in small phases without changing the public constructor."""

    def __init__(self, actor: "actor_mod.Actor"):
        self.actor = actor

    def prepare_core_references(
        self, world_override: Optional["world_mod.World"] = None
    ) -> None:
        self.actor._dirty = 0
        self.actor._world = world_override or app.App.get_running_world()
        self.actor._is_setup_completed = False
        self.actor._sensor_manager = None
        self.actor._position_manager = None
        self.actor._costume_manager = None
        self.actor._appearance_facade = actor_appearance_facade.ActorAppearanceFacade(
            self.actor
        )

    def initialize_runtime_state(self, actor_id: int) -> None:
        self.actor._collision_type = "mask"
        self.actor._layer = 0
        self.actor._inner = 0
        self.actor._size = (0, 0)
        self.actor._static = False
        self.actor.actor_id = actor_id
        self.actor._has_position_manager = False
        self.actor._has_sensor_manager = False
        self.actor._has_costume_manager = False
        self.actor._is_acting = True
        self.actor._is_deleted = False
        self.actor.is_focusable = False
        self.actor.has_focus = False
        self.actor._parent = None

    def initialize_world_managers(
        self, position: Optional[Tuple[float, float]] = (0, 0)
    ) -> None:
        try:
            self.actor.world.get_world_connector(self.actor).init_managers(position)
        except AttributeError as error:
            logger.exception(
                "Failed to initialize actor %s on world %r",
                self.actor.__class__.__name__,
                self.actor._world,
            )
            raise AttributeError(
                "Actor could not be created on a World - Did you created a world instance before?"
            ) from error
        if not self.actor.world:
            raise NoWorldError()

    def finalize_sprite_state(self, origin: Optional[str] = None) -> None:
        pygame.sprite.DirtySprite.__init__(self.actor)
        self.actor.speed = 1
        self.actor._dirty = 1
        self.actor.origin = origin if origin else "center"
        self.actor._visible = True