import unittest
from unittest.mock import Mock

from miniworlds.worlds.manager.event_registry import EventRegistry
from miniworlds.worlds.manager.event_subscription import EventSubscription


class ParentHandler:
    """Base fixture class used to verify inherited event discovery."""

    def on_parent_event(self):
        return None

    def helper(self):
        return None


class ChildHandler(ParentHandler):
    """Derived fixture class that contributes additional event methods."""

    def on_child_event(self):
        return None

    def act(self):
        return None


ActorRoot = type(
    "Actor",
    (),
    {
        "__module__": "miniworlds.actors.actor",
        "on_base_actor_event": lambda self: None,
        "act_base": lambda self: None,
    },
)


class StudentActor(ActorRoot):
    def on_student_event(self):
        return None

    def act(self):
        return None


WorldRoot = type(
    "World",
    (),
    {
        "__module__": "miniworlds.worlds.world",
        "on_base_world_event": lambda self: None,
        "act_base": lambda self: None,
    },
)


class StudentWorld(WorldRoot):
    def on_world_started(self):
        return None


class TestEventRegistry(unittest.TestCase):
    """Regression coverage for the internal event registry behavior."""

    def test_collects_inherited_event_methods(self):
        registry = EventRegistry(Mock(), Mock())

        members = registry._get_members_for_instance(ChildHandler())

        self.assertEqual(members, {"act", "on_child_event", "on_parent_event"})

    def test_actor_root_methods_are_not_registered_as_student_events(self):
        registry = EventRegistry(Mock(), Mock())

        members = registry._get_members_for_instance(StudentActor())

        self.assertEqual(members, {"act", "on_student_event"})

    def test_world_root_methods_are_not_registered_as_world_events(self):
        registry = EventRegistry(Mock(), Mock())

        members = registry._get_members_for_instance(StudentWorld())

        self.assertEqual(members, {"on_world_started"})

    def test_registers_middle_mouse_up_event(self):
        class MiddleMouseHandler:
            def on_mouse_middle_up(self, position):
                return position

        definition = Mock()
        definition.class_events_set = {"on_mouse_middle_up"}
        definition.update = Mock()
        registry = EventRegistry(Mock(), definition)
        handler = MiddleMouseHandler()

        registered = registry.register_event("on_mouse_middle_up", handler)

        self.assertEqual(registered[0], "on_mouse_middle_up")
        self.assertIn(handler.on_mouse_middle_up, registry.copy_event_methods("on_mouse_middle_up"))

    def test_registers_not_on_world_alias_event(self):
        class BoundaryHandler:
            def on_detecting_not_on_world(self):
                return None

        definition = Mock()
        definition.class_events_set = {"on_detecting_not_on_world"}
        definition.update = Mock()
        registry = EventRegistry(Mock(), definition)
        handler = BoundaryHandler()

        registered = registry.register_event("on_detecting_not_on_world", handler)

        self.assertEqual(registered[0], "on_detecting_not_on_world")
        self.assertIn(
            handler.on_detecting_not_on_world,
            registry.copy_event_methods("on_detecting_not_on_world"),
        )

    def test_reuses_event_member_discovery_for_instances_of_same_class(self):
        registry = EventRegistry(Mock(), Mock())
        handler = ChildHandler()

        first = registry._get_members_for_instance(handler)
        ChildHandler.on_late_event = lambda self: None
        try:
            second = registry._get_members_for_instance(ChildHandler())
        finally:
            del ChildHandler.on_late_event

        self.assertEqual(second, first)
        self.assertNotIn("on_late_event", second)

    def test_registering_actor_updates_definition_once_per_actor_class(self):
        definition = Mock()
        definition.class_events_set = {"act", "on_child_event", "on_parent_event"}
        registry = EventRegistry(Mock(), definition)
        handler = ChildHandler()

        registry.register_events_for_actor(handler)
        registry.register_events_for_actor(ChildHandler())

        definition.update.assert_called_once_with()
        registered_methods = registry.copy_event_methods("act")
        self.assertIn(handler.act, registered_methods)
        self.assertEqual(len(registered_methods), 2)

    def test_unregister_instance_preserves_message_and_sensor_metadata(self):
        class CompositeHandler:
            def on_message_boost(self, payload):
                return payload

            def on_sensor_runner(self, target):
                return target

        definition = Mock()
        definition.class_events_set = set()
        definition.update = Mock()
        registry = EventRegistry(Mock(), definition)
        handler = CompositeHandler()

        registry.register_message_event("on_message_boost", handler, "boost")
        registry.register_sensor_event("on_sensor_runner", handler, "runner")

        subscriptions = registry.unregister_instance(handler)

        self.assertIn(EventSubscription.message("boost", handler.on_message_boost), subscriptions)
        self.assertIn(EventSubscription.sensor("runner", handler.on_sensor_runner), subscriptions)

        registry.restore_subscriptions(subscriptions)

        self.assertEqual(registry.copy_message_methods("boost"), {handler.on_message_boost})
        self.assertEqual(registry.iter_sensor_methods(), (("runner", (handler.on_sensor_runner,)),))

    def test_has_registered_event_checks_all_registry_types(self):
        definition = Mock()
        definition.class_events_set = {"on_child_event"}
        definition.update = Mock()
        registry = EventRegistry(Mock(), definition)
        handler = ChildHandler()

        registry.register_event("on_child_event", handler)
        registry.register_message_event("on_child_event", handler, "saved")
        registry.register_sensor_event("on_child_event", handler, "runner")

        self.assertTrue(registry.has_registered_event("on_child_event"))
        self.assertTrue(registry.has_registered_event("message"))
        self.assertTrue(registry.has_registered_event("sensor"))
        self.assertFalse(registry.has_registered_event("on_missing"))

    def test_iter_event_methods_cache_invalidates_when_registry_changes(self):
        definition = Mock()
        definition.class_events_set = {"act", "on_child_event"}
        definition.update = Mock()
        registry = EventRegistry(Mock(), definition)
        first = ChildHandler()
        second = ChildHandler()

        registry.register_event("act", first)
        first_snapshot = registry.iter_event_methods("act")
        second_snapshot = registry.iter_event_methods("act")

        self.assertIs(first_snapshot, second_snapshot)
        self.assertEqual(first_snapshot, (first.act,))

        registry.register_event("act", second)

        updated_snapshot = registry.iter_event_methods("act")
        self.assertIsNot(updated_snapshot, first_snapshot)
        self.assertCountEqual(updated_snapshot, (first.act, second.act))

    def test_iter_message_and_sensor_methods_cache_invalidates(self):
        class CompositeHandler:
            def on_message_saved(self, payload):
                return payload

            def on_sensor_runner(self, target):
                return target

        definition = Mock()
        definition.class_events_set = set()
        definition.update = Mock()
        registry = EventRegistry(Mock(), definition)
        handler = CompositeHandler()

        registry.register_message_event("on_message_saved", handler, "saved")
        registry.register_sensor_event("on_sensor_runner", handler, "runner")
        message_snapshot = registry.iter_message_methods("saved")
        sensor_snapshot = registry.iter_sensor_methods()

        registry.unregister_instance(handler)

        self.assertIsNot(registry.iter_message_methods("saved"), message_snapshot)
        self.assertIsNot(registry.iter_sensor_methods(), sensor_snapshot)
        self.assertEqual(registry.iter_message_methods("saved"), ())
        self.assertEqual(registry.iter_sensor_methods(), ())


if __name__ == "__main__":
    unittest.main()
