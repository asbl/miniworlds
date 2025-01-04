from typing import List, cast, Tuple
import pygame
import miniworlds.base.app as app
import miniworlds.base.window as window_mod
import miniworlds.worlds.world_base as base_world
from miniworlds.base.exceptions import MiniworldsError


class WorldsManager:
    def __init__(self, miniworlds_app: "app.App") -> None:
        self.worlds: List["base_world.BaseWorld"] = []
        self.total_width: int = 0
        self.total_height: int = 0
        self.app: "app.App" = miniworlds_app
        self.topleft : base_world.BaseWorld|None  = None
        self.worlds_total_height: int = 0
        self.worlds_total_width: int = 0

    def get_world_by_pixel(self, pixel_x: int, pixel_y: int):
        """Gets world by pixel coordinates."""
        for world in self.worlds:
            if world.rect.collidepoint((pixel_x, pixel_y)):
                return world
        return None

    def reload_all_worlds(self):
        """Called in mainloop, triggered 1/frame.

        If dirty, worlds are updated and repainted.
        """
        for world in self.worlds:
            if world.dirty:
                world.update()
                world.repaint()
                world.blit_surface_to_window_surface()

    def add_topleft(
        self, new_world: "base_world.BaseWorld"
    ) -> "base_world.BaseWorld":
        """Adds the topleft corner if it does not exist."""
        for world in self.worlds:
            if world.docking_position == "top_left":
                return self.get_topleft()
        self.topleft = new_world
        self.add_world(new_world, "top_left")
        return new_world

    def add_world(
        self, world: "base_world.BaseWorld", dock: str, size: int|None = None
    ) -> "base_world.BaseWorld":
        """Adds a new container

        Args:
            container (container.Container): The container
            dock (str): The position: "top_left", "right" or "bottom"
            size (int, optional): Size in pixels. Defaults to attribute
            `default_size`of container

        Raises:
            MiniworldsError: Raises error if container is already in
            world containers.

        Returns:
            container.Container: The container
        """
        if world not in self.worlds:
            world.docking_position = dock
            self.worlds.append(world)
            world.add_to_window(self.app, dock, size)
            for world in self.worlds:
                world.dirty = 1
            for world in self.app.running_worlds:
                for actor in world.actors:
                    actor.dirty = 1
        else:
            raise MiniworldsError("Container already in world.worlds")
        self.app.resize()
        return world

    def switch_world(self, new_world, reset = True, setup = True):
        #remove old world and stop events
        old_world = self.app.running_world
        old_world.stop()
        old_world.stop_listening()
        old_world.app.event_manager.event_queue.clear()
        #self.app.worlds_manager.switch_world(new_world)
        app.App.running_worlds.remove(old_world)
        app.App.running_world = new_world
        app.App.running_worlds.append(new_world)
        new_world._app = old_world._app
        # Start listening to new world
        new_world.init_display()
        new_world.is_running = True
        new_world._window = self.app.window
        if reset:
            new_world.reset()
        if setup:
            new_world.on_setup()
        new_world.background.set_dirty("all", 2)
        new_world.start_listening()

        self.app.image = new_world.image
        self.switch_container(old_world, new_world)
        #for world in self.worlds:
        #    if world != new_world:
        #        self.remove_world(world)
        self.app.prepare_mainloop()

    def worlds_right(self):
        """List of all containers with docking_position "right", 
        ordered by display-position"""
        return [self.topleft] + [
            world for world in self.worlds if world.docking_position == "right"
        ]

    def worlds_bottom(self):
        """List of all containers with docking_position "bottom",
        ordered by display-position"""
        return [self.topleft] + [
            world for world in self.worlds if world.docking_position == "bottom"
        ]
        
    def switch_container(
        self,
        container: "base_world.BaseWorld",
        new_container: "base_world.BaseWorld",
    ) -> "base_world.BaseWorld":
        """Switches a container (e.g. replace a world with another world)

        Args:
            container: The container which should be replaced
            new_container: The container which should be inserted
        """
        for i, world in enumerate(self.worlds):
            if world == container:
                dock = container.docking_position
                self.worlds[i] = new_container
                new_container.docking_position = dock
                if dock == "top_left":
                    self.topleft = new_container
                break
        self.update_containers()
        self.app.resize()
        return new_container

    def get_topleft(self) -> "base_world.BaseWorld":
        for container in self.worlds:
            if container.docking_position == "top_left":
                return container
        raise MiniworldsError("Container top_left is missing!")

    def containers_right(self):
        """List of all containers with docking_position "right", 
        ordered by display-position"""
        return [self.topleft] + [
            world for world in self.worlds if world.docking_position == "right"
        ]

    def containers_bottom(self):
        """List of all containers with docking_position "bottom",
        ordered by display-position"""
        return [self.topleft] + [
            world for world in self.worlds if world.docking_position == "bottom"
        ]

    def remove_world(self, world):
        """Removes a container and updates window."""
        if world in self.worlds:
            self.worlds.remove(world)
        for world in self.worlds:
            world.dirty = 1
        self.update_containers()
        self.app.resize()
        
    def reset(self):
        for world in self.worlds:
            world.clear()
            if world.docking_position != "top_left":
                self.remove_world(world)

    def update_containers(self):
        """updates container widths and heights if a container was changed"""
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
        """Recalculates container width"""
        containers_width: int = 0
        for container in self.worlds:
            if container.window_docking_position == "top_left":
                containers_width = container.camera.width
            elif container.window_docking_position == "right":
                containers_width += container.camera.width
        self.total_width = containers_width
        return self.total_width

    def recalculate_total_height(self) -> int:
        """Recalculates container height"""
        containers_height = 0
        for container in self.worlds:
            if container.window_docking_position == "top_left":
                containers_height = container.camera.height
            elif container.window_docking_position == "bottom":
                containers_height += container.camera.height
        self.total_height = containers_height
        return self.total_height


    def recalculate_dimensions(self) -> Tuple[int, int]:
        """Updates container sizes and recalculates dimensions"""
        self.update_containers()
        self.worlds_total_width = self.recalculate_total_width()
        self.worlds_total_height = self.recalculate_total_height()