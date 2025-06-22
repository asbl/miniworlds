import unittest
from miniworlds.worlds.manager.position_manager import Positionmanager
from unittest.mock import MagicMock

class TestPositionManagerMove(unittest.TestCase):

    def setUp(self):
        # Create an Actor object with required attributes and methods
        self.actor = MagicMock()
        self.world = MagicMock()
        self.actor.speed = 5
        self.actor.sensor_manager = MagicMock()
        
        # The object that has the move method
        self.mover = Positionmanager(self.actor, self.world, (0,0))
        self.mover.actor = self.actor
        
        # Mocks for methods
        self.mover.get_position = MagicMock(return_value=(0, 0))
        self.mover.get_direction = MagicMock(return_value=1)  # Simple direction value
        self.mover.set_position = MagicMock()
        self.mover.is_blockable = True
        self.mover.last_direction = None

    def test_move_with_default_distance_and_no_blocking(self):
        # Destination is calculated
        self.actor.sensor_manager.get_destination.return_value = (5, 0)
        # No blocking actors found
        self.actor.sensor_manager.detect_actors_at_destination.return_value = []
        
        # Execute move without parameter (distance=0 -> speed=5)
        result = self.mover.move()
        
        # Expect position to be set
        self.mover.set_position.assert_called_once_with((5, 0))
        # Return value should be self.actor
        self.assertEqual(result, self.actor)

    def test_move_with_negative_distance_blocked(self):
        # Destination is calculated (backwards)
        self.actor.sensor_manager.get_destination.return_value = (-5, 0)
        # Blocking actor found
        blocking_actor = MagicMock()
        blocking_actor.is_blocking = True
        self.actor.sensor_manager.detect_actors_at_destination.return_value = [blocking_actor]
        
        # Execute move with negative distance
        result = self.mover.move(distance=-5)
        
        # set_position should not be called since blocked
        self.mover.set_position.assert_not_called()
        self.assertEqual(result, self.actor)

    def test_move_with_positive_distance_blockable_false(self):
        # Set is_blockable to False
        self.mover.is_blockable = False
        self.actor.sensor_manager.get_destination.return_value = (10, 0)
        
        # Execute move with positive distance
        result = self.mover.move(distance=10)
        
        # Position should be set
        self.mover.set_position.assert_called_once_with((10, 0))
        # last_direction should be updated
        self.assertEqual(self.mover.last_direction, 1)
        self.assertEqual(result, self.actor)

if __name__ == "__main__":
    unittest.main()
