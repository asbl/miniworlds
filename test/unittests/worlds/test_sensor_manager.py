import unittest
from unittest.mock import patch

from miniworlds import Actor, World
from miniworlds.base.app import App
from miniworlds.base.exceptions import MissingPositionManager, WrongFilterType


class Runner(Actor):
    pass


class FastRunner(Runner):
    pass


class Hunter(Actor):
    pass


class Wall(Actor):
    pass


class TestSensorManager(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(80, 80)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def _create_actor(self, actor_cls, position=(20, 20)):
        actor = actor_cls(position, world=self.world)
        actor.size = (24, 24)
        actor.collision_type = "rect"
        return actor

    def test_detect_all_by_classname_includes_subclasses(self):
        hunter = self._create_actor(Hunter)
        runner = self._create_actor(Runner)
        fast_runner = self._create_actor(FastRunner)
        wall = self._create_actor(Wall)

        detected = hunter.detect_all("runner")

        self.assertIn(runner, detected)
        self.assertIn(fast_runner, detected)
        self.assertNotIn(wall, detected)
        self.assertNotIn(hunter, detected)

    def test_world_tracks_blocking_actors_when_flag_changes(self):
        wall = self._create_actor(Wall)

        self.assertNotIn(wall, self.world._blocking_actors)

        wall.is_blocking = True
        self.assertIn(wall, self.world._blocking_actors)

        wall.is_blocking = False
        self.assertNotIn(wall, self.world._blocking_actors)

    def test_detect_blocking_actor_at_destination_uses_blocking_index(self):
        hunter = self._create_actor(Hunter, position=(20, 20))
        hunter.direction = 90
        wall = self._create_actor(Wall, position=(40, 20))
        wall.is_blocking = True

        detected = hunter.sensor_manager.detect_blocking_actor_at_destination((40, 20))

        self.assertIs(detected, wall)

    def test_removed_blocking_actor_is_removed_from_world_index(self):
        wall = self._create_actor(Wall)
        wall.is_blocking = True

        wall.remove()

        self.assertNotIn(wall, self.world._blocking_actors)

    def test_world_blocking_registry_version_updates_on_flag_changes(self):
        wall = self._create_actor(Wall)
        initial_version = self.world._blocking_registry_version

        wall.is_blocking = True
        after_enable = self.world._blocking_registry_version

        wall.is_blocking = False
        after_disable = self.world._blocking_registry_version

        self.assertGreater(after_enable, initial_version)
        self.assertGreater(after_disable, after_enable)

    def test_static_blocking_cache_is_invalidated_when_actor_moves(self):
        hunter = self._create_actor(Hunter, position=(20, 20))
        wall = self._create_actor(Wall, position=(40, 20))
        wall.is_blocking = True
        wall.static = True

        self.assertIs(
            hunter.sensor_manager.get_blocking_actor_at_position((40, 20)),
            wall,
        )

        wall.position = (60, 20)

        self.assertIsNone(hunter.sensor_manager.get_blocking_actor_at_position((40, 20)))
        self.assertIs(
            hunter.sensor_manager.get_blocking_actor_at_position((60, 20)),
            wall,
        )

    def test_detect_actors_with_invalid_filter_raises_wrong_filter_type(self):
        hunter = self._create_actor(Hunter)

        with self.assertRaises(WrongFilterType):
            hunter.sensor_manager.detect_actors(42)

    def test_prefilter_detectable_actors_applies_instance_filter(self):
        hunter = self._create_actor(Hunter)
        runner = self._create_actor(Runner)
        wall = self._create_actor(Wall, position=(50, 20))

        filtered, applied = hunter.sensor_manager._prefilter_detectable_actors(
            [hunter, runner, wall],
            runner,
        )

        self.assertTrue(applied)
        self.assertEqual(filtered, [runner])

    def test_prefilter_detectable_actors_keeps_visible_actors_for_unknown_classname(self):
        hunter = self._create_actor(Hunter)
        runner = self._create_actor(Runner)

        visible_actors = [hunter, runner]
        filtered, applied = hunter.sensor_manager._prefilter_detectable_actors(
            visible_actors,
            "ghost",
        )

        self.assertFalse(applied)
        self.assertEqual(filtered, visible_actors)

    def test_prefilter_detectable_actors_resolves_classname_once(self):
        hunter = self._create_actor(Hunter)
        runner = self._create_actor(Runner)

        with patch.object(
            hunter.sensor_manager,
            "_resolve_actor_type_by_name",
            wraps=hunter.sensor_manager._resolve_actor_type_by_name,
        ) as resolve_actor_type:
            filtered, applied = hunter.sensor_manager._prefilter_detectable_actors(
                [hunter, runner],
                "runner",
            )

        self.assertTrue(applied)
        self.assertEqual(filtered, [runner])
        resolve_actor_type.assert_called_once_with("runner")

    def test_detect_actors_applies_actor_list_filter(self):
        hunter = self._create_actor(Hunter)
        runner = self._create_actor(Runner)
        fast_runner = self._create_actor(FastRunner)
        wall = self._create_actor(Wall)

        detected = hunter.sensor_manager.detect_actors([runner, fast_runner])

        self.assertCountEqual(detected, [runner, fast_runner])
        self.assertNotIn(wall, detected)

    def test_detect_actor_returns_first_matching_actor_for_class_filter(self):
        hunter = self._create_actor(Hunter)
        runner = self._create_actor(Runner)
        self._create_actor(Wall)

        detected = hunter.sensor_manager.detect_actor(Runner)

        self.assertIs(detected, runner)

    def test_detect_actors_uses_cached_actor_class_lookup_when_available(self):
        hunter = self._create_actor(Hunter)
        runner = self._create_actor(Runner)
        fast_runner = self._create_actor(FastRunner)
        definition = self.world.event_manager.definition
        definition.actor_classes_by_name["runner"] = Runner

        with patch(
            "miniworlds.tools.actor_class_inspection.ActorClassInspection.find_actor_class_by_classname"
        ) as find_class:
            detected = hunter.sensor_manager.detect_actors("runner")

        find_class.assert_not_called()
        self.assertCountEqual(detected, [runner, fast_runner])

    def test_get_actors_at_position_returns_empty_for_invalid_point_shape(self):
        hunter = self._create_actor(Hunter)

        detected = hunter.sensor_manager.get_actors_at_position((42,))

        self.assertEqual(detected, [])

    def test_get_actors_at_position_skips_actor_with_missing_position_manager(self):
        hunter = self._create_actor(Hunter)

        class BrokenActor:
            @property
            def position_manager(self):
                raise MissingPositionManager(self)

        self.world.camera.get_actors_in_view = lambda: [BrokenActor()]

        detected = hunter.sensor_manager.get_actors_at_position((20, 20))

        self.assertEqual(detected, [])

    def test_get_blocking_actor_at_position_returns_none_for_invalid_point_shape(self):
        hunter = self._create_actor(Hunter)

        detected = hunter.sensor_manager.get_blocking_actor_at_position((99,))

        self.assertIsNone(detected)

    def test_get_blocking_actor_at_position_skips_broken_blocking_actor(self):
        hunter = self._create_actor(Hunter)

        class BrokenBlockingActor:
            @property
            def position_manager(self):
                raise MissingPositionManager(self)

        self.world._blocking_actors.add(BrokenBlockingActor())

        detected = hunter.sensor_manager.get_blocking_actor_at_position((20, 20))

        self.assertIsNone(detected)


if __name__ == "__main__":
    unittest.main()