import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from miniworlds.appearances.costume import Costume
from miniworlds.worlds.manager.world_connector import WorldConnector
from miniworlds.worlds.manager.event_subscription import EventSubscription


class DummyActor:
    """Minimal actor double for WorldConnector lifecycle tests."""

    def __init__(self, with_setup: bool = True):
        self.static = False
        self._world = None
        self._is_acting = False
        self._is_setup_completed = False
        self.is_blocking = True
        self.costume_manager = SimpleNamespace(_is_display_initialized=False)
        self.costume = MagicMock()
        if with_setup:
            self.on_setup = MagicMock()


class TestWorldConnector(unittest.TestCase):
    """Regression coverage for actor attach, detach, and world-transfer flows."""

    def test_add_to_world_initializes_actor_and_runs_setup_once(self):
        actor = DummyActor()

        world = SimpleNamespace(
            backgrounds=SimpleNamespace(_is_display_initialized=True),
            camera=SimpleNamespace(_clear_camera_cache=MagicMock()),
            actors=set(),
            _mainloop=SimpleNamespace(reload_costumes_queue=[]),
            _blocking_actors=set(),
            event_manager=SimpleNamespace(register_events_for_actor=MagicMock()),
            on_new_actor=MagicMock(),
        )

        connector = WorldConnector(world, actor)
        connector.init_managers = MagicMock()
        connector.set_static = MagicMock()

        result = connector.add_to_world((3, 4))

        self.assertIs(result, actor)
        self.assertIs(actor._world, world)
        self.assertTrue(actor.costume_manager._is_display_initialized)
        connector.init_managers.assert_called_once_with((3, 4))
        world.camera._clear_camera_cache.assert_called_once_with()
        self.assertIn(actor, world.actors)
        connector.set_static.assert_called_once_with(False)
        self.assertTrue(actor._is_acting)
        actor.costume.set_dirty.assert_called_once_with("all", Costume.LOAD_NEW_IMAGE)
        actor.on_setup.assert_called_once_with()
        self.assertTrue(actor._is_setup_completed)
        self.assertEqual(world._mainloop.reload_costumes_queue, [actor])
        self.assertIn(actor, world._blocking_actors)
        world.event_manager.register_events_for_actor.assert_called_once_with(actor)
        world.on_new_actor.assert_called_once_with(actor)

    def test_add_to_world_skips_completed_setup_and_blocking_registration(self):
        actor = DummyActor()
        actor._is_setup_completed = True
        actor.is_blocking = False

        world = SimpleNamespace(
            backgrounds=SimpleNamespace(_is_display_initialized=False),
            camera=SimpleNamespace(_clear_camera_cache=MagicMock()),
            actors=set(),
            _mainloop=SimpleNamespace(reload_costumes_queue=[]),
            _blocking_actors=set(),
            event_manager=SimpleNamespace(register_events_for_actor=MagicMock()),
            on_new_actor=MagicMock(),
        )

        connector = WorldConnector(world, actor)
        connector.init_managers = MagicMock()
        connector.set_static = MagicMock()

        connector.add_to_world((1, 2))

        actor.on_setup.assert_not_called()
        self.assertEqual(world._mainloop.reload_costumes_queue, [])
        self.assertNotIn(actor, world._blocking_actors)

    def test_remove_actor_clears_reload_queue(self):
        actor = MagicMock()
        actor.before_remove = MagicMock()
        actor.sensor_manager.detect_actors.return_value = []
        actor._static = False
        actor._has_sensor_manager = True
        actor._has_position_manager = True

        world = MagicMock()
        world.camera._clear_camera_cache = MagicMock()
        world.event_manager.unregister_instance.return_value = []
        world._mainloop.reload_costumes_queue = [actor]
        world._dynamic_actors = {actor}
        world.actors.remove = MagicMock()
        world.on_remove_actor = MagicMock()

        connector = WorldConnector(world, actor)
        connector.remove_actor_from_world()

        self.assertNotIn(actor, world._mainloop.reload_costumes_queue)
        self.assertNotIn(actor, world._dynamic_actors)
        self.assertFalse(actor._has_sensor_manager)
        self.assertFalse(actor._has_position_manager)
        world.event_manager.unregister_instance.assert_called_once_with(actor)
        world.actors.remove.assert_called_once_with(actor)
        world.on_remove_actor.assert_called_once_with(actor)

    def test_remove_actor_with_kill_marks_colliding_actors_and_discards_blocking(self):
        actor = MagicMock()
        actor.before_remove = MagicMock()
        colliding_actor = MagicMock()
        actor.sensor_manager.detect_actors.return_value = [colliding_actor]
        actor._static = False
        actor._has_sensor_manager = True
        actor._has_position_manager = True

        world = MagicMock()
        world.camera._clear_camera_cache = MagicMock()
        unregistered_methods = []
        world.event_manager.unregister_instance.return_value = unregistered_methods
        world._mainloop.reload_costumes_queue = []
        world._dynamic_actors = {actor}
        world._blocking_actors = {actor}
        world.actors.remove = MagicMock()
        world.on_remove_actor = MagicMock()

        connector = WorldConnector(world, actor)
        connector._delete_removed_actor = MagicMock()

        result = connector.remove_actor_from_world(kill=True)

        self.assertEqual(colliding_actor.dirty, 1)
        self.assertNotIn(actor, world._blocking_actors)
        connector._delete_removed_actor.assert_called_once_with()
        self.assertIs(result, unregistered_methods)

    def test_set_world_moves_actor_and_re_registers_methods(self):
        actor = MagicMock()
        old_world = MagicMock()
        new_world = MagicMock()
        old_connector = MagicMock()
        unregistered_methods = [EventSubscription.event("act", MagicMock())]
        old_connector.remove_actor_from_world.return_value = unregistered_methods
        old_world.get_world_connector.return_value = old_connector

        connector = WorldConnector(new_world, actor)
        connector.add_to_world = MagicMock()
        connector.restore_event_subscriptions = MagicMock()

        connector.set_world(old_world, new_world, position=(3, 4))

        old_world.get_world_connector.assert_called_once_with(actor)
        old_connector.remove_actor_from_world.assert_called_once_with(kill=False)
        self.assertIs(connector.world, new_world)
        connector.add_to_world.assert_called_once_with((3, 4))
        connector.restore_event_subscriptions.assert_called_once_with(unregistered_methods)

    def test_restore_event_subscriptions_delegates_to_event_manager(self):
        actor = MagicMock()
        world = MagicMock()
        connector = WorldConnector(world, actor)
        subscriptions = [
            EventSubscription.message("boost", MagicMock()),
            EventSubscription.sensor("runner", MagicMock()),
        ]

        connector.restore_event_subscriptions(subscriptions)

        world.event_manager.restore_subscriptions.assert_called_once_with(subscriptions)


if __name__ == "__main__":
    unittest.main()