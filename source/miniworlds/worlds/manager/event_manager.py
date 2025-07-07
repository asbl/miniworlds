import collections
import inspect
import logging
from collections import defaultdict
from typing import Any, Optional, Callable

import miniworlds.tools.inspection as inspection
import miniworlds.tools.actor_class_inspection as actor_class_inspection
import miniworlds.tools.keys as keys
import miniworlds.worlds.world as world_mod
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.manager.event_definition as event_definition
import miniworlds.worlds.manager.event_handler as event_handler
import miniworlds.worlds.manager.event_registry as event_registry



class EventManager:
    """Processes World Events

    * World Events which can be registered are stored `self.events` variable.
    * World Events which are registered are stored in the dict self.registered_events
    """
    members = set()
    registered_class_events = defaultdict()
    setup = False

    def __init__(self, world):
        self.world = world
        self.definition = event_definition.EventDefinition()
        self.registry = event_registry.EventRegistry(world, self.definition)
        self.registry.setup()
        self.handler = event_handler.EventHandler(world, self.registry)
        self.focus_actor: Optional[actor_mod.Actor] = None
        self._last_focus_actor = None
        self._setup_completed = False

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

    def unregister_instance(self, instance) -> collections.defaultdict:
        return self.registry.unregister_instance(instance)

    def can_register_to_actor(self, method: Callable):
        self.definition.update()
        return method.__name__ in self.definition.actor_class_events_set

    def copy_registered_events(self, key):
        return self.registry.registered_events[key].copy()

    def update(self):
        self.handler.executed_events.clear()

    def setup_world(self):
        if hasattr(self.world, "on_setup") and not self._setup_completed:
            self.world.on_setup()
            self._setup_completed = True