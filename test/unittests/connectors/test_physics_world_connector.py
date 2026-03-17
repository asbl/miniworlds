import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from miniworlds_physics.physics_world_connector import PhysicsWorldConnector


class TestPhysicsWorldConnector(unittest.TestCase):
    def _create_actor(self):
        return SimpleNamespace(
            position_manager=SimpleNamespace(
                impulse=Mock(),
                force=Mock(),
                set_simulation=Mock(),
                set_velocity_x=Mock(),
                set_velocity_y=Mock(),
                set_velocity=Mock(),
            )
        )

    def test_get_registered_actor_returns_connector_actor_when_present(self):
        actor = object()
        connector = SimpleNamespace(actor=actor)

        self.assertIs(PhysicsWorldConnector._get_registered_actor(connector), actor)

    def test_get_registered_actor_returns_actor_for_actor_bound_calls(self):
        actor = object()

        self.assertIs(PhysicsWorldConnector._get_registered_actor(actor), actor)

    def test_registered_helper_methods_forward_when_called_on_connector(self):
        actor = self._create_actor()
        connector = SimpleNamespace(actor=actor)

        PhysicsWorldConnector.impulse(connector, 90, 12)
        PhysicsWorldConnector.force(connector, 45, 8)
        PhysicsWorldConnector.set_simulation(connector, "manual")
        PhysicsWorldConnector.set_velocity_x(connector, 5)
        PhysicsWorldConnector.set_velocity_y(connector, 7)
        PhysicsWorldConnector.set_velocity(connector, (3, 4))

        actor.position_manager.impulse.assert_called_once_with(90, 12)
        actor.position_manager.force.assert_called_once_with(45, 8)
        actor.position_manager.set_simulation.assert_called_once_with("manual")
        actor.position_manager.set_velocity_x.assert_called_once_with(5)
        actor.position_manager.set_velocity_y.assert_called_once_with(7)
        actor.position_manager.set_velocity.assert_called_once_with((3, 4))

    def test_registered_helper_methods_forward_when_called_on_actor(self):
        actor = self._create_actor()

        PhysicsWorldConnector.impulse(actor, 180, 4)
        PhysicsWorldConnector.force(actor, 270, 6)
        PhysicsWorldConnector.set_simulation(actor, "simulated")
        PhysicsWorldConnector.set_velocity_x(actor, 9)
        PhysicsWorldConnector.set_velocity_y(actor, 11)
        PhysicsWorldConnector.set_velocity(actor, (1, 2))

        actor.position_manager.impulse.assert_called_once_with(180, 4)
        actor.position_manager.force.assert_called_once_with(270, 6)
        actor.position_manager.set_simulation.assert_called_once_with("simulated")
        actor.position_manager.set_velocity_x.assert_called_once_with(9)
        actor.position_manager.set_velocity_y.assert_called_once_with(11)
        actor.position_manager.set_velocity.assert_called_once_with((1, 2))