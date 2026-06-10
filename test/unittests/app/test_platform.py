import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

import pygame

from miniworlds.base.platform import PlatformAdapter


class TestPlatformAdapter(unittest.TestCase):
    def test_ensure_audio_prefers_dummy_backend_in_test_mode(self):
        adapter = PlatformAdapter()

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SDL_AUDIODRIVER", None)
            os.environ["MINIWORLDS_TEST_FAST"] = "1"
            with patch("pygame.mixer.init") as init_mock:
                adapter.ensure_audio()

                self.assertEqual(os.environ["SDL_AUDIODRIVER"], "dummy")
                init_mock.assert_called_once_with()

    def test_ensure_audio_falls_back_to_dummy_backend_after_init_error(self):
        adapter = PlatformAdapter()

        with patch.dict(os.environ, {}, clear=True):
            with patch("pygame.mixer.init", side_effect=[pygame.error("boom"), None]) as init_mock:
                with patch("pygame.mixer.quit") as quit_mock:
                    adapter.ensure_audio()

                    self.assertEqual(os.environ["SDL_AUDIODRIVER"], "dummy")
                    self.assertEqual(init_mock.call_count, 2)
                    quit_mock.assert_called_once_with()

    def test_get_package_version_returns_unknown_for_missing_distribution(self):
        adapter = PlatformAdapter()

        self.assertEqual(
            adapter.get_package_version("__missing_miniworlds_test_package__"),
            "unknown",
        )

    def test_get_package_version_returns_unknown_without_importlib_metadata(self):
        adapter = PlatformAdapter()

        with patch.dict("sys.modules", {"importlib.metadata": None}):
            self.assertEqual(adapter.get_package_version("miniworlds"), "unknown")


class TestPlatformFramePacing(unittest.TestCase):
    def _make_web_adapter(self):
        adapter = PlatformAdapter()
        adapter.is_web = lambda: True
        return adapter

    def test_wait_for_frame_desktop_sleeps_wait_time(self):
        adapter = PlatformAdapter()
        adapter.is_web = lambda: False

        with patch("miniworlds.base.platform.asyncio.sleep", new=AsyncMock()) as sleep_mock:
            asyncio.run(adapter.wait_for_frame(0.02))
            sleep_mock.assert_awaited_once_with(0.02)

    def test_wait_for_frame_web_awaits_one_animation_frame_without_wait(self):
        adapter = self._make_web_adapter()

        with patch.object(adapter, "_await_animation_frame", new=AsyncMock(return_value=True)) as raf_mock:
            asyncio.run(adapter.wait_for_frame(0))

        self.assertEqual(raf_mock.await_count, 1)
        self.assertTrue(adapter._frame_yielded)

    def test_wait_for_frame_web_awaits_animation_frames_until_deadline(self):
        adapter = self._make_web_adapter()

        with patch.object(adapter, "_await_animation_frame", new=AsyncMock(return_value=True)) as raf_mock:
            with patch("miniworlds.base.platform.time.perf_counter", side_effect=[0.0, 0.005, 0.011, 0.017]):
                asyncio.run(adapter.wait_for_frame(0.016))

        self.assertEqual(raf_mock.await_count, 3)
        self.assertTrue(adapter._frame_yielded)

    def test_wait_for_frame_web_falls_back_to_sleep_without_raf(self):
        adapter = self._make_web_adapter()
        adapter._raf_unavailable = True

        with patch("miniworlds.base.platform.asyncio.sleep", new=AsyncMock()) as sleep_mock:
            asyncio.run(adapter.wait_for_frame(0.016))

        sleep_mock.assert_awaited_once_with(0.016)
        self.assertTrue(adapter._frame_yielded)

    def test_wait_for_frame_skip_delay_does_not_mark_frame_yielded(self):
        adapter = self._make_web_adapter()

        with patch.object(adapter, "_await_animation_frame", new=AsyncMock(return_value=True)) as raf_mock:
            asyncio.run(adapter.wait_for_frame(0.016, skip_delay=True))

        self.assertEqual(raf_mock.await_count, 0)
        self.assertFalse(adapter._frame_yielded)

    def test_yield_mainloop_skips_extra_hop_after_wait_for_frame(self):
        adapter = self._make_web_adapter()

        async def scenario():
            with patch.object(adapter, "_await_animation_frame", new=AsyncMock(return_value=True)) as raf_mock:
                await adapter.wait_for_frame(0)
                await adapter.yield_mainloop()
                return raf_mock.await_count

        self.assertEqual(asyncio.run(scenario()), 1)
        self.assertFalse(adapter._frame_yielded)

    def test_yield_mainloop_uses_animation_frame_when_no_wait_happened(self):
        adapter = self._make_web_adapter()

        with patch.object(adapter, "_await_animation_frame", new=AsyncMock(return_value=True)) as raf_mock:
            asyncio.run(adapter.yield_mainloop())

        self.assertEqual(raf_mock.await_count, 1)

    def test_yield_mainloop_desktop_unchanged(self):
        adapter = PlatformAdapter()
        adapter.is_web = lambda: False

        with patch("miniworlds.base.platform.asyncio.sleep", new=AsyncMock()) as sleep_mock:
            asyncio.run(adapter.yield_mainloop())

        sleep_mock.assert_awaited_once_with(0)


if __name__ == "__main__":
    unittest.main()
