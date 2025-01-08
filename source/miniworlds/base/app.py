import __main__
import os
import sys
import warnings
import asyncio


import pygame
from typing import List, cast, Optional

import miniworlds.appearances.managers.image_manager as image_manager
import miniworlds.base.manager.app_event_manager as event_manager
import miniworlds.base.manager.app_worlds_manager as worlds_manager
import miniworlds.base.manager.app_music_manager as music_manager
import miniworlds.base.manager.app_sound_manager as sound_manager
import miniworlds.base.window as window_mod
import miniworlds.worlds.world as world_mod


class App:
    """The class app contains the game itself. It's created the first time you call world.run().

    Raises:
        NoRunError: After running the program, the source of the main module is checked.
            If it does not contain a run() method (e.g. world.run()), this error is raised.
    """

    running_world: Optional["world_mod.World"] = None
    running_worlds: List["world_mod.World"] = []
    path: str = ""
    running_app: Optional["App"] = None
    init: bool = False
    window: Optional["window_mod.Window"] = None

    @staticmethod
    def reset(unittest=False, file=None):
        App.running_world = None
        App.running_worlds = []
        App.path = None
        App.running_app = None
        App.init = False  # is pygame.init called?
        if file and unittest:
            App.path = os.path.dirname(file)

    @staticmethod
    def check_for_run_method():
        try:
            with open(__main__.__file__) as f:
                if ".run(" not in f.read():
                    warnings.warn(
                        """[world_name].run() was not found in your code. 
                        This must be the last line in your code 
                        \ne.g.:\nworld.run()\n if your world-object is named world.""")
        except AttributeError:
            if sys.platform != 'emscripten':
                print("can't check if run() is present (This can happen if you are using jupyter notebooks. Resuming)")

    def _output_start(self):
        if sys.platform != 'emscripten':
            import pkg_resources # type: ignore
            version = pkg_resources.require("miniworlds")[0].version
            print("Show new miniworlds v.{0} Window".format(version))

    def __init__(self, title):
        self._output_start()
        self.check_for_run_method()
        self.worlds_manager: "worlds_manager.WorldsManager" = worlds_manager.WorldsManager(self)
        self._quit = False
        self.image = None
        self._unittest = False
        self._mainloop_started: bool = False
        self.event_manager: "event_manager.AppEventManager" = event_manager.AppEventManager(self)
        self.sound_manager: "sound_manager.SoundManager" = sound_manager.SoundManager(self)
        self.music_manager: "music_manager.MusicManager" = music_manager.MusicManager(self)
        self.window: "window_mod.Window" = window_mod.Window(title, self.worlds_manager, self.event_manager)
        App.running_app = self
        App.window = self.window
        self._exit_code: int = 0
        if App.path:
            self.path = App.path
        self.repaint_areas: List = []


    async def run(self, image, fullscreen: bool = False, fit_desktop: bool = False, replit: bool = False):
        """
        runs the main_loop
        Args:
            image: The background image
            fullscreen: True or False
            fit_desktop: True or false
            replit: True or false
        """
        self.image = image
        self.window = cast(window_mod.Window, self.window)
        self.window.fullscreen = fullscreen
        self.window.fit_desktop = fit_desktop
        self.window.replit = replit
        print("...")
        # Start the main-loop
        self.init_app()
        print("init completed")
        self.prepare_mainloop()
        print("mainloop prepared")
        if not self._mainloop_started:
            if sys.platform == 'emscripten':
                await self.start_mainloop();
            else:
                asyncio.run(self.start_mainloop());
        else:
            for world in self.running_worlds:
                world.dirty = 1
                world.background.set_dirty("all", 2)

    def init_app(self):
        image_manager.ImageManager.cache_images_in_image_folder()

    def prepare_mainloop(self):
        self.resize()
        for world in self.running_worlds:
            world.dirty = 1
            world.background.set_dirty("all", 2)

    async def start_mainloop(self):
        self._mainloop_started = True
        print("start mainloop")
        while not self._quit:
            await self._update()
        if not self._unittest:
            pygame.display.quit()
            sys.exit(self._exit_code)

    async def _update(self):
        """This is the mainloop. This function is called until the app quits.
        """
        print("update")
        self.event_manager.pygame_events_to_event_queue()
        if self.window.dirty:
            self.resize()
        if not self._quit:
            self.event_manager.handle_event_queue()
            await self.worlds_manager.reload_all_worlds()
            self.display_repaint()
            await asyncio.sleep(0) # do not forget that one, it must be called on every frame

    def quit(self, exit_code=0):
        self._exit_code = exit_code
        self._quit = True

    def register_path(self, path):
        self.path = path
        App.path = path

    def display_repaint(self):
        """Called 1/frame - Draws all repaint rectangles and resets the repaint areas."""
        pygame.display.update(self.repaint_areas)
        self.repaint_areas = []
        
    def display_update(self):
        """Updates the display
        @todo: Can be merged into display_repaint and update_surface
        """
        if self.window.dirty:
            self.window.dirty = 0
            self.add_display_to_repaint_areas()
            pygame.display.update(self.repaint_areas)
            self.repaint_areas = []
            
    def add_display_to_repaint_areas(self):
        self.repaint_areas.append(pygame.Rect(0, 0, self.window.width, self.window.height))
        
    def resize(self):
        """Resizes the window:
        1. Recalculates the container dimensions
        2. updates own surface
        3. updates display
        """
        self.worlds_manager.recalculate_dimensions()
        self.window._update_surface()
        self.display_update()