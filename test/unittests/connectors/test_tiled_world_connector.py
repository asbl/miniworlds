import unittest
from types import SimpleNamespace
from unittest.mock import patch

from miniworlds.worlds.manager import world_connector
from miniworlds.worlds.tiled_world.tiled_world_connector import TiledWorldConnector
from miniworlds.worlds.tiled_world.tiled_world_position_manager import TiledWorldPositionManager
from miniworlds.worlds.tiled_world.tiled_world_sensor_manager import TiledWorldSensorManager


class TestTiledWorldConnector(unittest.TestCase):
    def _create_connector(self):
        class DummyActor:
            def __init__(self):
                self.position = (2, 3)
                self._static = False

        actor = DummyActor()
        world = SimpleNamespace(
            static_actors_dict={},
            _dynamic_actors=set(),
            mainloop=SimpleNamespace(reload_costumes_queue=[]),
        )
        return TiledWorldConnector(world, actor), world, actor

    def test_get_sensor_manager_class_returns_tiled_sensor_manager(self):
        self.assertIs(TiledWorldConnector.get_sensor_manager_class(), TiledWorldSensorManager)

    def test_get_position_manager_class_returns_tiled_position_manager(self):
        self.assertIs(TiledWorldConnector.get_position_manager_class(), TiledWorldPositionManager)

    def test_add_static_actor_creates_entry_and_avoids_duplicates(self):
        connector, world, actor = self._create_connector()

        connector.add_static_actor()
        connector.add_static_actor()

        self.assertEqual(world.static_actors_dict[(2, 3)], [actor])
        self.assertEqual(world.mainloop.reload_costumes_queue, [actor])

    def test_remove_static_actor_removes_actor_from_position_bucket(self):
        connector, world, actor = self._create_connector()
        world.static_actors_dict[(2, 3)] = [actor]

        connector.remove_static_actor()

        self.assertEqual(world.static_actors_dict[(2, 3)], [])

    def test_set_static_true_moves_actor_to_static_storage(self):
        connector, world, actor = self._create_connector()
        world._dynamic_actors.add(actor)

        connector.set_static(True)

        self.assertTrue(actor._static)
        self.assertNotIn(actor, world._dynamic_actors)
        self.assertEqual(world.static_actors_dict[(2, 3)], [actor])

    def test_set_static_false_removes_actor_from_static_storage_and_adds_dynamic(self):
        connector, world, actor = self._create_connector()
        actor._static = True
        world.static_actors_dict[(2, 3)] = [actor]

        connector.set_static(False)

        self.assertFalse(actor._static)
        self.assertIn(actor, world._dynamic_actors)
        self.assertEqual(world.static_actors_dict[(2, 3)], [])

    def test_remove_actor_from_world_runs_static_cleanup_before_super_call(self):
        connector, _, _ = self._create_connector()

        with patch.object(connector, "remove_static_actor") as remove_static_actor:
            with patch.object(connector, "remove_dynamic_actor") as remove_dynamic_actor:
                with patch.object(
                    world_connector.WorldConnector,
                    "remove_actor_from_world",
                    return_value={"event": {"handler"}},
                ) as super_remove:
                    result = connector.remove_actor_from_world(kill=True)

        remove_static_actor.assert_called_once_with()
        remove_dynamic_actor.assert_called_once_with()
        super_remove.assert_called_once_with(kill=True)
        self.assertEqual(result, {"event": {"handler"}})