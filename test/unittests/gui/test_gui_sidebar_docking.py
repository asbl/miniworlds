import unittest
from types import SimpleNamespace

from miniworlds.base.manager.app_worlds_manager import WorldsManager
from miniworlds.worlds.gui.pager import PagerHorizontal


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


if __name__ == "__main__":
    unittest.main()
