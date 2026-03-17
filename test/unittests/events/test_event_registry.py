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


class TestEventRegistry(unittest.TestCase):
    """Regression coverage for the internal event registry behavior."""

    def test_collects_inherited_event_methods(self):
        registry = EventRegistry(Mock(), Mock())

        members = registry._get_members_for_instance(ChildHandler())

        self.assertEqual(members, {"act", "on_child_event", "on_parent_event"})

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
        self.assertEqual(registry.iter_sensor_methods(), [("runner", (handler.on_sensor_runner,))])


if __name__ == "__main__":
    unittest.main()