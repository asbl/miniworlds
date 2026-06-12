from typing import Tuple, Union, Optional, List, cast, Callable
import miniworlds.actors.actor as actor_mod
import time
import asyncio

class MainloopManager:

    def __init__(self, world, app):
        self.world = world
        self.app = app
        self.reload_costumes_queue: list = []
        self._dialog_was_visible = False
    
    async def update(self):
        """The mainloop, called once per frame.

        Called in app.update() when reload_all_worlds is called.

        Returns:
            The remaining frame budget in seconds (for the app-level frame
            pacing), or None if the world is not running. The frame wait
            itself happens once per app frame in App._update, not per world:
            awaiting it here would multiply the frame delay by the number of
            docked worlds (e.g. world + toolbar).
        """
        if not self.world.is_running and self.world.frame != 0:
            self.world.event_manager.update()
            return None
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
        return max(0, (1 / self.world.fps) - elapsed)
        
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
        for obj in self.world._timed_objects:
            obj.tick()

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
        background = self.world.background
        draw_overlay = getattr(self.world, "_draw_debug_overlay", None)
        active_dialog = getattr(self.world, "_active_dialog", None)
        dialog_visible = active_dialog is not None and getattr(active_dialog, "is_open", False)
        pending_rects = getattr(background, "_pending_window_rects", None)
        if pending_rects is None or callable(draw_overlay) or dialog_visible or self._dialog_was_visible:
            # Overlay/dialog frames are repainted as a whole anyway.
            self.app.window.surface.blit(background.surface, self.world.camera.screen_rect)
        else:
            # Copy only the areas that were redrawn this frame. Blitting the
            # whole camera surface every frame is a large fixed per-frame cost
            # (significant on slow targets such as Pyodide/wasm).
            offset_x, offset_y = self.world.camera.screen_topleft
            for rect in pending_rects:
                self.app.window.surface.blit(
                    background.surface, rect, rect.move(-offset_x, -offset_y)
                )
        if pending_rects is not None:
            pending_rects.clear()
        if callable(draw_overlay):
            draw_overlay(self.app.window.surface)
        if dialog_visible:
            active_dialog.draw(self.app.window.surface)
        if dialog_visible or self._dialog_was_visible:
            # The display only flushes dirty actor rects. A modal dialog is
            # drawn independently of actors, so repaint the whole display
            # while it is shown and once more after it closes.
            self.app.add_display_to_repaint_areas()
        self._dialog_was_visible = dialog_visible

    def dirty_all(self):
        for actor in self.world.actors:
            actor.dirty = 1
