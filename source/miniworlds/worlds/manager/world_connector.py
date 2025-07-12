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

    def create_costume(self) -> "costume.Costume":
        """
        Creates a new costume instance for the associated actor.

        Returns:
            costume.Costume: A new costume instance, using the actor's custom costume class if defined,
                            otherwise falling back to the default costume class.
        """
        costume_class = self.actor.get_costume_class() or self.get_actor_costume_class()
        return costume_class(self.actor)

    @staticmethod
    def get_actor_costume_class() -> Type["costume.Costume"]:
        """
        Returns the default costume class to be used when an actor does not define a specific one.

        This is implemented in subclasses, if other costume is used.

        Returns:
            Type[costume.Costume]: The default Costume class.
        """
        return costume.Costume

    @staticmethod
    def _get_actor_costume_manager_class() -> Type["costumes_manager.CostumesManager"]:
        """
        Returns the default costume manager class responsible for handling an actor's appearances.

        This is implemented in subclasses, if other CostumesManager is used.

        Returns:
            Type[CostumesManager]: The default CostumesManager class.
        """
        return costumes_manager.CostumesManager

    @staticmethod
    def get_position_manager_class() -> Type["position_manager.Positionmanager"]:
        """
        Returns the default class used to manage the actor's position within the world.

        Returns:
            Type[Positionmanager]: The default Positionmanager class.
        """
        return position_manager.Positionmanager

    @staticmethod
    def get_sensor_manager_class() -> Type["sensor_manager.SensorManager"]:
        """
        Returns the default class used to manage the actor's sensors for detecting other actors or objects.

        Returns:
            Type[SensorManager]: The default SensorManager class.
        """
        return sensor_manager.SensorManager


    def init_managers(self, position: Tuple[float, float] = (0, 0)) -> None:
        """
        Initializes the required manager components (sensor, position, costume) for the actor
        if they are not already initialized.

        Args:
            position (Tuple[float, float], optional): Initial position to assign to the actor.
                                                    Defaults to (0, 0).
        """
        if not self.actor._has_sensor_manager:
            self.init_sensor_manager()
            self.actor._has_sensor_manager = True

        if not self.actor._has_position_manager:
            self.init_position_manager(position)
            self.actor._has_position_manager = True

        if not self.actor._has_costume_manager:
            self.init_costume_manager()
            self.actor._has_costume_manager = True


    def add_to_world(self, position: Tuple[float, float] = (0, 0)) -> "actor_mod.Actor":
        """
        Adds the actor to the world at the given position. Initializes required managers and
        prepares the actor for interaction within the world (e.g., visuals, events, setup logic).

        Args:
            position (Tuple[float, float], optional): Position to place the actor in the world. Defaults to (0, 0).

        Returns:
            actor_mod.Actor: The actor instance that was added to the world.
        """
        if self.world.backgrounds._is_display_initialized:
            self.actor.costume_manager._is_display_initialized = True

        self.actor._world = self.world
        self.init_managers(position)
        self.world.camera._clear_camera_cache()

        if self.actor not in self.world.actors: 
            self.world.actors.add(self.actor)

        self.set_static(self.actor.static)
        self.actor._is_acting = True

        if self.actor.costume:
            self.actor.costume.set_dirty("all", costume.Costume.LOAD_NEW_IMAGE)

        if hasattr(self.actor, "on_setup") and not self.actor._is_setup_completed:
            self.actor.on_setup()
            self.actor._is_setup_completed = True
            self.world._mainloop.reload_costumes_queue.append(self.actor)

        self.world.event_manager.register_events_for_actor(self.actor)
        self.world.on_new_actor(self.actor)

        return self.actor


    def remove_actor_from_world(self, kill: bool = False) -> collections.defaultdict:
        """
        Removes the actor from the world, unregisters it from events, updates visuals,
        and optionally deletes it from memory.

        Args:
            kill (bool): Whether the actor should be permanently deleted. Defaults to False.

        Returns:
            collections.defaultdict: A dictionary of unregistered event methods for potential re-registration.
        """
        self.actor.before_remove()
        self.actor._is_acting = False
        self.world.camera._clear_camera_cache()

        # Mark any colliding actors as dirty (trigger visual update)
        try:
            for colliding_actor in self.actor.sensor_manager.detect_actors():
                colliding_actor.dirty = 1
        except AttributeError:
            pass  # Sensor manager might not be initialized

        # Unregister event methods
        unregistered_methods = self.world.event_manager.unregister_instance(self.actor)

        # Remove from reload queue if present
        if self in self.world._mainloop.reload_costumes_queue:
            self.world.mainloop.reload_costumes_queue.remove(self)

        # Remove from dynamic actors if not static
        if not self.actor._static:
            self.remove_dynamic_actor()

        # Disable managers
        self.actor._has_sensor_manager = False
        self.actor._has_position_manager = False

        # Remove from world
        self.world.actors.remove(self.actor)
        self.world.on_remove_actor(self.actor)

        # Optionally delete the actor completely
        if kill:
            self._delete_removed_actor()

        return unregistered_methods


    def set_world(self, old_world: "world_mod.World", new_world: "world_mod.World", position: Tuple[float, float] = (0, 0)):
        """
        Transfers the actor from the old world to a new world instance,
        preserving registered event methods.

        Args:
            old_world (world_mod.World): The current world from which the actor is removed.
            new_world (world_mod.World): The target world to which the actor is added.
            position (Tuple[float, float], optional): The new position in the target world. Defaults to (0, 0).
        """
        old_connector = old_world.get_world_connector(self.actor)
        unregistered_methods = old_connector.remove_actor_from_world(kill=False)

        # Reassign world reference
        self.world = new_world
        self.add_to_world(position)

        # Re-register previously registered event methods
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
        if self.actor in self.world._dynamic_actors:
            self.world._dynamic_actors.remove(self.actor)

    def add_dynamic_actor(self):
        if self.actor not in self.world._dynamic_actors:
            self.world._dynamic_actors.add(self.actor)
