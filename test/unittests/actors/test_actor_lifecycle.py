from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from miniworlds.actors.actor import Actor
from miniworlds.actors.actor_movement_facade import ActorMovementFacade
from miniworlds.actors.actor_size_facade import ActorSizeFacade
from miniworlds.base.exceptions import MiniworldsError
from miniworlds.worlds.manager.event_subscription import EventSubscription


class TestActorLifecycle(unittest.TestCase):
    def test_remove_returns_connector_result(self):
        actor = Actor.__new__(Actor)
        connector = MagicMock()
        unregistered_methods = [EventSubscription.event("act", MagicMock())]
        connector.remove_actor_from_world.return_value = unregistered_methods
        actor._world = SimpleNamespace(get_world_connector=MagicMock(return_value=connector))

        result = Actor.remove(actor, kill=False)

        actor.world.get_world_connector.assert_called_once_with(actor)
        connector.remove_actor_from_world.assert_called_once_with(kill=False)
        self.assertIs(result, unregistered_methods)

    def test_is_blockable_property_reads_position_manager_state(self):
        actor = Actor.__new__(Actor)
        actor._position_manager = SimpleNamespace(is_blockable=True)

        self.assertTrue(Actor.is_blockable.__get__(actor, Actor))

        actor._position_manager.is_blockable = False

        self.assertFalse(Actor.is_blockable.__get__(actor, Actor))

    def test_set_world_delegates_to_new_world_connector(self):
        actor = Actor.__new__(Actor)
        old_world = SimpleNamespace()
        actor._world = old_world
        connector = MagicMock()
        new_world = SimpleNamespace(get_world_connector=MagicMock(return_value=connector))

        result = Actor.set_world(actor, new_world)

        new_world.get_world_connector.assert_called_once_with(actor)
        connector.set_world.assert_called_once_with(old_world, new_world)
        self.assertIs(result, actor)

    def test_register_sensor_binds_method_and_registers_sensor_event(self):
        actor = Actor.__new__(Actor)
        actor._world = SimpleNamespace(event_manager=MagicMock())

        def on_sensor_enemy(self, target):
            return target

        decorator = Actor.register_sensor(actor, "enemy")
        bound_method = decorator(on_sensor_enemy)

        actor.world.event_manager.register_sensor_event.assert_called_once_with(
            "on_sensor_enemy",
            actor,
            "enemy",
        )
        self.assertIs(bound_method.__self__, actor)
        self.assertEqual(bound_method("ok"), "ok")

    def test_move_delegates_to_position_manager_and_applies_direction(self):
        actor = Actor.__new__(Actor)
        position_manager = MagicMock()
        position_manager.move.return_value = "moved"
        actor._position_manager = position_manager

        result = Actor.move(actor, distance=5, direction=90)

        position_manager.set_direction.assert_called_once_with(90)
        position_manager.move.assert_called_once_with(5)
        self.assertEqual(result, "moved")

    def test_position_accessors_delegate_to_position_manager(self):
        actor = Actor.__new__(Actor)
        position_manager = SimpleNamespace(position=(11, 22), set_position=MagicMock())
        actor._position_manager = position_manager

        self.assertEqual(Actor.position.__get__(actor, Actor), (11, 22))

        Actor.set_position(actor, (7, 8))
        position_manager.set_position.assert_called_once_with((7, 8))

        position_manager.set_position.reset_mock()
        Actor.x.__set__(actor, 30)
        position_manager.set_position.assert_called_once_with((30, 22))

        position_manager.set_position.reset_mock()
        Actor.y.__set__(actor, 40)
        position_manager.set_position.assert_called_once_with((11, 40))

    def test_move_in_direction_raises_for_invalid_direction_type(self):
        actor = Actor.__new__(Actor)
        actor._position_manager = MagicMock()

        with self.assertRaises(MiniworldsError):
            Actor.move_in_direction(actor, object(), 1)

    def test_size_delegates_to_position_manager(self):
        actor = Actor.__new__(Actor)
        pm = MagicMock()
        pm.get_size.return_value = (40, 60)
        actor._position_manager = pm

        self.assertEqual(Actor.size.__get__(actor, Actor), (40, 60))

        Actor.set_size(actor, (80, 120))
        pm.set_size.assert_called_once_with((80, 120))

    def test_width_and_height_delegate_to_position_manager(self):
        actor = Actor.__new__(Actor)
        pm = MagicMock()
        pm.get_size.return_value = (100, 200)
        actor._position_manager = pm
        actor.on_shape_change = MagicMock()

        self.assertEqual(Actor.width.__get__(actor, Actor), 100)
        self.assertEqual(Actor.height.__get__(actor, Actor), 200)

        Actor.width.__set__(actor, 50)
        pm.set_width.assert_called_once_with(50)
        actor.on_shape_change.assert_called_once()

        actor.on_shape_change.reset_mock()
        Actor.height.__set__(actor, 75)
        pm.set_height.assert_called_once_with(75)
        actor.on_shape_change.assert_called_once()

    def test_origin_and_switch_origin_delegate_to_position_manager(self):
        actor = Actor.__new__(Actor)
        pm = MagicMock()
        pm.origin = "center"
        actor._position_manager = pm

        self.assertEqual(Actor.origin.__get__(actor, Actor), "center")

        Actor.origin.__set__(actor, "topleft")
        self.assertEqual(pm.origin, "topleft")

        Actor.switch_origin(actor, "topleft")
        pm.switch_origin.assert_called_once_with("topleft")

    def test_last_position_and_last_direction_delegate_to_position_manager(self):
        actor = Actor.__new__(Actor)
        pm = SimpleNamespace(last_center=(5, 10), last_direction=45)
        actor._position_manager = pm

        self.assertEqual(Actor.last_position.__get__(actor, Actor), (5, 10))
        self.assertEqual(Actor.last_direction.__get__(actor, Actor), 45)

    def test_topleft_setters_keep_other_axis_unchanged(self):
        position_manager = SimpleNamespace(
            set_topleft=MagicMock(),
            get_topleft=MagicMock(return_value=(11, 22)),
        )
        actor = SimpleNamespace(
            position_manager=position_manager,
            get_global_rect=MagicMock(
                return_value=SimpleNamespace(
                    get_topleft=MagicMock(return_value=(11, 22))
                )
            ),
        )
        facade = ActorMovementFacade(actor)

        facade.set_topleft_x(30)
        position_manager.set_topleft.assert_called_once_with((30, 22))

        position_manager.set_topleft.reset_mock()
        facade.set_topleft_y(40)
        position_manager.set_topleft.assert_called_once_with((11, 40))

    def test_scale_helpers_handle_zero_dimensions(self):
        actor = SimpleNamespace(size=(0, 20), position_manager=MagicMock())
        facade = ActorSizeFacade(actor)

        facade.scale_width(50)
        self.assertEqual(actor.size, (50, 20))

        actor.size = (10, 0)
        facade.scale_height(40)
        self.assertEqual(actor.size, (10, 40))

    def test_is_blocking_setter_delegates_registry_sync_to_world_connector(self):
        actor = Actor.__new__(Actor)
        actor._position_manager = SimpleNamespace(is_blocking=False)
        connector = SimpleNamespace(sync_blocking_registration=MagicMock())
        actor._world = SimpleNamespace(get_world_connector=MagicMock(return_value=connector))

        Actor.is_blocking.__set__(actor, True)

        self.assertTrue(actor._position_manager.is_blocking)
        actor.world.get_world_connector.assert_called_once_with(actor)
        connector.sync_blocking_registration.assert_called_once_with(False, True)


if __name__ == "__main__":
    unittest.main()
