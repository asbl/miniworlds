import unittest
from unittest.mock import Mock
import pygame

from miniworlds.worlds.manager.camera_manager import CameraManager  

class TestCameraManager(unittest.TestCase):
    def setUp(self):
        self.mock_world = Mock()
        self.mock_world.actors = []
        self.mock_world.frame = 0
        self.mock_world.background.set_dirty = Mock()
        self.mock_world.app.resize = Mock()

        self.camera = CameraManager(100, 80, self.mock_world)
        self.camera._world_size_x = 200
        self.camera._world_size_y = 200

    def test_initial_state(self):
        self.assertEqual(self.camera.width, 100)
        self.assertEqual(self.camera.height, 80)
        self.assertEqual(self.camera.world_size, (200, 200))

    def test_position_and_center(self):
        self.camera.topleft = (10, 20)
        self.assertEqual(self.camera.topleft, (10, 20))
        self.assertAlmostEqual(self.camera.center[0], 60)
        self.assertAlmostEqual(self.camera.center[1], 60)

    def test_screen_translation(self):
        self.camera.screen_topleft = (5, 5)
        self.camera.topleft = (100, 100)
        screen_pos = self.camera.get_screen_position((120, 130)) # (120-100+5 130-100+5)
        self.assertEqual(screen_pos, (25, 35))

    def test_local_global_conversion(self):
        self.camera.topleft = (50, 25)
        self.assertEqual(self.camera.topleft,  (50,25))
        local = self.camera.get_local_position((70, 55))
        self.assertEqual(local, (20, 30))

        global_pos = self.camera.get_global_coordinates_for_world((20, 30))
        self.assertEqual(global_pos, (70, 55))

    def test_actor_visibility(self):
        mock_actor = Mock()
        mock_actor.position_manager.get_global_rect.return_value = self.camera.rect
        self.assertTrue(self.camera.is_actor_in_view(mock_actor))

    def test_get_actors_in_view(self):
        mock_actor = Mock()
        mock_actor.position_manager.get_global_rect.return_value = self.camera.rect
        self.mock_world.actors = [mock_actor]
        result = self.camera.get_actors_in_view()
        self.assertIn(mock_actor, result)

    def test_reload_camera_triggers_resize(self):
        self.camera._reload_camera()
        self.mock_world.app.resize.assert_called_once()

    def test_reload_actors_marks_dirty(self):
        mock_actor = Mock()
        mock_actor.position_manager.get_global_rect.return_value = self.camera.rect
        self.mock_world.actors = [mock_actor]
        self.camera._reload_actors_in_view()
        self.assertEqual(mock_actor.dirty, 1)

    def test_camera_outside_world_bounds(self):
        self.camera.world_size = (100, 100)
        self.camera.topleft = (200, 200)
        # Expect clamped to world size
        self.assertLessEqual(self.camera.topleft[0], 100)
        self.assertLessEqual(self.camera.topleft[1], 100)

    def test_resize_world_smaller_than_view(self):
        self.camera.width = 200
        self.camera.height = 150
        self.camera.world_size = (100, 100)
        self.assertEqual(self.camera.width, 200)  # View is kept
        self.assertEqual(self.camera.world_size, (100, 100))

    def test_set_dirty_and_update(self):
        self.camera.dirty = True
        self.camera._update()
        self.assertFalse(self.camera.dirty)

if __name__ == '__main__':
    unittest.main()
