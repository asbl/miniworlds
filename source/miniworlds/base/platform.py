from __future__ import annotations

import __main__
import asyncio
import os
import sqlite3
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Iterable

import pygame


class PlatformAdapter:
    def __init__(self) -> None:
        self._audio_initialized = False
        self._reserved_channels: int | None = None
        self._channel_count: int | None = None

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
        return pygame.display.set_mode(size, flags)

    def toggle_fullscreen(self) -> None:
        pygame.display.toggle_fullscreen()

    def display_info(self) -> pygame.display.Info:
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
        await asyncio.sleep(0)

    async def wait_for_frame(self, wait_time: float, skip_delay: bool = False) -> None:
        if skip_delay or wait_time <= 0:
            return
        await asyncio.sleep(wait_time)

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

    def connect_sqlite(self, file: str):
        return sqlite3.connect(file)

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
