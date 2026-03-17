import unittest
from unittest.mock import MagicMock, patch

from miniworlds.base.app import App


class DummyWorld:
    def __init__(self):
        self.dirty = 0
        self.background = MagicMock()
        self.background.set_dirty = MagicMock()


class TestAppLifecycle(unittest.TestCase):
    def setUp(self):
        App.reset()

    def tearDown(self):
        App.reset()

    def _create_app(self, world):
        with patch("miniworlds.base.app.worlds_manager.WorldsManager", return_value=MagicMock()):
            with patch("miniworlds.base.app.event_manager.AppEventManager", return_value=MagicMock()):
                with patch("miniworlds.base.app.sound_manager.SoundManager", return_value=MagicMock()):
                    with patch("miniworlds.base.app.music_manager.MusicManager", return_value=MagicMock()):
                        with patch("miniworlds.base.app.window_mod.Window", return_value=MagicMock()):
                            return App("TestApp", world)

    def test_reset_sets_path_for_unit_test_context(self):
        App.reset(unittest=True, file="/tmp/example/tests/test_sample.py")

        self.assertEqual(App.get_path(), "/tmp/example/tests")

    def test_initialization_binds_global_state(self):
        world = DummyWorld()
        app = self._create_app(world)

        self.assertIs(App.running_app, app)
        self.assertIs(App.get_running_world(), world)
        self.assertEqual(App.running_worlds, [world])
        self.assertIs(App.get_window(), app.window)

    def test_add_and_remove_running_worlds_keep_state_consistent(self):
        first_world = DummyWorld()
        second_world = DummyWorld()
        app = self._create_app(first_world)

        app.add_running_world(second_world)
        app.add_running_world(second_world)
        app.set_running_world(second_world)
        app.remove_running_world(second_world)

        self.assertEqual(App.running_worlds, [first_world])
        self.assertIs(App.get_running_world(), first_world)

    def test_direct_class_attribute_override_syncs_back_into_state_on_read(self):
        world = DummyWorld()
        self._create_app(world)
        replacement_world = DummyWorld()

        App.running_world = replacement_world
        App.path = "/tmp/override"

        self.assertIs(App.get_running_world(), replacement_world)
        self.assertIs(App._state.running_world, replacement_world)
        self.assertEqual(App.get_path(), "/tmp/override")
        self.assertEqual(App._state.path, "/tmp/override")


if __name__ == "__main__":
    unittest.main()