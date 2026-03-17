import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from miniworlds.worlds.manager.mainloop_manager import MainloopManager


class TestMainloopManager(unittest.IsolatedAsyncioTestCase):
    def _create_world(self):
        world = MagicMock()
        world.is_running = True
        world.frame = 0
        world.tick_rate = 1
        world.fps = 60
        world.event_manager = MagicMock()
        world._collision_manager = MagicMock()
        world.mouse = MagicMock()
        world.backgrounds = MagicMock()
        world.background = MagicMock()
        world.camera = MagicMock()
        world._dynamic_actors = []
        world._timed_objects = []
        return world

    async def test_update_skips_frame_delay_in_fast_mode(self):
        world = self._create_world()
        app = MagicMock()
        app._skip_frame_delay = True
        app.platform = SimpleNamespace(wait_for_frame=AsyncMock())
        manager = MainloopManager(world, app)

        with patch(
            "miniworlds.worlds.manager.mainloop_manager.time.perf_counter",
            side_effect=[0.0, 0.0],
        ):
            await manager.update()

        app.platform.wait_for_frame.assert_awaited_once_with(1 / world.fps, True)
        self.assertEqual(world.frame, 1)

    async def test_update_waits_for_remaining_frame_time_by_default(self):
        world = self._create_world()
        app = MagicMock()
        app._skip_frame_delay = False
        app.platform = SimpleNamespace(wait_for_frame=AsyncMock())
        manager = MainloopManager(world, app)

        with patch(
            "miniworlds.worlds.manager.mainloop_manager.time.perf_counter",
            side_effect=[0.0, 0.0],
        ):
            await manager.update()

        app.platform.wait_for_frame.assert_awaited_once_with(1 / world.fps, False)


if __name__ == "__main__":
    unittest.main()