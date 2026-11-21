"""Frame pacing includes all work without changing simulation tick semantics."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from miniworlds.base.app import App
from miniworlds.base.manager.app_worlds_manager import WorldsManager
from miniworlds.worlds.manager.mainloop_manager import MainloopManager


class TestAppFramePacing(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.now = 100.0
        self.app = object.__new__(App)
        self.app._quit = False
        self.app._skip_frame_delay = False
        self.app.window = SimpleNamespace(dirty=False)
        self.app.platform = SimpleNamespace(
            wait_for_frame=AsyncMock(), yield_mainloop=AsyncMock()
        )
        self.app.event_manager = SimpleNamespace(
            pygame_events_to_event_queue=Mock(side_effect=lambda: self.advance(0.001)),
            handle_event_queue=Mock(side_effect=lambda: self.advance(0.002)),
        )
        self.app.resize = Mock(side_effect=lambda: self.advance(0.003))
        self.app.display_repaint = Mock(side_effect=lambda: self.advance(0.001))
        self.app.worlds_manager = WorldsManager(self.app)
        self.clock_patch = patch(
            "miniworlds.base.app.time.perf_counter", side_effect=lambda: self.now
        )
        self.host_patch = patch(
            "miniworlds.base.app.runtime_host.poll",
            side_effect=lambda app: self.advance(0.001),
        )
        self.clock_patch.start()
        self.host_patch.start()
        self.addCleanup(self.clock_patch.stop)
        self.addCleanup(self.host_patch.stop)

    def advance(self, seconds):
        self.now += seconds

    def world(self, fps=30):
        world = MagicMock()
        world.dirty = True
        world.is_running = True
        world.is_paused = False
        world.frame = 1
        world.tick_rate = 1
        world.fps = fps
        world._dynamic_actors = []
        world._timed_objects = [SimpleNamespace(tick=Mock())]
        world._runtime_facade = SimpleNamespace(_pending_steps=0)
        world.event_manager.act_all.side_effect = lambda: self.advance(0.005)
        world._mainloop = MainloopManager(world, self.app)
        world._mainloop.repaint = Mock(side_effect=lambda: self.advance(0.008))
        world._mainloop.blit_surface_to_window_surface = Mock(
            side_effect=lambda: self.advance(0.002)
        )
        self.app.worlds_manager.worlds.append(world)
        return world

    def assert_wait(self, expected):
        self.app.platform.wait_for_frame.assert_awaited_once()
        duration, skip_delay = self.app.platform.wait_for_frame.await_args.args
        self.assertAlmostEqual(duration, expected)
        self.assertEqual(skip_delay, self.app._skip_frame_delay)
        self.app.platform.yield_mainloop.assert_awaited_once()

    async def test_budget_includes_input_resize_simulation_drawing_and_display(self):
        world = self.world()
        self.app.window.dirty = True

        await self.app._update()

        # Input/host: 4 ms, resize: 3 ms, simulation: 5 ms,
        # drawing: 8 ms, window copy: 2 ms, presentation: 1 ms.
        self.assert_wait(1 / 30 - 0.023)
        self.app.resize.assert_called_once()
        self.app.display_repaint.assert_called_once()
        world.event_manager.act_all.assert_called_once()
        world._timed_objects[0].tick.assert_called_once()
        self.assertEqual(world.frame, 2)

    async def test_overrun_waits_zero_without_extra_simulation_steps(self):
        world = self.world(fps=60)

        await self.app._update()

        self.assert_wait(0)
        world.event_manager.act_all.assert_called_once()
        world._timed_objects[0].tick.assert_called_once()
        self.assertEqual(world.frame, 2)

    async def test_multiple_worlds_share_budget_in_both_orders(self):
        for rates in ((10, 20), (20, 10)):
            with self.subTest(rates=rates):
                self.app.worlds_manager.worlds.clear()
                self.app.platform.wait_for_frame.reset_mock()
                self.app.platform.yield_mainloop.reset_mock()
                worlds = [self.world(fps=rate) for rate in rates]

                await self.app._update()

                # Both worlds' full work counts, regardless of their order.
                self.assert_wait(1 / 20 - 0.035)
                for world in worlds:
                    world.event_manager.act_all.assert_called_once()
                    self.assertEqual(world.frame, 2)

    async def test_pause_keeps_input_and_rendering_without_advancing_simulation(self):
        world = self.world()
        world.is_paused = True

        await self.app._update()

        self.assert_wait(1 / 30 - 0.015)
        world.event_manager.update.assert_called_once()
        world.event_manager.act_all.assert_not_called()
        world._timed_objects[0].tick.assert_not_called()
        world._mainloop.repaint.assert_called_once()
        self.assertEqual(world.frame, 1)

    async def test_single_step_on_initial_frame_advances_once_then_stays_paused(self):
        world = self.world()
        world.is_paused = True
        world.frame = 0
        world._runtime_facade._pending_steps = 1

        await self.app._update()
        await self.app._update()

        world.event_manager.act_all.assert_called_once()
        world._timed_objects[0].tick.assert_called_once()
        self.assertEqual(world.frame, 1)
        self.assertEqual(world._runtime_facade._pending_steps, 0)
        self.assertEqual(self.app.platform.wait_for_frame.await_count, 2)

    async def test_tick_rate_still_controls_act_calls(self):
        world = self.world()
        world.tick_rate = 2
        world.frame = 3

        await self.app._update()
        world.event_manager.act_all.assert_not_called()
        await self.app._update()

        world.event_manager.act_all.assert_called_once()
        self.assertEqual(world._timed_objects[0].tick.call_count, 2)
        self.assertEqual(world.frame, 5)

    async def test_stopped_world_does_not_request_a_wait(self):
        world = self.world()
        world.is_running = False

        await self.app._update()

        self.app.platform.wait_for_frame.assert_not_awaited()
        self.app.platform.yield_mainloop.assert_awaited_once()
        world.event_manager.act_all.assert_not_called()
        self.assertEqual(world.frame, 1)

    async def test_fast_test_mode_is_forwarded_to_platform(self):
        self.world()
        self.app._skip_frame_delay = True

        await self.app._update()

        self.assert_wait(1 / 30 - 0.020)

    async def test_quit_does_not_update_draw_or_wait(self):
        world = self.world()
        self.app._quit = True

        await self.app._update()

        world._mainloop.repaint.assert_not_called()
        self.app.display_repaint.assert_not_called()
        self.app.platform.wait_for_frame.assert_not_awaited()
        self.app.platform.yield_mainloop.assert_not_awaited()
        self.assertEqual(world.frame, 1)
