import unittest

from miniworlds.base.app_state import AppState


class TestAppState(unittest.TestCase):
    def test_reset_clears_runtime_state(self):
        state = AppState(
            running_world=object(),
            running_worlds=[object(), object()],
            path="/tmp/project",
            running_app=object(),
            window=object(),
        )

        state.reset()

        self.assertIsNone(state.running_world)
        self.assertEqual(state.running_worlds, [])
        self.assertEqual(state.path, "")
        self.assertIsNone(state.running_app)
        self.assertIsNone(state.window)

    def test_reset_uses_unittest_file_directory(self):
        state = AppState()

        state.reset(unittest=True, file="/tmp/project/tests/test_state.py")

        self.assertEqual(state.path, "/tmp/project/tests")

    def test_bind_app_sets_all_references(self):
        app = object()
        world = object()
        window = object()
        state = AppState()

        state.bind_app(app, world, window)

        self.assertIs(state.running_app, app)
        self.assertIs(state.running_world, world)
        self.assertEqual(state.running_worlds, [world])
        self.assertIs(state.window, window)

    def test_add_running_world_prevents_duplicates(self):
        world = object()
        state = AppState(running_worlds=[world])

        state.add_running_world(world)

        self.assertEqual(state.running_worlds, [world])

    def test_remove_running_world_promotes_next_world(self):
        first = object()
        second = object()
        state = AppState(running_world=first, running_worlds=[first, second])

        state.remove_running_world(first)

        self.assertEqual(state.running_worlds, [second])
        self.assertIs(state.running_world, second)

    def test_remove_running_world_ignores_missing_entries(self):
        first = object()
        state = AppState(running_world=first, running_worlds=[first])

        state.remove_running_world(object())

        self.assertEqual(state.running_worlds, [first])
        self.assertIs(state.running_world, first)

    def test_set_path_normalizes_none_to_empty_string(self):
        state = AppState(path="/tmp/project")

        state.set_path(None)

        self.assertEqual(state.path, "")