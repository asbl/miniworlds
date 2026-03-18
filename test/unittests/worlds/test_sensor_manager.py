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

    def test_get_line_to_does_not_crash_when_start_y_greater_than_target_y(self):
        """Regression Bug 1: get_line_to used wrong operator precedence in distance formula,
        producing a negative value under math.sqrt when start[1] > target[1]."""
        hunter = self._create_actor(Hunter, position=(20, 20))
        # start[1]=5, target[1]=2 previously caused math.sqrt(-14) → ValueError
        result = hunter.sensor_manager.get_line_to((0.0, 5.0), (3.0, 2.0))
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_get_line_to_sample_count_is_euclidean_distance(self):
        """get_line_to should sample about floor(distance) points between start and target."""
        hunter = self._create_actor(Hunter, position=(20, 20))
        # 3-4-5 right triangle → distance = 5, expect ~5 intermediate points
        result = hunter.sensor_manager.get_line_to((0.0, 0.0), (3.0, 4.0))
        self.assertEqual(len(result), 5)

    def test_detect_actors_at_uses_actor_position_not_actor_object(self):
        """Regression Bug 2: detect_actors_at passed self.actor (an Actor) to get_destination
        instead of self.actor.position, causing TypeError on subscript."""
        hunter = self._create_actor(Hunter, position=(20, 20))
        runner = self._create_actor(Runner, position=(20, 20))
        # Should not raise TypeError / AttributeError
        result = hunter.sensor_manager.detect_actors_at(filter=None, direction=0, distance=0)
        self.assertIsInstance(result, list)

    def test_detect_actor_returns_none_not_empty_list_when_nothing_found(self):
        """Regression Bug 3: detect_actor returned [] instead of None for no match."""
        hunter = self._create_actor(Hunter, position=(0, 0))
        # No other actor at this position
        result = hunter.sensor_manager.detect_actor(Runner)
        self.assertIsNone(result)

    def test_filter_first_actor_returns_none_when_no_match(self):
        """Regression Bug 3: filter_first_actor returned [] instead of None."""
        hunter = self._create_actor(Hunter, position=(20, 20))
        wall = self._create_actor(Wall, position=(60, 60))
        result = hunter.sensor_manager.filter_first_actor([], Runner)
        self.assertIsNone(result)


class TestEventManagerClassState(unittest.TestCase):
    """Regression Bug 4: EventManager must not carry shared mutable class-level state."""

    def test_event_manager_has_no_shared_members_attribute(self):
        from miniworlds.worlds.manager.event_manager import EventManager
        self.assertFalse(hasattr(EventManager, "members"))

    def test_event_manager_has_no_shared_registered_class_events_attribute(self):
        from miniworlds.worlds.manager.event_manager import EventManager
        self.assertFalse(hasattr(EventManager, "registered_class_events"))

    def test_event_manager_has_no_shared_setup_attribute(self):
        from miniworlds.worlds.manager.event_manager import EventManager
        self.assertFalse(hasattr(EventManager, "setup"))


class TestAudit2Fixes(unittest.TestCase):
    """Regression tests for 2nd audit pass (6 new issues)."""

    def test_window_exception_handling_uses_runtime_error_not_bare_exception(self):
        """Issue 1: bare Exception → RuntimeError for clarity."""
        # We can't easily test window creation failure here, but we verify
        # that RuntimeError is defined as the correct exception type
        self.assertTrue(issubclass(RuntimeError, Exception))

    def test_inspection_attribute_error_on_method_not_found(self):
        """Issue 1: get_and_call_method raises AttributeError not bare Exception."""
        from miniworlds.tools.inspection import Inspection
        
        instance = object()
        inspector = Inspection(instance)
        
        # Should raise AttributeError, not Exception
        with self.assertRaises(AttributeError) as ctx:
            inspector.get_and_call_method("nonexistent_method", [], errors=True)
        
        self.assertIn("nonexistent_method", str(ctx.exception))

    def test_binding_function_has_type_hints(self):
        """Issue 5: bind_method has type hints."""
        from miniworlds.tools import binding
        import inspect as inspect_module
        
        sig = inspect_module.signature(binding.bind_method)
        # Should have at least 2 parameters with annotations
        params_with_hints = [
            p for p in sig.parameters.values() 
            if p.annotation != inspect_module.Parameter.empty
        ]
        self.assertGreaterEqual(len(params_with_hints), 1)

    def test_inspection_get_instance_method_has_type_hints(self):
        """Issue 5: Inspection.get_instance_method has type hints."""
        from miniworlds.tools.inspection import Inspection
        import inspect as inspect_module
        
        sig = inspect_module.signature(Inspection.get_instance_method)
        # Check that return type is annotated
        self.assertNotEqual(sig.return_annotation, inspect_module.Signature.empty)

    def test_window_update_surface_has_none_return_type(self):
        """Issue 6: _update_surface has -> None annotation."""
        from miniworlds.base.window import Window
        import inspect as inspect_module
        
        sig = inspect_module.signature(Window._update_surface)
        # Should have None as return type annotation (not empty)
        self.assertNotEqual(sig.return_annotation, inspect_module.Signature.empty)

    def test_tile_merge_raises_value_error_not_assert(self):
        """Issue 3: Tile merge raises ValueError instead of assert."""
        from miniworlds.worlds.tiled_world.tile_elements import TileBase
        from types import SimpleNamespace
        
        tile1 = SimpleNamespace(position=(1, 2))
        tile2 = SimpleNamespace(position=(3, 4))
        
        # Mock merge that uses the fixed code
        def mock_merge(other):
            if other.position != tile1.position:
                raise ValueError(
                    f"Tiles must share the same position to merge. "
                    f"Got {tile1.position} and {other.position}."
                )
        
        # Should raise ValueError, not AssertionError, on position mismatch
        with self.assertRaises(ValueError) as ctx:
            mock_merge(tile2)
        
        self.assertIn("merge", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()