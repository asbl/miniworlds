from collections import defaultdict
from collections.abc import Iterable
from typing import Any, Callable, Optional
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.world as world_mod
import miniworlds.tools.inspection as inspection
from miniworlds.worlds.manager.event_subscription import EventSubscription


class EventRegistry:
    """Stores event, message, and sensor handlers behind a single internal registry API."""

    def __init__(self, world : "world_mod.World", event_definition):
        self.event_definition = event_definition
        self.world = world
        self.change_counter = 0
        self._event_handlers: defaultdict[str, set[Callable]] = defaultdict(set)
        self._message_handlers: defaultdict[str, set[Callable]] = defaultdict(set)
        self._sensor_handlers: defaultdict[str, set[Callable]] = defaultdict(set)

    def _mark_changed(self) -> None:
        self.change_counter += 1

    @property
    def registered_events(self):
        events = defaultdict(set)
        for event_name, methods in self._event_handlers.items():
            events[event_name] = methods.copy()
        if self._message_handlers:
            events["message"] = defaultdict(
                set,
                {message: methods.copy() for message, methods in self._message_handlers.items()},
            )
        if self._sensor_handlers:
            events["sensor"] = defaultdict(
                set,
                {target: methods.copy() for target, methods in self._sensor_handlers.items()},
            )
        return events

    def registered_event_names(self) -> set[str]:
        names = set(self._event_handlers.keys())
        if self._message_handlers:
            names.add("message")
        if self._sensor_handlers:
            names.add("sensor")
        return names

    def copy_event_methods(self, event_name: str) -> set[Callable]:
        return self._event_handlers.get(event_name, set()).copy()

    def copy_message_methods(self, message: str) -> set[Callable]:
        return self._message_handlers.get(message, set()).copy()

    def copy_generic_message_methods(self) -> set[Callable]:
        return self.copy_event_methods("on_message")

    def iter_sensor_methods(self) -> list[tuple[str, tuple[Callable, ...]]]:
        return [
            (target, tuple(methods.copy()))
            for target, methods in self._sensor_handlers.items()
        ]

    def restore_subscriptions(
        self, subscriptions: Iterable[EventSubscription]
    ) -> None:
        for subscription in subscriptions:
            self._restore_subscription(subscription)

    def _add_event_method(self, event_name: str, method: Callable) -> None:
        previous_len = len(self._event_handlers[event_name])
        self._event_handlers[event_name].add(method)
        if len(self._event_handlers[event_name]) != previous_len:
            self._mark_changed()

    def _add_message_method(self, message: str, method: Callable) -> None:
        previous_len = len(self._message_handlers[message])
        self._message_handlers[message].add(method)
        if len(self._message_handlers[message]) != previous_len:
            self._mark_changed()

    def _add_sensor_method(self, target: str, method: Callable) -> None:
        previous_len = len(self._sensor_handlers[target])
        self._sensor_handlers[target].add(method)
        if len(self._sensor_handlers[target]) != previous_len:
            self._mark_changed()

    def _restore_subscription(self, subscription: EventSubscription) -> None:
        if subscription.kind == "event":
            self._add_event_method(subscription.event_name, subscription.method)
        elif subscription.kind == "message" and subscription.route_key is not None:
            self._add_message_method(subscription.route_key, subscription.method)
        elif subscription.kind == "sensor" and subscription.route_key is not None:
            self._add_sensor_method(subscription.route_key, subscription.method)

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
        if method and member in self.event_definition.class_events_set:
            self._add_event_method(member, method)
            return member, method

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

        self._add_message_method(message, method)

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

        self._add_sensor_method(target, method)

    def unregister_instance(self, instance: Any) -> list[EventSubscription]:
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
            A list of structured event subscriptions that can later be restored.
        """
        removed_methods: list[EventSubscription] = []
        registry_changed = False

        for event_name, method_set in self._event_handlers.items():
            for method in list(method_set):
                if getattr(method, "__self__", None) == instance:
                    method_set.remove(method)
                    removed_methods.append(EventSubscription.event(event_name, method))
                    registry_changed = True

        for message, method_set in self._message_handlers.items():
            for method in list(method_set):
                if getattr(method, "__self__", None) == instance:
                    method_set.remove(method)
                    removed_methods.append(EventSubscription.message(message, method))
                    registry_changed = True

        for target, method_set in self._sensor_handlers.items():
            for method in list(method_set):
                if getattr(method, "__self__", None) == instance:
                    method_set.remove(method)
                    removed_methods.append(EventSubscription.sensor(target, method))
                    registry_changed = True

        if registry_changed:
            self._mark_changed()

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
                member_set = member_set.union(self._get_members_for_classes(cls.__bases__))
                all_members = all_members.union(member_set)
            else:
                continue
        return all_members
