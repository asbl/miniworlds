from collections import defaultdict
from typing import Any, Callable, Optional, Union
from collections import defaultdict
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.world as world_mod
import miniworlds.tools.actor_class_inspection as actor_class_inspection
import miniworlds.tools.inspection as inspection


class EventRegistry:
    def __init__(self, world : "world_mod.World", event_definition):
        self.registered_events = defaultdict(set)
        self.event_definition = event_definition
        self.world = world

    def setup(self):
        """Registers initial world events."""
        self.register_events_for_world()

    def register_events_for_world(self):
        """Registers all world-level event methods."""
        for member in self._get_members_for_instance(self.world):
            if member in self.event_definition.world_class_events_set:
                self.register_event(member, self.world)

    def register_events_for_actor(self, actor):
        """Registers all actor-level event methods."""
        for member in self._get_members_for_instance(actor):
            self.register_event(member, actor)

    def register_event(self, member: str, instance: Any) -> Optional[tuple[str, Callable]]:
        """
        Registers a method on an instance for a specific event type.

        Returns:
            Tuple of event name and method, or None if not matched.
        """
        # Retrieve the bound method from the instance using reflection
        method = inspection.Inspection(instance).get_instance_method(member)
        self.event_definition.update()
        if method:
            # Loop through all known event names defined in the event definition
            for defined_event in self.event_definition.class_events_set:
                # Check if the method name matches a known event name exactly
                if member == defined_event:
                    # Register the method under the corresponding event
                    self.registered_events[defined_event].add(method)
                    return defined_event, method

    def register_message_event(self, member, instance, message):
        """
        Registers a method as a handler for a specific message-based event.

        Args:
            member: The name of the method to register (e.g. 'on_message_received')
            instance: The object (e.g. Actor or World) the method belongs to
            message: The message key this method should respond to (e.g. 'hello')
        """
        # Retrieve the bound method from the instance by name
        method = inspection.Inspection(instance).get_instance_method(member)

        if not method:
            return  # Skip if the method doesn't exist or isn't accessible

        # Ensure the 'message' entry in the event registry is a defaultdict(set)
        if not isinstance(self.registered_events["message"], defaultdict):
            self.registered_events["message"] = defaultdict(set)

        # Register the method under the given message key
        self.registered_events["message"][message].add(method)

    def register_sensor_event(self, member: str, instance: Any, target: str) -> None:
        """
        Registers a method as a handler for a sensor-based event tied to a specific target identifier.

        Args:
            member: The name of the method to register (e.g. 'on_sensor_triggered')
            instance: The object (Actor or World) the method belongs to
            target: The target ID (e.g. another object) this sensor is linked to
        """
        # Retrieve the bound method from the instance by method name
        method = inspection.Inspection(instance).get_instance_method(member)
        if not method:
            return  # Exit early if the method doesn't exist or isn't bound

        # Ensure the 'sensor' entry in the event registry is a defaultdict(set)
        if not isinstance(self.registered_events["sensor"], defaultdict):
            self.registered_events["sensor"] = defaultdict(set)

        # Register the method under the given target identifier
        self.registered_events["sensor"][target].add(method)

    def unregister_instance(self, instance: Any) -> dict[str, set[Callable]]:
        """
        Unregisters all event methods associated with the given instance.

        Supports both flat event sets (e.g. {"on_mouse_left": set(...)})
        and nested mappings (e.g.:
                            self.registered_events["message"] = {
                            "hello": {on_message_hello},
                            "goodbye": {on_message_goodbye, log_goodbye},
                            "ping": {respond_to_ping}
                        }


        Args:
            instance: The object (typically an Actor or World) whose methods should be unregistered.

        Returns:
            A dictionary mapping event names to the set of methods that were removed.
        """
        removed_methods: dict[str, set[Callable]] = defaultdict(set)


        for event, method_data in self.registered_events.items():
            # Handle nested event structures like "message" or "sensor"
            if isinstance(method_data, dict):
                for subkey, method_set in method_data.items():
                    for method in list(method_set):
                        if getattr(method, "__self__", None) == instance:
                            method_set.remove(method)
                            removed_methods[event].add(method)

            # Handle flat event sets
            elif isinstance(method_data, set):
                for method in list(method_data):  # Copy to avoid mutation during iteration
                    if getattr(method, "__self__", None) == instance:
                        method_data.remove(method)
                        removed_methods[event].add(method)

        return removed_methods


    def _get_members_for_instance(self, instance) -> set:
        """Gets all members of an instance

        Gets members from instance class and instance base classes
        which are overwritten from Actor or World class.

        Example:
            class MyActor(Actor):
                def on_mouse_left(self): ...
                def on_key_down(self): ...
                def custom_method(self): ...

            _get_members_for_instance(my_actor_instance)

            Returns:
                {"on_mouse_left", "on_key_down"}
                custom_method will be ignored, because it does not start with on_ or act
        """
        if instance.__class__ not in [
            actor_mod.Actor,
            world_mod.World,
        ]:
            members = {
                name
                for name, method in vars(instance.__class__).items()
                if callable(method)
            }
            member_set = set(
                [
                    member
                    for member in members
                    if member.startswith("on_") or member.startswith("act")
                ]
            )
            return member_set.union(
                self._get_members_for_classes(instance.__class__.__bases__)
            )
        else:
            return set()

    def _get_members_for_classes(self, classes) -> set:
        """Get all members for a list of classes

        called recursively in `_get_members for instance` to get all parent class members
        :param classes:
        :return:
        """
        all_members = set()
        for cls in classes:
            if cls not in [
                actor_mod.Actor,
                world_mod.World,
            ]:
                members = {
                    name for name, method in vars(cls).items() if callable(method)
                }
                member_set = set(
                    [
                        member
                        for member in members
                        if member.startswith("on_") or member.startswith("act")
                    ]
                )
                member_set.union(self._get_members_for_classes(cls.__bases__))
                all_members = all_members.union(member_set)
            else:
                all_members = set()
        return all_members
