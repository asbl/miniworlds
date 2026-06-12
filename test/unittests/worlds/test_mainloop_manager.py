import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pygame

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

    async def test_update_returns_remaining_frame_budget(self):
        world = self._create_world()
        app = MagicMock()
        app.platform = SimpleNamespace(wait_for_frame=AsyncMock())
        manager = MainloopManager(world, app)

        with patch(
            "miniworlds.worlds.manager.mainloop_manager.time.perf_counter",
            side_effect=[0.0, 0.0],
        ):
            frame_wait = await manager.update()

        # The frame wait happens once per app frame in App._update; a wait
        # per world would multiply the frame delay by the number of worlds.
        self.assertEqual(frame_wait, 1 / world.fps)
        app.platform.wait_for_frame.assert_not_awaited()
        self.assertEqual(world.frame, 1)

    async def test_update_subtracts_elapsed_time_from_frame_budget(self):
        world = self._create_world()
        app = MagicMock()
        app.platform = SimpleNamespace(wait_for_frame=AsyncMock())
        manager = MainloopManager(world, app)

        with patch(
            "miniworlds.worlds.manager.mainloop_manager.time.perf_counter",
            side_effect=[0.0, 0.01],
        ):
            frame_wait = await manager.update()

        self.assertAlmostEqual(frame_wait, 1 / world.fps - 0.01)

    async def test_update_returns_none_for_paused_world(self):
        world = self._create_world()
        world.is_running = False
        world.frame = 5
        app = MagicMock()
        manager = MainloopManager(world, app)

        self.assertIsNone(await manager.update())

    def test_blit_calls_debug_overlay_when_available(self):
        world = self._create_world()
        world._draw_debug_overlay = MagicMock()
        world.background.surface = pygame.Surface((20, 20))
        world.camera.screen_rect = pygame.Rect(0, 0, 20, 20)
        app = MagicMock()
        app.window = SimpleNamespace(surface=pygame.Surface((20, 20)))
        manager = MainloopManager(world, app)

        manager.blit_surface_to_window_surface()

        world._draw_debug_overlay.assert_called_once_with(app.window.surface)


if __name__ == "__main__":
    unittest.main()