import collections
from collections import defaultdict
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.world as world_mod
import miniworlds.tools.actor_class_inspection as actor_class_inspection
import miniworlds.tools.inspection as inspection
from collections import defaultdict


class EventRegistry:
    def __init__(self, world, event_definition):
        self.registered_events = defaultdict(set)
        self.event_definition = event_definition
        self.world = world

    def setup(self):
        self.register_events_for_world()

    def register_events_for_world(self):
        """Registers all World events."""
        for member in self._get_members_for_instance(self.world):
            if member in self.event_definition.world_class_events_set:
                self.register_event(member, self.world)

    def register_events_for_actor(self, actor):
        """Registers all Actor events."""
        for member in self._get_members_for_instance(actor):
            self.register_event(member, actor)

    def register_event(self, member, instance):
        """Register event to event manager, IF method exists in instance.

        :param member: the method to register
        :param instance: the instance the method should be registered to (e.g. a world or a actor
        """
        method = inspection.Inspection(instance).get_instance_method(member)
        if method:
            for event in self.event_definition.class_events_set:
                "Iterates over all events in class_events_set"
                if member == event:
                    self.registered_events[event].add(method)
                    return event, method
            # for event in self.__class__.class_events_set:
            #    if member.startswith(event):
            #        self.registered_events[event].add(method)
            #        return event, method

    def register_message_event(self, member, instance, message):
        """Register message event to event manager.

        :param member: the method to register
        :param instance: the instance the method should be registered to (e.g. a world or a actor
        """
        member = inspection.Inspection(instance).get_instance_method(member)
        # Default for self.registered_events["message"] is set, so
        # transform this in a defaultdict
        if self.registered_events["message"] == set():
            self.registered_events["message"] = defaultdict(set)
        # Add member to dict
        if member:
            self.registered_events["message"][message].add(member)
        return

    def register_sensor_event(self, member, instance, target):
        """Register message event to event manager.

        :param member: the method to register
        :param instance: the instance the method should be registered to (e.g. a world or a actor
        """
        member = inspection.Inspection(instance).get_instance_method(member)
        # Default for self.registered_events["message"] is set, so
        # transform this in a defaultdict
        if self.registered_events["sensor"] == set():
            self.registered_events["sensor"] = defaultdict(set)
        # Add member to dict
        if member:
            self.registered_events["sensor"][target].add(member)
        return

    def unregister_instance(self, instance) -> collections.defaultdict:
        """unregister an instance (e.g. a Actor) from
        event manager.
        """
        unregister_methods_dict = defaultdict()
        for event, method_set in self.registered_events.items():
            # some events do not contain a set of methods but instead
            # a dictionaray, e.g. {"message_a": set(method_a, method_b, ...]
            methods = set()
            if isinstance(method_set, dict):
                for value in method_set.values():
                    methods.union(value)
                method_set = methods
            for method in method_set:
                if method.__self__ == instance:
                    unregister_methods_dict[event] = method
        for event, method in unregister_methods_dict.items():
            self.registered_events[event].remove(method)
        return unregister_methods_dict

    def _get_members_for_instance(self, instance) -> set:
        """Gets all members of an instance

        Gets members from instance class and instance base classes
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
