from typing import Any, Optional, Callable

import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.manager.event_definition as event_definition
import miniworlds.worlds.manager.event_handler as event_handler
import miniworlds.worlds.manager.event_registry as event_registry
import miniworlds.worlds.manager.collision_event_view as collision_event_view
from miniworlds.worlds.manager.event_subscription import EventSubscription



class EventManager:
    """Coordinates event registration, dispatch, and collision-event views for one world."""

    def __init__(self, world):
        self.world = world
        self.definition = event_definition.EventDefinition()
        self.registry = event_registry.EventRegistry(world, self.definition)
        self.registry.setup()
        self.handler = event_handler.EventHandler(world, self.registry)
        self.focus_actor: Optional[actor_mod.Actor] = None
        self._last_focus_actor = None
        self._setup_completed = False
        self._collision_event_view = collision_event_view.CollisionEventView(self)

    def act_all(self):
        self.handler.act_all()

    def register_event(self, member, instance):
        self.registry.register_event(member, instance)

    def register_message_event(self, member, instance, message):
        self.registry.register_message_event(member, instance, message)

    def register_sensor_event(self, member, instance, message):
        self.registry.register_sensor_event(member, instance, message)

    def register_events_for_actor(self, actor):
        self.registry.register_events_for_actor(actor)

    def unregister_instance(self, instance) -> list[EventSubscription]:
        return self.registry.unregister_instance(instance)

    def restore_subscriptions(self, subscriptions: list[EventSubscription]) -> None:
        self.registry.restore_subscriptions(subscriptions)

    def can_register_to_actor(self, method: Callable):
        self.definition.update()
        return method.__name__ in self.definition.actor_class_events_set

    def copy_registered_events(self, key):
        return self.registry.copy_event_methods(key)

    @property
    def class_events_set(self):
        return self.definition.class_events_set

    @property
    def registered_events(self):
        return self.registry.registered_event_names()

    def get_collision_event_view(self) -> collision_event_view.CollisionEventView:
        view = getattr(self, "_collision_event_view", None)
        if view is None:
            view = collision_event_view.CollisionEventView(self)
            self._collision_event_view = view
        return view

    def update(self):
        self.handler.executed_events.clear()

    def setup_world(self):
        if hasattr(self.world, "on_setup") and not self._setup_completed:
            self.world.on_setup()
            self._setup_completed = True