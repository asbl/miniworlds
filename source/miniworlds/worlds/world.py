import math
import pygame
import sys
import asyncio
import time
from typing import Tuple, Union, Optional, List, cast, Callable, Set

import miniworlds.appearances.appearance as appearance
import miniworlds.appearances.background as background_mod
import miniworlds.appearances.backgrounds_manager as backgrounds_manager
import miniworlds.base.app as app
import miniworlds.worlds.world_base as world_base
import miniworlds.worlds.manager.collision_manager as coll_manager
import miniworlds.worlds.manager.event_manager as event_manager
import miniworlds.worlds.manager.mouse_manager as mouse_manager
import miniworlds.worlds.manager.music_manager as world_music_manager
import miniworlds.worlds.manager.layout_manager as layout_manager
import miniworlds.worlds.manager.draw_manager as draw_manager
import miniworlds.worlds.manager.data_manager as data_manager
import miniworlds.worlds.manager.mainloop_manager as mainloop_manager
import miniworlds.worlds.manager.sound_manager as world_sound_manager
import miniworlds.worlds.manager.position_manager as position_manager
import miniworlds.worlds.manager.camera_manager as world_camera_manager
import miniworlds.worlds.data.export_factory as export_factory
import miniworlds.worlds.data.import_factory as import_factory
import miniworlds.worlds.world_background_facade as world_background_facade
import miniworlds.worlds.world_initialization_facade as world_initialization_facade
import miniworlds.worlds.world_runtime_facade as world_runtime_facade
import miniworlds.positions.rect as world_rect
import miniworlds.actors.actor as actor_mod
import miniworlds.tools.timer as timer
import miniworlds.base.app as app_mod

from miniworlds.base.exceptions import (
    WorldArgumentsError,
)


class World(world_base.WorldBase):
    """Base world class for pixel-based scenes.

    A world owns the shared runtime state: actors, backgrounds, input
    handling, and event dispatch.

    Notes:
        - Actor positions in a `World` are pixel coordinates.
        - New actors start at their top-left position unless their origin is
          switched to `center`.
        - Sprite overlap is used for collision checks by default.

    Examples:
        Create a world directly:
            from miniworlds import World

            world = World(300, 200)
            world.run()

        Subclass a world and configure setup values:
            import miniworlds

            class MyWorld(miniworlds.World):
                def on_setup(self):
                    self.columns = 300
                    self.rows = 200
    """

    def _validate_parameters(self, x, y):
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError(
                f"World(x, y) x and y must be int or float; Got ({type(x)}, {type(y)})"
            )

    def __init__(
        self,
        x: Union[int, Tuple[int, int]] = 400,
        y: int = 400,
        ):
        """Initializes the world and all internal managers needed for runtime operation."""
        self._initialization_facade = world_initialization_facade.WorldInitializationFacade(self)
        self._get_initialization_facade().initialize_pre_base_state(x, y)
        super().__init__()
        self._get_initialization_facade().initialize_post_base_state()


    def _get_initialization_facade(
        self,
    ) -> world_initialization_facade.WorldInitializationFacade:
        facade = getattr(self, "_initialization_facade", None)
        if facade is None:
            facade = world_initialization_facade.WorldInitializationFacade(self)
            self._initialization_facade = facade
        return facade

    def _get_background_facade(self) -> world_background_facade.WorldBackgroundFacade:
        facade = getattr(self, "_background_facade", None)
        if facade is None:
            facade = world_background_facade.WorldBackgroundFacade(self)
            self._background_facade = facade
        return facade

    def _get_runtime_facade(self) -> world_runtime_facade.WorldRuntimeFacade:
        facade = getattr(self, "_runtime_facade", None)
        if facade is None:
            facade = world_runtime_facade.WorldRuntimeFacade(self)
            self._runtime_facade = facade
        return facade

    @property
    def layout(self):
        """Backward-compatible docking API for older example code.

        The actual layout manager remains internal on ``world._layout``. Public
        docking helpers continue to live on ``world.camera`` and are exposed
        here as a compatibility alias for existing teaching material.
        """
        return self.camera

    def contains_position(self, pos):
        """Checks if position is in the world.

        Returns:
            True, if Position is in the world.
        """
        return self.sensor_manager.contains_position(pos)

    def contains_rect(self, rect: Union[Tuple[int, int, int, int], pygame.Rect]):
        """
        Returns True if the entire rectangle is fully inside the world.

        Useful when ensuring that an object is completely within bounds.
        """
        return self.sensor_manager.contains_rect_all(rect)

    def contains_rect_any(self, rect: Union[Tuple[int, int, int, int], pygame.Rect]):
        """
        Returns True if any part of the rectangle is inside the world.

        Useful when ensuring that an object is completely within bounds.
        """
        return self.sensor_manager.contains_rect_any_(rect)

    @property
    def tick_rate(self) -> int:
        """How often world logic runs relative to the frame loop.

        A value of `1` runs game logic every frame. A value of `30` runs it
        every 30th frame.

        Example:
            from miniworlds import World

            world = World(120, 210)
            world.fps = 60
            world.tick_rate = 3
            world.run()
        """
        return self._tick_rate

    @tick_rate.setter
    def tick_rate(self, value: int):
        self._tick_rate = value

    @property
    def fps(self) -> int:
        """Frames per second of the render loop.

        This controls redraw frequency. Logic frequency can be tuned
        independently via `world.tick_rate`.

        Example:
            world.fps = 24
            world.tick_rate = 2
        """
        return self._fps

    @fps.setter
    def fps(self, value: int):
        self._fps = value

    @property
    def world_size_x(self) -> int:
        """
        Gets the horizontal size of the world in pixels.

        This usually equals the camera's world width.

        Returns:
            Width of the world in pixels.

        Example:
            >>> print(world.world_size_x)
            800
        """
        return self.camera.world_size_x

    @world_size_x.setter
    def world_size_x(self, value: int) -> None:
        """
        Sets the horizontal size of the world in pixels.

        Args:
            value: New width in pixels.

        Example:
            >>> world.world_size_x = 1024
        """
        self.camera.world_size_x = value


    @property
    def world_size_y(self) -> int:
        """
        Gets the vertical size of the world in pixels.

        Returns:
            Height of the world in pixels.
        """
        return self.camera.world_size_y

    @world_size_y.setter
    def world_size_y(self, value: int) -> None:
        """
        Sets the vertical size of the world in pixels.

        Args:
            value: New height in pixels.
        """
        self.camera.world_size_y = value

    @property
    def columns(self) -> int:
        """
        Gets the number of horizontal pixels (columns) visible in the world.

        Returns:
            The width of the camera view in pixels.
        """
        return self.camera.width

    @columns.setter
    def columns(self, value: int) -> None:
        """
        Sets the number of columns and adjusts the internal world size accordingly.

        Args:
            value: New width in pixels.

        Example:
            >>> world.columns = 640
        """
        self.set_columns(value)

    def set_columns(self, value: int) -> None:
        """
        Internal method to set columns and sync world width.

        Args:
            value: New column count (width in pixels).
        """
        self.camera.width = value
        self.world_size_x = value


    @property
    def rows(self) -> int:
        """
        Gets the number of vertical pixels (rows) visible in the world.

        Returns:
            The height of the camera view in pixels.
        """
        return self.camera.height

    @rows.setter
    def rows(self, value: int) -> None:
        """
        Sets the number of rows and adjusts the internal world size accordingly.

        Args:
            value: New height in pixels.

        Example:
            >>> world.rows = 480
        """
        self.set_rows(value)

    def set_rows(self, value: int) -> None:
        """
        Internal method to set rows and sync world height.

        Args:
            value: New row count (height in pixels).
        """
        self.camera.height = value
        self.world_size_y = value

    @property
    def size(self) -> Tuple[int, int]:
        """
        Gets the world size as a tuple (width, height), in pixels.

        Returns:
            A tuple representing the world size in pixels.

        Example:
            >>> w, h = world.size
            >>> print(f\"World is {w}x{h} pixels large\")
        """
        return self.world_size_x, self.world_size_y


    @size.setter
    def size(self, value: Tuple[int, int]) -> None:
        """
        Sets the size of the world in pixels.

        This updates both the internal world size and the camera dimensions.

        Args:
            value: A tuple (width, height) representing the new world size.

        Example:
            >>> world.size = (800, 600)
        """
        width, height = value
        self.world_size_x = width
        self.world_size_y = height
        self.camera.width = width
        self.camera.height = height


    @property
    def background(self) -> background_mod.Background:
        """
        Returns the currently active background.

        This property delegates to `get_background()`.

        Returns:
            The currently active Background object.

        Example:
            >>> current = world.background
            >>> print(current)
        """
        return self._get_background_facade().background

    @background.setter
    def background(self, source: Union[str, Tuple[int, int, int], appearance.Appearance]) -> None:
        """
        Sets the world background either via an Appearance object or image/color source.

        If an Appearance is provided, it is directly set.
        If a file path or color is provided, it is added as a new background and activated.

        Args:
            source: Either an Appearance object, a color tuple (e.g. (255, 0, 0)), or a file path string.

        Raises:
            FileNotFoundError: If the image file does not exist.
            FileExistsError: If the background already exists.

        Example:
            >>> world.background = (0, 0, 0)                # black
            >>> world.background = \"images/background.png\"  # from image file
            >>> world.background = my_appearance            # custom Appearance
        """
        self._get_background_facade().set_background_property(source)

    def get_background(self) -> background_mod.Background:
        """
        Returns the current active background from the backgrounds manager.

        Returns:
            The current Background object.

        Example:
            >>> bg = world.get_background()
        """
        return self._get_background_facade().background


    def switch_background(
        self, background: Union[int, appearance.Appearance]
    ) -> background_mod.Background:
        """
        Switches the current background to a specified one.

        You can switch by index or directly using an `Appearance` object.
        If you pass -1 as index, it will switch to the next available background in the list.

        Args:
            background: Index of the background to switch to, or an Appearance instance.
                        Use -1 to switch to the next background in order.

        Returns:
            The new active Background object.

        Raises:
            FileNotFoundError: If the background image file is not found.

        Example:
            >>> world.add_background(\"images/1.png\")
            >>> world.add_background(\"images/2.png\")
            >>> world.switch_background(1)  # switches to second background

        Examples:

            Switch between different backgrounds:

            .. code-block:: python

                from miniworlds import *

                world = World()
                actor = Actor()

                world.add_background("images/1.png")
                world.add_background((255, 0, 0, 255))
                world.add_background("images/2.png")

                @timer(frames = 40)
                def switch():
                    world.switch_background(0)

                @timer(frames = 80)
                def switch():
                    world.switch_background(1)

                @timer(frames = 160)
                def switch():
                    world.switch_background(2)

                world.run()

            Output:

            .. image:: ../_images/switch_background.png
                :width: 100%
                :alt: Switch background
        """
        return self._get_background_facade().switch_background(background)

    def remove_background(self, background: Optional[Union[int, appearance.Appearance]] = None) -> None:
        """
        Removes a background from the world.

        If no argument is provided, the last added background will be removed.
        You can also remove a specific background by passing its index or Appearance object.

        Args:
            background: Either an integer index (e.g. 0) or an Appearance object. 
                        If None, the most recently added background is removed.

        Example:
            >>> world.remove_background()              # removes last background
            >>> world.remove_background(0)            # removes background at index 0
            >>> world.remove_background(my_background)  # removes specific Appearance object
        """
        self._get_background_facade().remove_background(background)


    def set_background(self, source: Union[str, Tuple[int, int, int]]) -> background_mod.Background:
        """
        Sets a new background and replaces the current active background.

        If multiple backgrounds already exist, this will override the active one with the new background.
        The source can be either an image path or a color tuple.

        Args:
            source: A string path to an image (e.g. "images/bg.png") or an RGB(A) color tuple (e.g. (0, 0, 255)).

        Returns:
            The newly created Background object that was set as active.

        Raises:
            FileNotFoundError: If the image file cannot be found.

        Example:
            >>> world.set_background("images/sky.png")
            >>> world.set_background((30, 30, 30))  # dark gray
        """
        return self._get_background_facade().set_background(source)

    def add_background(self, source: Union[str, Tuple[int, int, int]]) -> background_mod.Background:
        """
        Adds a new background to the world and sets it as the active one.

        The source can be either a file path (image) or a solid color in RGB(A) format.

        Args:
            source: Either a path to an image file (e.g. "images/bg.png") or an RGB/RGBA color tuple (e.g. (0, 0, 255)).

        Returns:
            The newly created Background object.

        Raises:
            FileNotFoundError: If the image file does not exist.

        Example:
            >>> world.add_background((255, 0, 0))               # red background
            >>> world.add_background("images/background.png")  # image background
        """
        return self._get_background_facade().add_background(source)

    def start(self) -> None:
        """
        Starts or resumes the world.

        Sets the internal running flag to True, allowing the world to continue updating and processing events.

        Example:
            >>> world.start()
        """
        self._get_runtime_facade().start()


    def stop(self, frames: int = 0) -> None:
        """
        Stops the world immediately or after a delay in frames.

        Args:
            frames: Number of frames to wait before stopping. If 0, stops immediately.

        Example:
            >>> world.stop()         # stops immediately
            >>> world.stop(frames=5) # stops after 5 frames
        """
        self._get_runtime_facade().stop(frames)

    def run(
        self,
        fullscreen: bool = False,
        fit_desktop: bool = False,
        replit: bool = False,
        event: Optional[str] = None,
        data: Optional[object] = None,
    ) -> None:
        """
        Starts the main application loop of the Miniworlds engine.

        This should be called once at the end of a Miniworlds program. It prepares and starts:
        - The main loop
        - Event handling
        - Rendering
        - Actor updates
        - Asynchronous compatibility (e.g. for REPLs and Jupyter)

        Args:
            fullscreen: If True, the game launches in fullscreen mode.
            fit_desktop: If True, window size adapts to desktop resolution.
            replit: Set True if running in a Replit environment (special adjustments).
            event: Optional event name to queue at startup (e.g. \"start\", \"setup\").
            data: Optional data to include with the startup event.

        Example:
            >>> world = World(800, 600)
            >>> world.run(fullscreen=False, event=\"setup\")

        Notes:
            Automatically detects and handles running event loops (e.g. in Jupyter).
        """
        self._get_runtime_facade().run(
            fullscreen=fullscreen,
            fit_desktop=fit_desktop,
            replit=replit,
            event=event,
            data=data,
        )


    def is_in_world(self, position: Tuple[float, float]) -> bool:
        """
        Checks whether a given world position lies within the world's boundaries.

        Args:
            position: A tuple (x, y) representing a position in world coordinates.

        Returns:
            True if the position is inside the world bounds, False otherwise.

        Example:
            >>> world.size = (800, 600)
            >>> world.is_in_world((100, 100))
            True
            >>> world.is_in_world((900, 100))
            False
        """
        return self._get_runtime_facade().is_in_world(position)

    def send_message(self, message: str, data: Optional[object] = None) -> None:
        """
        Sends a broadcast message to the world and all actors.

        The message is dispatched through the event system and can be handled
        by any registered method in the world or its actors. When `data` is
        provided, handlers registered with `@register_message("...")` receive
        that payload while generic `on_message` handlers still receive the
        message name.

        Args:
            message: The name of the message/event to send.
            data: Optional payload for handlers registered to this message.

        Example:
            >>> world.send_message(\"explode\", {\"power\": 10})
        """
        self._get_runtime_facade().send_message(message, data)

    def switch_world(self, new_world: "World", reset: bool = False) -> None:
        """Switch the active scene to another world.

        Args:
            new_world: The world that should become active.
            reset: If `True`, the new world is reset before it starts.
        """
        self._get_runtime_facade().switch_world(new_world, reset)

    def load_world_from_db(self, file: str) -> "World":
        """Load a saved world from a sqlite database file and activate it.

        Args:
            file: Path to the sqlite database file.

        Returns:
            The loaded world instance.
        """
        return self._get_runtime_facade().load_world_from_db(file)

    def load_actors_from_db(
        self, file: str, actor_classes: list[type[actor_mod.Actor]]
    ) -> list[actor_mod.Actor]:
        """Load actors from a sqlite database file into the current world.

        Args:
            file: Path to the sqlite database file.
            actor_classes: Actor classes that may be recreated from the file.

        Returns:
            A list with the recreated actors.
        """
        return self._get_runtime_facade().load_actors_from_db(file, actor_classes)

    def save_to_db(self, file: str) -> None:
        """Save the current world and its actors to a sqlite database file.

        Args:
            file: Path to the sqlite database file that should be written.
        """
        return self._get_runtime_facade().save_to_db(file)


    def quit(self, exit_code: int = 0) -> None:
        """
        Immediately quits the application and closes the game window.

        Args:
            exit_code: Exit code returned by the application. Defaults to 0.

        Example:
            >>> world.quit()
        """
        self._get_runtime_facade().quit(exit_code)

    def reset(self):
        """Resets the world
        Creates a new world with init-function - recreates all actors and actors on the world.

        Examples:

            Restarts flappy the bird game after collision with pipe:

            .. code-block:: python

              def on_sensing_collision_with_pipe(self, other, info):
                  self.world.is_running = False
                  self.world.reset()
        """
        self._get_runtime_facade().reset()
            
    def _clear(self) -> None:
        """
        Clears the world's state: event queue, all backgrounds, and all actors.

        This method is typically used during a world reset.

        Example:
            >>> world.clear()
        """
        self._get_runtime_facade().clear()

        
    def get_from_pixel(self, position: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Converts a screen pixel position into a valid world position if inside bounds.

        In PixelWorlds, this returns the position directly. In TiledWorlds, this might
        return a tile coordinate instead (override if needed).

        Args:
            position: A screen pixel coordinate (x, y)

        Returns:
            The same position if it lies inside the world, else None.

        Example:
            >>> world.get_from_pixel((100, 50))
            (100, 50)
        """
        return self._get_runtime_facade().get_from_pixel(position)


    def to_pixel(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Converts a world position to a screen pixel position.

        In PixelWorlds, this is an identity function. In TiledWorlds, override this.

        Args:
            position: World coordinate (x, y)

        Returns:
            Pixel coordinate (x, y)

        Example:
            >>> world.to_pixel((5, 8))
            (5, 8)
        """
        return self._get_runtime_facade().to_pixel(position)


    def on_setup(self) -> None:
        """
        Hook method to define initial setup logic when the world is created.

        Override this in subclasses or register via `@world.register`.

        Example:
            >>> def on_setup():
            ...     actor = Actor()
        """
        pass


    @property
    def has_background(self) -> bool:
        """
        Returns True if the world has at least one background appearance.

        Example:
            >>> if world.has_background:
            ...     print(\"Background is set\")
        """
        return self._get_background_facade().has_background()

    def detect_actors(self, position: Tuple[float, float]) -> List["actor_mod.Actor"]:
        """Gets all actors which are found at a specific position (in global world coordinates)

        Args:
            position: Position, where actors should be searched.

        Returns:
            A list of actors

        Examples:

          Get all actors at mouse position:

          .. code-block:: python

              position = world.mouse.get_position()
              actors = world.get_actors_from_pixel(position)

        """
        # overwritten in tiled_sensor_manager
        return self._get_runtime_facade().detect_actors(position)

    def get_actors_from_pixel(self, pixel: Tuple[float, float]) -> List[actor_mod.Actor]:
        """
        Returns a list of all actors located at the given screen pixel position.

        This checks whether each actor's screen-rect overlaps with the given pixel.

        Args:
            pixel: A tuple (x, y) representing the screen pixel.

        Returns:
            A list of Actor instances under the given pixel.

        Example:
            >>> actors = world.get_actors_from_pixel((120, 80))
            >>> for actor in actors:
            ...     print(actor.name)
        """
        return self._get_runtime_facade().get_actors_from_pixel(pixel)

    @staticmethod
    def distance_to(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """
        Calculates the Euclidean distance between two positions.

        Args:
            pos1: First position (x, y)
            pos2: Second position (x, y)

        Returns:
            The distance as a float.

        Example:
            >>> World.distance_to((0, 0), (3, 4))
            5.0
        """
        return world_runtime_facade.WorldRuntimeFacade.distance_to(pos1, pos2)

    def direction_to(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """
        Calculates the angle from pos1 to pos2 in degrees.

        Args:
            pos1: Starting position (x, y)
            pos2: Target position (x, y)

        Returns:
            Angle in degrees between the two points.

        Example:
            >>> world.direction_to((0, 0), (0, 1))
            90.0
        """
        return world_runtime_facade.WorldRuntimeFacade.direction_to(pos1, pos2)