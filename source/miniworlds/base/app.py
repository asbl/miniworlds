import __main__
import os
import sys
import warnings
import asyncio
import logging

import pygame

from typing import List, Optional, TYPE_CHECKING, cast
from importlib.metadata import version, PackageNotFoundError

import miniworlds.appearances.managers.image_manager as image_manager
import miniworlds.base.manager.app_event_manager as event_manager
import miniworlds.base.manager.app_worlds_manager as worlds_manager
import miniworlds.base.manager.app_music_manager as music_manager
import miniworlds.base.manager.app_sound_manager as sound_manager
import miniworlds.base.app_state as app_state
import miniworlds.base.app_state_bridge as app_state_bridge
import miniworlds.base.platform as platform_mod
import miniworlds.base.window as window_mod
from miniworlds.base.window import Window

if TYPE_CHECKING:
    from miniworlds.base.manager.app_event_manager import AppEventManager
    from miniworlds.base.manager.app_worlds_manager import WorldsManager
    from miniworlds.base.manager.app_music_manager import MusicManager
    from miniworlds.base.manager.app_sound_manager import SoundManager
    from miniworlds.worlds.world import World


logger = logging.getLogger(__name__)


class App:
    """
    Main application class for Miniworlds.
    Created automatically when `world.run()` is called for the first time.

    Raises:
        NoRunError: If `run()` is not called from the main module.
    """

    _state = app_state.AppState()
    _state_bridge: "app_state_bridge.AppStateBridge | None" = None
    _fallback_platform = platform_mod.PlatformAdapter()
    running_world: Optional["World"] = None
    running_worlds: List["World"] = []
    path: str | None = ""
    running_app: Optional["App"] = None
    init: bool = False
    window: Optional["Window"] = None

    @classmethod
    def _get_state_bridge(cls) -> app_state_bridge.AppStateBridge:
        bridge = cls._state_bridge
        if bridge is None or bridge.app_class is not cls or bridge.state is not cls._state:
            bridge = app_state_bridge.AppStateBridge(cls, cls._state)
            cls._state_bridge = bridge
        return bridge

    @classmethod
    def _sync_class_state(cls) -> None:
        cls._get_state_bridge().sync_class_state()

    @classmethod
    def get_running_world(cls) -> Optional["World"]:
        return cls._get_state_bridge().get_running_world()

    @classmethod
    def get_running_app(cls) -> Optional["App"]:
        return cls._get_state_bridge().get_running_app()

    @classmethod
    def get_window(cls) -> Optional["Window"]:
        return cls._get_state_bridge().get_window()

    @classmethod
    def get_path(cls) -> str | None:
        return cls._get_state_bridge().get_path()

    @classmethod
    def get_platform(cls) -> platform_mod.PlatformAdapter:
        running_app = cls.get_running_app()
        if running_app and hasattr(running_app, "platform"):
            return running_app.platform
        return cls._fallback_platform

    @staticmethod
    def reset(unittest=False, file=None):
        """
        Resets all app globals.

        Args:
            unittest: Whether the reset is being called in a unit test context.
            file: Optional file path to use for setting the base path.
        """
        App._get_state_bridge().reset(unittest=unittest, file=file)
        App.init = False
        import miniworlds.base.manager.app_file_manager as app_file_manager

        app_file_manager.FileManager.clear_cache()

    @staticmethod
    def check_for_run_method():
        """
        Verifies that `.run()` is called in the user's main module.
        Prints a warning if it's not found (except in emscripten or notebooks).
        """
        try:
            content = App.get_platform().read_main_module()
            if content is not None and ".run(" not in content:
                    warnings.warn(
                        """[world_name].run() was not found in your code. 
                        This must be the last line in your code 
                        \ne.g.:\nworld.run()\n if your world-object is named world.""")
        except AttributeError:
            if not App.get_platform().is_web():
                logger.info(
                    "Skipping run() presence check because the main module could not be read"
                )

    def _output_start(self):
        """
        Outputs version info at app start (desktop only).
        """
        if not self.platform.is_web():
            version_str = self.platform.get_package_version("miniworlds")
            logger.info("Starting miniworlds window for version %s", version_str)

    def __init__(self, title, world):
        """
        Initializes the App and all its managers.

        Args:
            title: Title for the window.
            world: The initial world object to be run.
        """
        self.platform = platform_mod.PlatformAdapter()
        self._output_start()
        self.check_for_run_method()

        self.worlds_manager: "WorldsManager" = worlds_manager.WorldsManager(self)
        self.event_manager: "AppEventManager" = event_manager.AppEventManager(self)
        self.sound_manager: "SoundManager" = sound_manager.SoundManager(self)
        self.music_manager: "MusicManager" = music_manager.MusicManager(self)
        self.window: "Window" = window_mod.Window(title, self, self.worlds_manager, self.event_manager)

        self._quit = False
        self._unittest = False
        self._skip_frame_delay = os.getenv("MINIWORLDS_TEST_FAST") == "1"
        self._mainloop_started: bool = False
        self._exit_code: int = 0
        self.image = None
        self.repaint_areas: List = []

        self._get_state_bridge().bind_app(self, world, self.window)

        if self.get_path():
            self.path = self.get_path()

    async def run(self, image, fullscreen: bool = False, fit_desktop: bool = False, replit: bool = False):
        """
        Starts the app and enters the mainloop.

        Args:
            image: The background image to display.
            fullscreen: Whether to start in fullscreen mode.
            fit_desktop: Whether to adapt the window to desktop size.
            replit: Whether running in replit environment.
        """
        self.image = image
        self.window = cast(Window, self.window)
        self.window.fullscreen = fullscreen
        self.window.fit_desktop = fit_desktop
        self.window.replit = replit

        self.init_app()
        App.init = True
        self.prepare_mainloop()

        if not self._mainloop_started:
            await self.start_mainloop()
        else:
            for world in self.running_worlds:
                world.dirty = 1
                world.background.set_dirty("all", 2)

    def init_app(self):
        """
        Initializes global resources (e.g., image cache).
        """
        image_manager.ImageManager.cache_images_in_image_folder()

    def prepare_mainloop(self):
        """
        Prepares all world objects for drawing.
        """
        self.resize()
        for world in self.running_worlds:
            world.dirty = 1
            world.background.set_dirty("all", 2)

    async def start_mainloop(self):
        """
        Starts the main event loop.
        """
        self._mainloop_started = True
        finished_normally = False
        try:
            while not self._quit:
                await self._update()
            finished_normally = True
        finally:
            self._finalize_mainloop(finished_normally)

    def _finalize_mainloop(self, finished_normally: bool) -> None:
        self._mainloop_started = False
        if self._unittest:
            return

        self.platform.quit_display()
        if finished_normally and not self.platform.is_web():
            sys.exit(self._exit_code)

    async def _update(self):
        """
        A single iteration of the mainloop.
        Handles events, updates worlds, redraws screen.
        """
        self.event_manager.pygame_events_to_event_queue()

        if self.window.dirty:
            self.resize()

        if not self._quit:
            self.event_manager.handle_event_queue()
            await self.worlds_manager.reload_all_worlds()
            self.display_repaint()
            await self.platform.yield_mainloop()

    def set_running_world(self, world: Optional["World"]) -> None:
        self._get_state_bridge().set_running_world(world)

    def add_running_world(self, world: "World") -> None:
        self._get_state_bridge().add_running_world(world)

    def remove_running_world(self, world: "World") -> None:
        self._get_state_bridge().remove_running_world(world)

    def quit(self, exit_code=0):
        """
        Signals the mainloop to exit.

        Args:
            exit_code: Exit code to use when quitting.
        """
        self._exit_code = exit_code
        self._quit = True

    def register_path(self, path):
        """
        Registers the app path for relative resource access.

        Args:
            path: Path to the project directory.
        """
        self.path = path
        self._get_state_bridge().set_path(path)
        import miniworlds.base.manager.app_file_manager as app_file_manager

        app_file_manager.FileManager.clear_cache()

    def display_repaint(self):
        """
        Repaints the regions marked as dirty (called every frame).
        """
        self.platform.update_display(self.repaint_areas)
        self.repaint_areas = []

    def display_update(self):
        """
        Repaints the full display if it was marked dirty.

        Note:
            This could be merged with display_repaint and update_surface.
        """
        if self.window.dirty:
            self.window.dirty = 0
            self.add_display_to_repaint_areas()
            self.platform.update_display(self.repaint_areas)
            self.repaint_areas = []

    def add_display_to_repaint_areas(self):
        """
        Adds the full screen area to the repaint queue.
        """
        self.repaint_areas.append(pygame.Rect(0, 0, self.window.width, self.window.height))

    def resize(self):
        """
        Resizes the window surface and updates all layout-related components.
        """
        self.worlds_manager.recalculate_dimensions()
        self.window._update_surface()
        self.display_update()
