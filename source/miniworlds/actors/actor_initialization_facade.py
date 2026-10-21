from __future__ import annotations

import logging
import warnings
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
        # A world override must only be replaced when it is None: a world with
        # __len__ (e.g. QueueWorld/StackWorld) is falsy while it is still empty.
        self.actor._world = (
            world_override
            if world_override is not None
            else app.App.get_running_world()
        )
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
            logger.debug(
                "Failed to initialize actor %s on world %r",
                self.actor.__class__.__name__,
                self.actor._world,
            )
            raise AttributeError(
                "Actor could not be created on a World - Did you create a world instance before?"
            ) from error
        # Worlds may define __len__ and be falsy while they are still empty,
        # so only None means "no world".
        if self.actor.world is None:
            raise NoWorldError()
        self._warn_if_outside_world(position)

    def _warn_if_outside_world(
        self, position: Optional[Tuple[float, float]]
    ) -> None:
        """Warns in learning mode when an actor starts outside the world.

        The actor is still created (camera worlds may place actors
        off-screen on purpose), but beginners usually mistyped the
        position and wonder why the actor is invisible.
        """
        if not getattr(self.actor.world, "learning_mode", False):
            return
        if not position:
            return
        try:
            x, y = position
            size_x = self.actor.world.world_size_x
            size_y = self.actor.world.world_size_y
        except (TypeError, ValueError, AttributeError):
            return
        if not (0 <= x < size_x and 0 <= y < size_y):
            warnings.warn(
                f"Actor {self.actor.__class__.__name__} was created at "
                f"{position!r}, outside the world "
                f"(size: ({size_x}, {size_y})). "
                f"It is not visible.\n"
                f"Try: Actor((0, 0), world=world)",
                RuntimeWarning,
                stacklevel=4,
            )

    def finalize_sprite_state(self, origin: Optional[str] = None) -> None:
        pygame.sprite.DirtySprite.__init__(self.actor)
        self.actor.speed = 1
        self.actor._dirty = 1
        self.actor.origin = origin if origin else "center"
        self.actor._visible = True