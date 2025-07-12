from typing import Tuple, Union, Optional, List, cast, Callable
import miniworlds.actors.actor as actor_mod
import time
import asyncio

class MainloopManager:

    def __init__(self, world, app):
        self.world = world  
        self.app = app  
        self.reload_costumes_queue: list = []
    
    async def update(self):
        """The mainloop, called once per frame.

        Called in app.update() when reload_all_worlds is called.
        """
        if not self.world.is_running and self.world.frame != 0:
            self.world.event_manager.update()
            return
        start = 0
        if self.world.is_running or self.world.frame == 0:
            start = time.perf_counter()
            # Acting for all actors@static
            if self.world.frame > 0 and self.world.frame % self.world.tick_rate == 0:
                self.world.event_manager.act_all()
            self.world._collision_manager._handle_all_collisions()
            self.world.mouse._update_positions()
            if self.world.frame == 0:
                self.world.backgrounds._init_display()
            # run animations
            self.world.background.update()
            # update all costumes on current background
            self._update_all_costumes()
            self._tick_timed_objects()
            self.world.camera._update()
        self.world.frame += 1
        self.world.event_manager.update()
        elapsed = time.perf_counter() - start
        wait = max(0, (1 / self.world.fps) - elapsed)
        await asyncio.sleep(wait)
        
    def _update_all_costumes(self):
        """Updates the costumes of all actors in the world."""
        for actor in self.reload_costumes_queue:
            if actor.costume:
                actor.costume.update()
        self.reload_costumes_queue.clear()

        if hasattr(self.world, "_dynamic_actors"):
            for actor in self.world._dynamic_actors:
                if actor.costume:
                    actor.costume.update()

    def _tick_timed_objects(self):
        [obj.tick() for obj in self.world._timed_objects]

    def handle_event(self, event, data=None):
        """
        Event handling

        Args:
            event (str): The event which was thrown, e.g. "key_up", "act", "reset", ...
            data: The data of the event (e.g. ["S","s"], (155,3), ...
        """
        self.world.event_manager.handler.handle_event(event, data)

    def repaint(self):
        self.world.background.repaint()  # called 1/frame in container.repaint()

    def blit_surface_to_window_surface(self):
        self.app.window.surface.blit(self.world.background.surface, self.world.camera.screen_rect)

    def dirty_all(self):
        for actor in self.world.actors:
            actor.dirty = 1