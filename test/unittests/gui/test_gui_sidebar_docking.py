import unittest
from types import SimpleNamespace

from miniworlds.base.app import App
from miniworlds.base.manager.app_worlds_manager import WorldsManager
from miniworlds.worlds.gui.pager import PagerHorizontal
from miniworlds.worlds.gui.toolbar import Toolbar
from miniworlds import World


class FakeWorld:
    def __init__(self, name, dock):
        self.name = name
        self._layout = SimpleNamespace(docking_position=dock)
        self.camera = SimpleNamespace(screen_topleft=(0, 0), width=100, height=100)
        self.dirty = 0
        self.is_listening = True
        self.is_running = True
        self.stopped = False

    def _clear(self):
        pass

    def stop(self):
        self.stopped = True
        self.is_running = False

    def _stop_listening(self):
        self.is_listening = False


class FakeApp:
    def __init__(self):
        self.running_worlds = []
        self.resize_calls = 0
        self.event_manager = SimpleNamespace(event_queue=[])

    def resize(self):
        self.resize_calls += 1

    def remove_running_world(self, world):
        if world in self.running_worlds:
            self.running_worlds.remove(world)


def make_manager(*worlds):
    app = FakeApp()
    manager = WorldsManager(app)
    manager.worlds = list(worlds)
    manager.topleft = next(
        (w for w in worlds if w._layout.docking_position == "top_left"), None
    )
    app.running_worlds = list(worlds)
    return manager, app


class TestWorldsManagerReset(unittest.TestCase):
    def test_reset_removes_all_docked_worlds(self):
        main = FakeWorld("main", "top_left")
        toolbar = FakeWorld("toolbar", "right")
        console = FakeWorld("console", "bottom")
        manager, _ = make_manager(main, toolbar, console)

        manager.reset()

        self.assertEqual([w.name for w in manager.worlds], ["main"])

    def test_reset_keeps_topleft_world_listening(self):
        main = FakeWorld("main", "top_left")
        toolbar = FakeWorld("toolbar", "right")
        manager, _ = make_manager(main, toolbar)

        manager.reset()

        self.assertTrue(main.is_listening)
        self.assertFalse(toolbar.is_listening)

    def test_reset_clears_event_queue(self):
        main = FakeWorld("main", "top_left")
        toolbar = FakeWorld("toolbar", "right")
        manager, app = make_manager(main, toolbar)
        app.event_manager.event_queue.append(("key_down", ("a",)))

        manager.reset()

        self.assertEqual(app.event_manager.event_queue, [])


class TestWorldsManagerRemoveWorld(unittest.TestCase):
    def test_remove_world_deactivates_world(self):
        main = FakeWorld("main", "top_left")
        toolbar = FakeWorld("toolbar", "right")
        manager, app = make_manager(main, toolbar)

        manager.remove_world(toolbar)

        self.assertNotIn(toolbar, manager.worlds)
        self.assertTrue(toolbar.stopped)
        self.assertFalse(toolbar.is_listening)
        self.assertNotIn(toolbar, app.running_worlds)
        self.assertIn(main, app.running_worlds)

    def test_remove_world_marks_remaining_worlds_dirty(self):
        main = FakeWorld("main", "top_left")
        toolbar = FakeWorld("toolbar", "right")
        manager, _ = make_manager(main, toolbar)

        manager.remove_world(toolbar)

        self.assertEqual(main.dirty, 1)

    def test_remove_unknown_world_is_noop(self):
        main = FakeWorld("main", "top_left")
        stranger = FakeWorld("stranger", "right")
        manager, _ = make_manager(main)

        manager.remove_world(stranger)

        self.assertEqual(manager.worlds, [main])
        self.assertTrue(stranger.is_listening)


class TestWorldsManagerWorldLists(unittest.TestCase):
    def test_worlds_right_omits_missing_topleft(self):
        toolbar = FakeWorld("toolbar", "right")
        manager, _ = make_manager(toolbar)
        manager.topleft = None

        self.assertEqual(manager.worlds_right(), [toolbar])

    def test_worlds_bottom_omits_missing_topleft(self):
        console = FakeWorld("console", "bottom")
        manager, _ = make_manager(console)
        manager.topleft = None

        self.assertEqual(manager.worlds_bottom(), [console])

    def test_worlds_right_orders_topleft_first(self):
        main = FakeWorld("main", "top_left")
        toolbar = FakeWorld("toolbar", "right")
        manager, _ = make_manager(main, toolbar)

        self.assertEqual(manager.worlds_right(), [main, toolbar])


class TestWorldsManagerLeftDocking(unittest.TestCase):
    def test_worlds_left_returns_only_left_docked_worlds(self):
        main = FakeWorld("main", "top_left")
        sidebar = FakeWorld("sidebar", "left")
        toolbar = FakeWorld("toolbar", "right")
        manager, _ = make_manager(main, sidebar, toolbar)

        self.assertEqual(manager.worlds_left(), [sidebar])

    def test_worlds_left_is_empty_without_left_worlds(self):
        main = FakeWorld("main", "top_left")
        manager, _ = make_manager(main)

        self.assertEqual(manager.worlds_left(), [])

    def test_update_all_worlds_positions_left_before_topleft(self):
        main = FakeWorld("main", "top_left")
        sidebar = FakeWorld("sidebar", "left")
        toolbar = FakeWorld("toolbar", "right")
        manager, _ = make_manager(main, sidebar, toolbar)

        manager._update_all_worlds()

        self.assertEqual(sidebar.camera.screen_topleft[0], 0)
        self.assertEqual(main.camera.screen_topleft[0], 100)
        self.assertEqual(toolbar.camera.screen_topleft[0], 200)

    def test_update_all_worlds_keeps_y_positions(self):
        main = FakeWorld("main", "top_left")
        main.camera.screen_topleft = (0, 42)
        sidebar = FakeWorld("sidebar", "left")
        sidebar.camera.screen_topleft = (0, 7)
        manager, _ = make_manager(main, sidebar)

        manager._update_all_worlds()

        # Left-docked worlds keep their own y position;
        # the top-left world anchors the bottom stack at y=0.
        self.assertEqual(sidebar.camera.screen_topleft, (0, 7))
        self.assertEqual(main.camera.screen_topleft, (100, 0))

    def test_recalculate_total_width_includes_left_worlds(self):
        main = FakeWorld("main", "top_left")
        sidebar = FakeWorld("sidebar", "left")
        toolbar = FakeWorld("toolbar", "right")
        manager, _ = make_manager(main, sidebar, toolbar)

        self.assertEqual(manager.recalculate_total_width(), 300)

    def test_recalculate_total_width_is_order_independent(self):
        sidebar = FakeWorld("sidebar", "left")
        main = FakeWorld("main", "top_left")
        manager, _ = make_manager(sidebar, main)

        self.assertEqual(manager.recalculate_total_width(), 200)

    def test_reset_removes_left_docked_worlds(self):
        main = FakeWorld("main", "top_left")
        sidebar = FakeWorld("sidebar", "left")
        manager, _ = make_manager(main, sidebar)

        manager.reset()

        self.assertEqual(manager.worlds, [main])
        self.assertFalse(sidebar.is_listening)


class TestPagerVisibleGuard(unittest.TestCase):
    class CountingButton:
        def __init__(self, visible):
            self._visible = visible
            self.assignments = 0

        @property
        def visible(self):
            return self._visible

        @visible.setter
        def visible(self, value):
            self.assignments += 1
            self._visible = value

    def _make_pager(self, can_scroll_down, can_scroll_up):
        pager = PagerHorizontal.__new__(PagerHorizontal)
        pager.gui = SimpleNamespace(
            can_scroll_down=lambda value: can_scroll_down,
            can_scroll_up=lambda value: can_scroll_up,
        )
        pager.pager_buttons = SimpleNamespace(
            down=self.CountingButton(visible=False),
            up=self.CountingButton(visible=True),
        )
        return pager

    def test_act_sets_visibility_only_on_change(self):
        pager = self._make_pager(can_scroll_down=True, can_scroll_up=False)

        PagerHorizontal.act(pager)
        PagerHorizontal.act(pager)
        PagerHorizontal.act(pager)

        self.assertTrue(pager.pager_buttons.down.visible)
        self.assertFalse(pager.pager_buttons.up.visible)
        self.assertEqual(pager.pager_buttons.down.assignments, 1)
        self.assertEqual(pager.pager_buttons.up.assignments, 1)

    def test_act_updates_visibility_when_scroll_range_changes(self):
        pager = self._make_pager(can_scroll_down=True, can_scroll_up=False)
        PagerHorizontal.act(pager)

        pager.gui = SimpleNamespace(
            can_scroll_down=lambda value: False,
            can_scroll_up=lambda value: True,
        )
        PagerHorizontal.act(pager)

        self.assertFalse(pager.pager_buttons.down.visible)
        self.assertTrue(pager.pager_buttons.up.visible)
        self.assertEqual(pager.pager_buttons.down.assignments, 2)
        self.assertEqual(pager.pager_buttons.up.assignments, 2)


class TestAddLeftIntegration(unittest.TestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_add_left_docks_toolbar_and_shifts_main_world(self):
        App.reset(unittest=True, file=__file__)
        world = World(200, 100)
        toolbar = Toolbar()
        world.camera.add_left(toolbar, size=50)

        self.assertEqual(toolbar.camera.screen_topleft, (0, 0))
        self.assertEqual(world.camera.screen_topleft, (50, 0))
        self.assertEqual(toolbar.camera.width, 50)
        self.assertEqual(toolbar.camera.height, 100)
        self.assertEqual(world.app.window.width, 250)

    def test_add_left_with_default_size(self):
        App.reset(unittest=True, file=__file__)
        world = World(200, 100)
        toolbar = Toolbar()
        world.camera.add_left(toolbar)

        self.assertEqual(toolbar.camera.width, 100)
        self.assertEqual(world.camera.screen_topleft, (100, 0))

    def test_add_left_then_add_right(self):
        App.reset(unittest=True, file=__file__)
        world = World(200, 100)
        sidebar = Toolbar()
        toolbar = Toolbar()
        world.camera.add_left(sidebar, size=50)
        world.camera.add_right(toolbar, size=60)

        self.assertEqual(sidebar.camera.screen_topleft, (0, 0))
        self.assertEqual(world.camera.screen_topleft, (50, 0))
        self.assertEqual(toolbar.camera.screen_topleft, (250, 0))
        self.assertEqual(world.app.window.width, 310)

    def test_remove_left_world_restores_layout(self):
        App.reset(unittest=True, file=__file__)
        world = World(200, 100)
        sidebar = Toolbar()
        world.camera.add_left(sidebar, size=50)

        world.camera.remove_world(sidebar)

        self.assertEqual(world.camera.screen_topleft, (0, 0))
        self.assertEqual(world.app.window.width, 200)


if __name__ == "__main__":
    unittest.main()
