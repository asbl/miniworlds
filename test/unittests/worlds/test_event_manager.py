import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from miniworlds.worlds.manager.event_manager import EventManager
from miniworlds.worlds.manager.event_subscription import EventSubscription


class TestEventManager(unittest.TestCase):
    """Regression coverage for the EventManager facade over the internal registry."""

    def test_setup_world_calls_on_setup_once(self):
        world = SimpleNamespace(on_setup=Mock())
        manager = EventManager.__new__(EventManager)
        manager.world = world
        manager._setup_completed = False

        EventManager.setup_world(manager)
        EventManager.setup_world(manager)

        world.on_setup.assert_called_once_with()
        self.assertTrue(manager._setup_completed)

    def test_setup_world_skips_missing_handler(self):
        manager = EventManager.__new__(EventManager)
        manager.world = SimpleNamespace()
        manager._setup_completed = False

        EventManager.setup_world(manager)

        self.assertFalse(manager._setup_completed)

    def test_register_event_delegates_to_registry(self):
        registry = Mock()
        manager = EventManager.__new__(EventManager)
        manager.registry = registry

        EventManager.register_event(manager, "on_key_down", object())

        registry.register_event.assert_called_once()

    def test_unregister_instance_returns_registry_result(self):
        registry = Mock(return_value=None)
        subscription = EventSubscription.event("event", Mock())
        registry.unregister_instance.return_value = [subscription]
        manager = EventManager.__new__(EventManager)
        manager.registry = registry

        result = EventManager.unregister_instance(manager, object())

        self.assertEqual(result, [subscription])

    def test_copy_registered_events_returns_independent_copy(self):
        manager = EventManager.__new__(EventManager)
        manager.registry = SimpleNamespace(copy_event_methods=Mock(return_value={"a"}))

        copied = EventManager.copy_registered_events(manager, "on_key")
        copied.add("b")

        manager.registry.copy_event_methods.assert_called_once_with("on_key")
        self.assertEqual(copied, {"a", "b"})

    def test_update_clears_executed_events(self):
        manager = EventManager.__new__(EventManager)
        manager.handler = SimpleNamespace(executed_events={"event"})

        EventManager.update(manager)

        self.assertEqual(manager.handler.executed_events, set())

    def test_get_collision_event_view_is_cached(self):
        manager = EventManager.__new__(EventManager)
        manager.registry = SimpleNamespace(
            copy_event_methods=Mock(return_value={"handler"}),
            iter_sensor_methods=Mock(return_value=[]),
        )
        manager.definition = SimpleNamespace(class_events={"on_detecting": {"on_detecting"}})

        first_view = EventManager.get_collision_event_view(manager)
        second_view = EventManager.get_collision_event_view(manager)

        self.assertIs(first_view, second_view)
        self.assertEqual(first_view.copy_registered_methods("on_detecting"), {"handler"})