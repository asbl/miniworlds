from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from miniworlds.worlds.manager.collision_manager import CollisionManager


def test_handle_all_collisions_calls_all_internal_handlers(collision_world_builder):
    manager = CollisionManager(collision_world_builder())

    with patch.object(manager, "_handle_actor_detecting_actor_methods") as detecting:
        with patch.object(manager, "_handle_actor_not_detecting_actor_methods") as not_detecting:
            with patch.object(manager, "_handle_actor_detecting_border_methods") as borders:
                with patch.object(manager, "_handle_actor_detecting_on_the_world_methods") as on_world:
                    with patch.object(manager, "_handle_actor_detecting_not_on_the_world_methods") as off_world:
                        with patch.object(manager, "_handle_sensor_events") as sensor:
                            manager._handle_all_collisions()

    detecting.assert_called_once_with()
    not_detecting.assert_called_once_with()
    borders.assert_called_once_with()
    on_world.assert_called_once_with()
    off_world.assert_called_once_with()
    sensor.assert_called_once_with()


def test_handle_sensor_events_skips_when_registry_is_empty(collision_world_builder):
    manager = CollisionManager(collision_world_builder())

    with patch("miniworlds.worlds.manager.collision_manager.method_caller.call_method") as call_method:
        manager._handle_sensor_events()

    call_method.assert_not_called()


def test_handle_sensor_events_calls_method_for_detected_targets(
    collision_world_builder,
):
    world = collision_world_builder()
    actor = SimpleNamespace(
        sensor_manager=SimpleNamespace(detect_actors=Mock(return_value=[object()]))
    )
    method = Mock()
    method.__self__ = actor
    world.event_manager.registry.registered_events["sensor"]["runner"].add(method)
    manager = CollisionManager(world)

    with patch("miniworlds.worlds.manager.collision_manager.method_caller.call_method") as call_method:
        manager._handle_sensor_events()

    actor.sensor_manager.detect_actors.assert_called_once_with(filter="runner")
    call_method.assert_called_once_with(method, ("runner",))


def test_handle_sensor_events_only_calls_methods_for_matching_targets(
    collision_world_builder,
):
    world = collision_world_builder()
    matching_actor = SimpleNamespace(
        sensor_manager=SimpleNamespace(detect_actors=Mock(return_value=[object()]))
    )
    missing_actor = SimpleNamespace(
        sensor_manager=SimpleNamespace(detect_actors=Mock(return_value=[]))
    )
    matching_method = Mock()
    matching_method.__self__ = matching_actor
    missing_method = Mock()
    missing_method.__self__ = missing_actor
    world.event_manager.registry.registered_events["sensor"]["runner"].update(
        {matching_method, missing_method}
    )
    manager = CollisionManager(world)

    with patch("miniworlds.worlds.manager.collision_manager.method_caller.call_method") as call_method:
        manager._handle_sensor_events()

    matching_actor.sensor_manager.detect_actors.assert_called_once_with(filter="runner")
    missing_actor.sensor_manager.detect_actors.assert_called_once_with(filter="runner")
    call_method.assert_called_once_with(matching_method, ("runner",))


def test_handle_on_detecting_all_actors_excludes_self(collision_world_builder):
    actor = SimpleNamespace()
    target_one = SimpleNamespace(name="one")
    target_two = SimpleNamespace(name="two")
    actor.sensor_manager = SimpleNamespace(
        detect_actors=Mock(return_value=[actor, target_one, target_two])
    )
    method = Mock()
    manager = CollisionManager(collision_world_builder())

    with patch("miniworlds.worlds.manager.collision_manager.method_caller.call_method") as call_method:
        manager._handle_on_detecting_all_actors(actor, method)

    call_method.assert_has_calls(
        [
            call(method, target_one, target_one.__class__),
            call(method, target_two, target_two.__class__),
        ]
    )
    assert call_method.call_count == 2


def test_handle_actor_not_detecting_methods_calls_when_no_matches_exist(
    collision_world_builder,
):
    world = collision_world_builder()
    actor = SimpleNamespace(sensor_manager=SimpleNamespace(detect_actors=Mock(return_value=[])))
    method = Mock()
    method.__self__ = actor
    method.__name__ = "on_not_detecting_runner"
    world.event_manager.definition.class_events["on_not_detecting"] = {
        "on_not_detecting_runner"
    }
    world.event_manager.registry.registered_events["on_not_detecting_runner"] = {
        method
    }
    manager = CollisionManager(world)

    with patch("miniworlds.worlds.manager.collision_manager.method_caller.call_method") as call_method:
        manager._handle_actor_not_detecting_actor_methods()

    actor.sensor_manager.detect_actors.assert_called_once_with(filter="runner")
    call_method.assert_called_once_with(method, None)