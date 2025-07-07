from typing import List, cast, Tuple, TYPE_CHECKING
import pygame
import miniworlds.base.app as app

from miniworlds.base.exceptions import MiniworldsError

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod
    import miniworlds.actors.actor as actor_mod

class WorldsManager:
    def __init__(self, miniworlds_app: "app.App") -> None:
        self.worlds: List["worlds_mod.World"] = []
        self.total_width: int = 0
        self.total_height: int = 0
        self.app: "app.App" = miniworlds_app
        self.topleft : "worlds_mod.World"|None  = None
        self.worlds_total_height: int = 0
        self.worlds_total_width: int = 0

    def get_world_by_pixel(self, pixel_x: int, pixel_y: int):
        """Gets world by pixel coordinates."""
        for world in self.worlds:
            if world.camera.get_screen_rect().collidepoint((pixel_x, pixel_y)):
                return world
        return None

    async def reload_all_worlds(self):
        """Called in mainloop, triggered 1/frame.

        If dirty, worlds are updated and repainted.
        """
        for world in self.worlds:
            if world.dirty:
                await world.mainloop.update()
                world.mainloop.repaint()
                world.mainloop.blit_surface_to_window_surface()
                
    def add_topleft(
        self, new_world: "world_mod.World"
    ) -> "world_mod.World":
        """Adds the topleft corner if it does not exist."""
        for world in self.worlds:
            if world.layout.docking_position == "top_left":
                return self.get_topleft()
        self.topleft = new_world
        self.add_world(new_world, "top_left")
        return new_world

    def add_world(
            self,
            world: "world_mod.World",
            dock: str,
            size: int | None = None
    ) -> "world_mod.World":
        """Adds a new world to the layout and initializes it at the given docking position.

        Args:
            world: The world instance to add.
            dock: Docking position – one of "top_left", "right", or "bottom".
            size: Optional pixel size for docking (used for height or width depending on position).

        Returns:
            The world that was added.

        Raises:
            MiniworldsError: If the world is already in the layout.
        """
        if world in self.worlds:
            raise MiniworldsError("World already exists in worlds list.")

        # Set docking position and prepare camera
        world.layout.docking_position = dock
        world.layout._add_to_window(self.app, dock, size)

        # Set camera screen position based on docking
        if dock == "right":
            world.camera.screen_topleft = (self.app.window.width, 0)
            world.camera.height = self.app.window.height
            world.camera.width = size
        elif dock == "bottom":
            world.camera.screen_topleft = (0, self.app.window.height)
            world.camera.height = size or world.camera.height
            world.camera.width = self.app.window.width
        elif dock == "top_left":
            world.camera.screen_topleft = (0, 0)

        world.camera.disable_resize()
        frame = self.app.running_world.frame

        # Register world
        if world not in self.worlds:
            self.worlds.append(world)
        app.App.running_worlds.append(world)
        
        # Trigger world setup and state updates
        world.on_change()
        self.app.resize() # must be called before setup
        world.event_manager.setup_world()

        # Mark all worlds and their actors as dirty (to trigger redraw)
        world.camera.enable_resize()
        
        for w in self.app.running_worlds:
            for actor in w.actors:
                actor.dirty = 1
        if frame != 0:
            for w in self.worlds:
                w.dirty = 1
        return world      

    def _deactivate_world(self, world: "world_mod.World"):
        world.stop()
        world.stop_listening()
        world.app.event_manager.event_queue.clear()
        if world in app.App.running_worlds:
            app.App.running_worlds.remove(world)

    def _activate_world(self, world: "world_mod.World", reset: bool, setup: bool):
        app.App.running_world = world
        app.App.running_worlds.append(world)
        world._app = self.app
        world._window = self.app.window
        world.backgrounds_manager.init_display()
        world.is_running = True
        if reset:
            world.reset()
        if setup:
            world.event_manager.setup_world()
        world.background.set_dirty("all", 2)
        world.start_listening()

    def _finalize_world_switch(self, old_world, new_world):
        self.app.image = new_world.backgrounds_manager.image
        self._replace_world_in_worlds_list(old_world, new_world)
        self._update_all_worlds()
        self.app.resize()
        self.app.prepare_mainloop()

    def _replace_world_in_worlds_list(
            self,
            old_world: "world_mod.World",
            new_world: "world_mod.World",
    ) -> "world_mod.World":
        """intern: Replaces a world in the worlds list"""
        for i, world in enumerate(self.worlds):
            if world == old_world:
                dock = old_world.layout.docking_position
                self.worlds[i] = new_world
                new_world.layout.docking_position = dock
                if dock == "top_left":
                    self.topleft = new_world
                break
        return new_world

    def switch_world(self, new_world, reset = True, setup = True):
        #remove old world and stop events
        old_world = self.app.running_world
        self._deactivate_world(old_world)
        self._activate_world(new_world, reset, setup)
        self._finalize_world_switch(old_world, new_world)

    def worlds_right(self):
        """List of all worlds with docking_position "right", 
        ordered by display-position"""
        return [self.topleft] + [
            world for world in self.worlds if world.layout.docking_position == "right"
        ]

    def worlds_bottom(self):
        """List of all worlds with docking_position "bottom",
        ordered by display-position"""
        return [self.topleft] + [
            world for world in self.worlds if world.layout.docking_position == "bottom"
        ]

    def get_topleft(self) -> "world_mod.World":
        for world in self.worlds:
            if world.layout.docking_position == "top_left":
                return world
        raise MiniworldsError("World top_left is missing!")

    def remove_world(self, world: "world_mod.World"):
        """Removes a world and updates window."""
        if world in self.worlds:
            self.worlds.remove(world)
        for world in self.worlds:
            world.dirty = 1
        self._update_all_worlds()
        self.app.resize()
        
    def reset(self):
        for world in self.worlds:
            world.clear()
            if world.layout.docking_position != "top_left":
                self.remove_world(world)

    def _update_all_worlds(self):
        """updates all world widths and heights if a world was changed"""
        top_left = 0
        for world in self.worlds_right():
            if world:
                world.camera.screen_topleft = (top_left, world.camera.screen_topleft[1])
                top_left += world.camera.width
        top_left = 0
        for world in self.worlds_bottom():
            if world:
                world.camera.screen_topleft = (world.camera.screen_topleft[0], top_left)
                top_left += world.camera.height

    def recalculate_total_width(self) -> int:
        """Recalculates total width of all docked worlds."""
        total_width: int = 0
        for world in self.worlds:
            if world.layout.docking_position == "top_left":
                total_width = world.camera.width
            elif world.layout.docking_position == "right":
                total_width += world.camera.width
        self.total_width = total_width
        return self.total_width


    def recalculate_total_height(self) -> int:
        """Recalculates total height of all docked worlds."""
        total_height = 0
        for world in self.worlds:
            if world.layout.docking_position == "top_left":
                total_height = world.camera.height
            elif world.layout.docking_position == "bottom":
                total_height += world.camera.height
        self.total_height = total_height
        return self.total_height


    def recalculate_dimensions(self) -> Tuple[int, int]:
        """Updates container sizes and recalculates dimensions"""
        self._update_all_worlds()
        self.worlds_total_width = self.recalculate_total_width()
        self.worlds_total_height = self.recalculate_total_height()