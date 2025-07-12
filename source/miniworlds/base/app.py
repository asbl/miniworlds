import __main__
import os
import sys
import warnings
import asyncio

import pygame

from typing import List, Optional, TYPE_CHECKING, cast
from importlib.metadata import version, PackageNotFoundError

import miniworlds.appearances.managers.image_manager as image_manager
import miniworlds.base.manager.app_event_manager as event_manager
import miniworlds.base.manager.app_worlds_manager as worlds_manager
import miniworlds.base.manager.app_music_manager as music_manager
import miniworlds.base.manager.app_sound_manager as sound_manager
import miniworlds.base.window as window_mod
from miniworlds.base.window import Window

if TYPE_CHECKING:
    from miniworlds.base.manager.app_event_manager import AppEventManager
    from miniworlds.base.manager.app_worlds_manager import WorldsManager
    from miniworlds.base.manager.app_music_manager import MusicManager
    from miniworlds.base.manager.app_sound_manager import SoundManager
    from miniworlds.worlds.world import World


class App:
    """
    Main application class for Miniworlds.
    Created automatically when `world.run()` is called for the first time.

    Raises:
        NoRunError: If `run()` is not called from the main module.
    """

    running_world: Optional["World"] = None
    running_worlds: List["World"] = []
    path: str = ""
    running_app: Optional["App"] = None
    init: bool = False
    window: Optional["Window"] = None

    @staticmethod
    def reset(unittest=False, file=None):
        """
        Resets all app globals.

        Args:
            unittest: Whether the reset is being called in a unit test context.
            file: Optional file path to use for setting the base path.
        """
        App.running_world = None
        App.running_worlds = []
        App.path = None
        App.running_app = None
        App.init = False
        if file and unittest:
            App.path = os.path.dirname(file)

    @staticmethod
    def check_for_run_method():
        """
        Verifies that `.run()` is called in the user's main module.
        Prints a warning if it's not found (except in emscripten or notebooks).
        """
        try:
            with open(__main__.__file__) as f:
                if ".run(" not in f.read():
                    warnings.warn(
                        """[world_name].run() was not found in your code. 
                        This must be the last line in your code 
                        \ne.g.:\nworld.run()\n if your world-object is named world.""")
        except AttributeError:
            if sys.platform != 'emscripten':
                print("Can't check if run() is present (This may happen in Jupyter Notebooks. Resuming...)")

    def _output_start(self):
        """
        Outputs version info at app start (desktop only).
        """
        if sys.platform != 'emscripten':
            try:
                version_str = version("miniworlds")
            except PackageNotFoundError:
                version_str = "unknown"

            print(f"Show new miniworlds v.{version_str} Window")

    def __init__(self, title, world):
        """
        Initializes the App and all its managers.

        Args:
            title: Title for the window.
            world: The initial world object to be run.
        """
        self._output_start()
        self.check_for_run_method()

        self.worlds_manager: "WorldsManager" = worlds_manager.WorldsManager(self)
        self.event_manager: "AppEventManager" = event_manager.AppEventManager(self)
        self.sound_manager: "SoundManager" = sound_manager.SoundManager(self)
        self.music_manager: "MusicManager" = music_manager.MusicManager(self)
        self.window: "Window" = window_mod.Window(title, self, self.worlds_manager, self.event_manager)

        self._quit = False
        self._unittest = False
        self._mainloop_started: bool = False
        self._exit_code: int = 0
        self.image = None
        self.repaint_areas: List = []

        App.running_app = self
        App.running_world = world
        App.running_worlds.append(world)
        App.window = self.window

        if App.path:
            self.path = App.path

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
        while not self._quit:
            await self._update()

        if not self._unittest:
            pygame.display.quit()
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
            await asyncio.sleep(0)  # important: allows event loop to yield

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
        App.path = path

    def display_repaint(self):
        """
        Repaints the regions marked as dirty (called every frame).
        """
        pygame.display.update(self.repaint_areas)
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
            pygame.display.update(self.repaint_areas)
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
