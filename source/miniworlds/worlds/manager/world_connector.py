import collections
from typing import Optional, Dict, Type, Tuple
import pygame

import miniworlds.appearances.costume as costume
import miniworlds.appearances.costumes_manager as costumes_manager
import miniworlds.worlds.world as world_mod
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.manager.position_manager as position_manager
import miniworlds.worlds.manager.sensor_manager as sensor_manager
from miniworlds.base.exceptions import MissingActorPartsError

class WorldConnector():
    def __init__(self, world: "world_mod.World", actor: "actor_mod.Actor"):
        self.world: "world_mod.World" = world
        self.actor: "actor_mod.Actor" = actor
        self._costume = None
        self._costume_manager = None
        self._sensor_manager: Optional["sensor_manager.SensorManager"] = None
        self._position_manager: Optional["position_manager.Positionmanager"] = None

    def get_costume_class(self) -> "costume.Costume":
        actor_costume_class = self.actor.get_costume_class()
        if not actor_costume_class:
            return self.get_actor_costume_class()(self.actor)
        else:
            return actor_costume_class(self.actor)

    def create_costume(self) -> "costume.Costume":
        costume_class = self.actor.get_costume_class()
        if not costume_class:
            return self.get_costume_class()(self.token)
        else:
            return costume_class(self.actor)

    @staticmethod
    def get_actor_costume_class() -> Type["costume.Costume"]:
        return costume.Costume

    @staticmethod
    def _get_actor_costume_manager_class():
        return costumes_manager.CostumesManager

    @staticmethod
    def get_position_manager_class() -> Type["position_manager.Positionmanager"]:
        return position_manager.Positionmanager

    @staticmethod
    def get_sensor_manager_class() -> Type["sensor_manager.SensorManager"]:
        return sensor_manager.SensorManager

    def init_managers(self, position: Tuple[float,float] = (0, 0)):
        if not self.actor._has_sensor_manager:
            self.init_sensor_manager()
            self.actor._has_sensor_manager = True
        if not self.actor._has_position_manager:
            self.init_position_manager(position)
            self.actor._has_position_manager = True
        if not self.actor._has_costume_manager:
            self.init_costume_manager()
            self.actor._has_costume_manager = True

    def add_to_world(self, position: Tuple[float,float] = (0, 0)) -> "actor_mod.Actor":
        if self.world.is_display_initialized:
            self.actor.is_display_initialized = True
        self.actor._world = self.world
        self.init_managers(position)
        self.world.camera.clear_camera_cache()
        if self.actor not in self.world.actors: #@todo: needed?
            self.world.actors.add(self.actor)
        self.set_static(self.actor.static)
        self.actor._is_acting = True
        # Set world
        if self.actor.costume:
            self.actor.costume.set_dirty("all", costume.Costume.LOAD_NEW_IMAGE)
        if hasattr(self.actor, "on_setup") and not self.actor._was_setup:
            self.actor.on_setup()
            self.actor._was_setup = True
            self.world.reload_costumes_queue.append(self.actor)
        self.world.event_manager.register_events_for_actor(self.actor)
        self.world.on_new_actor(self.actor)
        return self.actor

    def remove_actor_from_world(self, kill = False) -> collections.defaultdict:
        """
        Removes a actor from world

        Returns:unregistered methods from event handler.
        """
        self.actor.before_remove()
        self.actor._is_acting = False
        self.world.camera.clear_camera_cache()
        try:
            for colliding_actor in self.actor.sensor_manager.detect_actors():
                colliding_actor.dirty = 1
        except AttributeError:
            pass
        unregistered_methods = self.world.event_manager.unregister_instance(self.actor)
        if self in self.world.reload_costumes_queue:
            self.world.background.reload_costumes_queue.remove(self)
        if not self.actor._static:
            self.remove_dynamic_actor()
        # Remove sensor manager and position manager (They are not removed)
        self.actor._has_sensor_manager = False
        self.actor._has_position_manager = False
        # Remove actor from world-actors
        self.world.actors.remove(self.actor)
        # Call on remove event
        self.world.on_remove_actor(self.actor)
        if kill:
            self._delete_removed_actor()
        return unregistered_methods


    def set_world(self, old_world, new_world: "world_mod.World"):
        """Switches Actor to new world

        Args:
            new_world (world_mod.World): A new world
        """
        old_connector = old_world.get_world_connector(self.actor)
        unregistered_methods = old_connector.remove_actor_from_world(kill = False)
        self.add_to_world((0,0))
        self.register_event_methods(unregistered_methods)

    def register_event_methods(self, method_dict: Dict[str, callable]):
        if method_dict:
            for event, method_data in method_dict.items():
                if isinstance(method_data, set):
                    for method in method_data:
                        self.actor.register(method)
                else:
                    self.actor.register(method_data)

    def init_sensor_manager(self):
        self.actor._sensor_manager = self.get_sensor_manager_class()(self.actor, self.world)
        return self.actor._sensor_manager

    def init_position_manager(self, position=(0, 0)):
        self.actor._position_manager = self.get_position_manager_class()(self.actor, self.world, position)
        self.actor._position_manager.position = position
        return self.actor._position_manager

    def init_costume_manager(self):
        self.actor._costume_manager = self._get_actor_costume_manager_class()(self.actor)
        self.actor._costume_manager._add_default_appearance()
        return self.actor._costume_manager

    def _delete_removed_actor(self):
        if not self.actor._is_deleted:
            self.actor._is_deleted = True
            self.actor._costume_manager.remove_from_world()
            self.actor.kill()
            del self.actor

    def set_static(self, value):
        self.actor._static = value
        if self.actor._static:
            self.remove_dynamic_actor()
        else:
            self.add_dynamic_actor()

    def remove_dynamic_actor(self):
        if self.actor in self.world.dynamic_actors:
            self.world.dynamic_actors.remove(self.actor)

    def add_dynamic_actor(self):
        if self.actor not in self.world.dynamic_actors:
            self.world.dynamic_actors.add(self.actor)
