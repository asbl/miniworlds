from __future__ import annotations

import __main__
import asyncio
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Iterable

import pygame


class PlatformAdapter:
    def __init__(self) -> None:
        self._audio_initialized = False
        self._reserved_channels: int | None = None
        self._channel_count: int | None = None
        self._frame_yielded = False
        self._raf = None
        self._raf_unavailable = False
        self._create_once_callable = None

    def is_web(self) -> bool:
        return sys.platform == "emscripten"

    def read_main_module(self) -> str | None:
        main_file = getattr(__main__, "__file__", None)
        if not main_file:
            return None
        with open(main_file, encoding="utf-8") as file_handle:
            return file_handle.read()

    def get_package_version(self, package_name: str) -> str:
        try:
            from importlib.metadata import PackageNotFoundError, version
        except ImportError:
            return "unknown"

        try:
            return version(package_name)
        except PackageNotFoundError:
            return "unknown"

    def set_window_caption(self, title: str) -> None:
        pygame.display.set_caption(title)

    def load_surface(self, path: str | os.PathLike[str]) -> pygame.Surface:
        return pygame.image.load(os.fspath(path))

    def set_window_icon(self, surface: pygame.Surface) -> None:
        pygame.display.set_icon(surface)

    def set_mode(self, size, flags: int = 0) -> pygame.Surface:
        # Re-initialize the display subsystem if it was previously shut down
        # (e.g. after stop → rerun in H5P).  Without this, set_mode() silently
        # returns an unusable surface and the canvas stays black.
        if not pygame.display.get_init():
            pygame.display.init()
        return pygame.display.set_mode(size, flags)

    def set_window_position(self, position: tuple[int, int]) -> None:
        try:
            from pygame._sdl2 import Window as SDLWindow
        except (ImportError, pygame.error):
            return

        try:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=(
                        "Please use Window.get_surface and Window.flip to use "
                        "surface-rendering with Window.*"
                    ),
                    category=DeprecationWarning,
                )
                SDLWindow.from_display_module().position = position
        except (AttributeError, pygame.error):
            return

    def toggle_fullscreen(self) -> None:
        pygame.display.toggle_fullscreen()

    def display_info(self) -> pygame.display.Info:
        if not pygame.display.get_init():
            pygame.display.init()
        return pygame.display.Info()

    def update_display(self, repaint_areas) -> None:
        pygame.display.update(repaint_areas)

    def quit_display(self) -> None:
        pygame.display.quit()

    def poll_events(self):
        return pygame.event.get()

    def get_mouse_pos(self):
        return pygame.mouse.get_pos()

    async def yield_mainloop(self) -> None:
        # wait_for_frame already returned control to the browser this frame,
        # so a second timer hop (setTimeout clamping: >= 4 ms) is not needed.
        if self._frame_yielded:
            self._frame_yielded = False
            return
        if self.is_web() and await self._await_animation_frame():
            return
        await asyncio.sleep(0)

    async def wait_for_frame(self, wait_time: float, skip_delay: bool = False) -> None:
        if skip_delay:
            return
        if self.is_web():
            await self._wait_for_frame_web(wait_time)
            return
        if wait_time <= 0:
            return
        await asyncio.sleep(wait_time)

    async def _wait_for_frame_web(self, wait_time: float) -> None:
        # In Pyodide, asyncio.sleep() schedules via setTimeout, which browsers
        # clamp to >= 4 ms and which is not aligned with display refresh.
        # Pacing via requestAnimationFrame yields control exactly once per
        # painted frame, so even wait_time <= 0 must await one frame.
        deadline = time.perf_counter() + max(wait_time, 0.0)
        while True:
            if not await self._await_animation_frame():
                await asyncio.sleep(max(wait_time, 0.0))
                break
            if time.perf_counter() >= deadline:
                break
        self._frame_yielded = True

    async def _await_animation_frame(self) -> bool:
        request_animation_frame = self._get_request_animation_frame()
        if request_animation_frame is None:
            return False

        future = asyncio.get_event_loop().create_future()

        def _on_frame(_timestamp=None):
            if not future.done():
                future.set_result(None)

        request_animation_frame(self._create_once_callable(_on_frame))
        await future
        return True

    def _get_request_animation_frame(self):
        if self._raf_unavailable:
            return None
        if self._raf is not None:
            return self._raf
        try:
            import js
            from pyodide.ffi import create_once_callable
        except ImportError:
            self._raf_unavailable = True
            return None

        request_animation_frame = getattr(js, "requestAnimationFrame", None)
        if request_animation_frame is None:
            # e.g. inside a web worker without DOM access
            self._raf_unavailable = True
            return None

        self._raf = request_animation_frame
        self._create_once_callable = create_once_callable
        return self._raf

    def _should_prefer_dummy_audio(self) -> bool:
        if os.environ.get("SDL_AUDIODRIVER"):
            return False
        return (
            os.environ.get("MINIWORLDS_TEST_FAST") == "1"
            or os.environ.get("PYTEST_CURRENT_TEST") is not None
            or os.environ.get("MINIWORLDS_AUDIO_BACKEND") == "dummy"
        )

    def _initialize_audio(self) -> None:
        if self._should_prefer_dummy_audio():
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        try:
            pygame.mixer.init()
        except pygame.error:
            if os.environ.get("SDL_AUDIODRIVER") == "dummy":
                raise
            os.environ["SDL_AUDIODRIVER"] = "dummy"
            pygame.mixer.quit()
            pygame.mixer.init()

    def ensure_audio(self, reserved_channels: int | None = None, channel_count: int | None = None) -> None:
        if not self._audio_initialized:
            self._initialize_audio()
            self._audio_initialized = True

        if reserved_channels is not None and reserved_channels != self._reserved_channels:
            pygame.mixer.set_reserved(reserved_channels)
            self._reserved_channels = reserved_channels

        if channel_count is not None and channel_count != self._channel_count:
            pygame.mixer.set_num_channels(channel_count)
            self._channel_count = channel_count

    @property
    def music(self):
        self.ensure_audio()
        return pygame.mixer.music

    def load_sound(self, path: str) -> pygame.mixer.Sound:
        self.ensure_audio()
        return pygame.mixer.Sound(path)

    def find_channel(self):
        self.ensure_audio()
        return pygame.mixer.find_channel()

    def path_is_file(self, path: str | os.PathLike[str]) -> bool:
        return Path(path).is_file()

    def path_exists(self, path: str | os.PathLike[str]) -> bool:
        return Path(path).exists()

    def remove_file(self, path: str | os.PathLike[str]) -> None:
        Path(path).unlink()

    def relative_to_absolute_path(self, path: str) -> str:
        return str(path).replace("/", os.sep).replace("\\", os.sep)

    def join_path(self, *parts: str) -> str:
        return os.path.join(*parts)

    def resolve_path_with_file_endings(
        self,
        path: str,
        file_endings: Iterable[str],
        base_path: str | None = None,
    ) -> str:
        normalized_path = path[1:] if self.is_web() and path.startswith("/") else path
        direct_candidates = [normalized_path]
        prefixed_candidates = [normalized_path, self.join_path("images", normalized_path)]

        for candidate in direct_candidates:
            full_candidate = self._apply_base_path(candidate, base_path)
            if self.path_is_file(full_candidate):
                return self.relative_to_absolute_path(full_candidate)

        full_path = self._resolve_candidate_with_endings(prefixed_candidates, file_endings, base_path)
        if full_path:
            return full_path

        if "." in normalized_path:
            stem = normalized_path.rsplit(".", 1)[0]
            full_path = self._resolve_candidate_with_endings(
                [stem, self.join_path("images", stem)],
                file_endings,
                base_path,
            )
            if full_path:
                return full_path

        raise FileNotFoundError(f"Filepath {path} not found")

    def _apply_base_path(self, path: str, base_path: str | None) -> str:
        if base_path:
            return self.join_path(base_path, path)
        return path

    def _resolve_candidate_with_endings(
        self,
        candidates: Iterable[str],
        file_endings: Iterable[str],
        base_path: str | None,
    ) -> str | None:
        for candidate in candidates:
            for file_ending in file_endings:
                full_candidate = self._apply_base_path(f"{candidate}.{file_ending}", base_path)
                if self.path_is_file(full_candidate):
                    return self.relative_to_absolute_path(full_candidate)
        return None

    def save_image(self, surface: pygame.Surface, filename: str) -> None:
        pygame.image.save(surface, filename)
