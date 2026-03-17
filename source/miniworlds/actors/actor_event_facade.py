from __future__ import annotations

from typing import TYPE_CHECKING

import miniworlds.tools.actor_inspection as actor_inspection

if TYPE_CHECKING:
    import miniworlds.actors.actor as actor_mod
    import miniworlds.worlds.world as world_mod


class ActorEventFacade:
    """Keeps actor-side event registration and messaging helpers in one internal unit."""

    def __init__(self, actor: "actor_mod.Actor"):
        self.actor = actor

    def send_message(self, message: str) -> None:
        self.actor.world.app.event_manager.to_event_queue("message", message)

    def register_sensor(self, *args, **kwargs):
        def decorator(method):
            method_to_bind = kwargs.get("method", method)
            bound_method = actor_inspection.ActorInspection(self.actor).bind_method(
                method_to_bind,
                method_to_bind.__name__,
            )
            self.actor.world.event_manager.register_sensor_event(
                method_to_bind.__name__,
                self.actor,
                args[0],
            )
            return bound_method

        return decorator

    def set_world(self, new_world: "world_mod.World") -> "actor_mod.Actor":
        world_connector = new_world.get_world_connector(self.actor)
        world_connector.set_world(self.actor.world, new_world)
        return self.actor