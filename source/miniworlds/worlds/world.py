import math
import warnings
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
import miniworlds.worlds.world_background_facade as world_background_facade
import miniworlds.worlds.world_initialization_facade as world_initialization_facade
import miniworlds.worlds.world_runtime_facade as world_runtime_facade
import miniworlds.worlds.dialog as dialog_mod
import miniworlds.positions.rect as world_rect
import miniworlds.actors.actor as actor_mod
import miniworlds.tools.timer as timer
import miniworlds.base.app as app_mod
import miniworlds.base.api_validation as api_validation

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

    @staticmethod
    def _type_name(value) -> str:
        return api_validation.type_name(value)

    @staticmethod
    def _with_try_hint(message: str, example: str | None = None) -> str:
        return api_validation.with_try_hint(message, example)

    @staticmethod
    def _ensure_bool(value, parameter_name: str) -> None:
        api_validation.ensure_bool(
            value,
            parameter_name,
            World._with_try_hint,
            f"{parameter_name} = True",
        )

    @staticmethod
    def _ensure_real(value, parameter_name: str) -> None:
        api_validation.ensure_real(
            value,
            parameter_name,
            World._with_try_hint,
            f"{parameter_name} = 10",
        )

    @staticmethod
    def _ensure_int(value, parameter_name: str) -> None:
        api_validation.ensure_int(
            value,
            parameter_name,
            World._with_try_hint,
            f"{parameter_name} = 1",
        )

    @staticmethod
    def _ensure_non_empty_str(value, parameter_name: str) -> None:
        if not isinstance(value, str):
            raise TypeError(
                f"{parameter_name} must be str, got {type(value).__name__}: {value!r}"
            )
        if not value.strip():
            raise ValueError(f"{parameter_name} must not be empty")

    @classmethod
    def _ensure_position_tuple(cls, value, parameter_name: str) -> None:
        api_validation.ensure_position_tuple(
            value,
            parameter_name,
            cls._ensure_real,
            cls._with_try_hint,
        )

    @classmethod
    def _ensure_dimension(cls, value, parameter_name: str) -> None:
        cls._ensure_real(value, parameter_name)
        if value <= 0:
            raise ValueError(f"{parameter_name} must be > 0, got {value}")

    @classmethod
    def _ensure_size_tuple(cls, value, parameter_name: str = "size") -> None:
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError(
                f"{parameter_name} must be tuple (width, height), got {cls._type_name(value)}: {value!r}"
            )
        cls._ensure_dimension(value[0], f"{parameter_name}[0]")
        cls._ensure_dimension(value[1], f"{parameter_name}[1]")

    @classmethod
    def _ensure_rect_like(cls, value, parameter_name: str = "rect") -> None:
        api_validation.ensure_rect_like(
            value,
            parameter_name,
            pygame.Rect,
            cls._ensure_real,
            cls._with_try_hint,
        )

    @classmethod
    def _ensure_color_like(cls, value, parameter_name: str = "color") -> None:
        api_validation.ensure_color_like(
            value,
            parameter_name,
            cls._ensure_real,
            cls._with_try_hint,
        )

    @classmethod
    def _ensure_background_source(cls, value, parameter_name: str = "source") -> None:
        if isinstance(value, appearance.Appearance):
            return
        if isinstance(value, str):
            return
        if isinstance(value, tuple):
            cls._ensure_color_like(value, parameter_name)
            return
        raise TypeError(
            f"{parameter_name} must be str path, color tuple, or Appearance, got {cls._type_name(value)}: {value!r}"
        )

    @classmethod
    def _ensure_background_selector(cls, value, parameter_name: str = "background") -> None:
        if isinstance(value, int):
            return
        if isinstance(value, appearance.Appearance):
            return
        raise TypeError(
            f"{parameter_name} must be int index or Appearance, got {cls._type_name(value)}: {value!r}"
        )

    @classmethod
    def _ensure_actor_classes(cls, actor_classes) -> None:
        if not isinstance(actor_classes, list):
            raise TypeError(
                f"actor_classes must be list[type[Actor]], got {cls._type_name(actor_classes)}: {actor_classes!r}"
            )
        for actor_class in actor_classes:
            if not isinstance(actor_class, type) or not issubclass(actor_class, actor_mod.Actor):
                raise TypeError(
                    f"actor_classes must contain Actor subclasses, got {cls._type_name(actor_class)}: {actor_class!r}"
                )

    def _validate_parameters(self, x, y):
        if isinstance(x, bool) or isinstance(y, bool):
            raise TypeError(
                f"World(x, y) x and y must be int or float; Got ({type(x)}, {type(y)})"
            )
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError(
                f"World(x, y) x and y must be int or float; Got ({type(x)}, {type(y)})"
            )
        if x <= 0 or y <= 0:
            raise ValueError(
                f"World dimensions must be positive (> 0), got ({x}, {y})"
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
        self._debug = False
        self._learning_mode = False
        self._active_dialog = None
        self.dialog = dialog_mod.DialogService(self)


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

    @property
    def debug(self) -> bool:
        """Enable a compact debug overlay with runtime values on screen."""
        return getattr(self, "_debug", False)

    @debug.setter
    def debug(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(
                f"debug must be bool, got {type(value).__name__}: {value!r}\nTry: world.debug = True"
            )
        self._debug = value

    @property
    def learning_mode(self) -> bool:
        """Enable beginner-friendly soft conversions and hints for common input mistakes."""
        return getattr(self, "_learning_mode", False)

    @learning_mode.setter
    def learning_mode(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(
                f"learning_mode must be bool, got {type(value).__name__}: {value!r}\nTry: world.learning_mode = True"
            )
        self._learning_mode = value

    @staticmethod
    def _student_warn(message: str) -> None:
        warnings.warn(message, RuntimeWarning, stacklevel=3)

    def _coerce_bool_learning(self, value, parameter_name: str):
        return api_validation.coerce_bool_learning(
            value,
            parameter_name,
            self.learning_mode,
            self._student_warn,
        )

    def _coerce_position_learning(self, value, parameter_name: str):
        return api_validation.coerce_position_learning(
            value,
            parameter_name,
            self.learning_mode,
            self._student_warn,
        )

    def _draw_debug_overlay(self, target_surface: pygame.Surface) -> None:
        if not self.debug:
            return
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(None, 18)
        lines = [
            f"frame: {self.frame}",
            f"fps: {self.fps}",
            f"tick_rate: {self.tick_rate}",
            f"actors: {len(self.actors)}",
            f"camera: {self.camera.topleft}",
        ]
        line_height = 18
        width = 0
        rendered = []
        for line in lines:
            surface = font.render(line, True, (255, 255, 255))
            rendered.append(surface)
            width = max(width, surface.get_width())

        box_width = width + 10
        box_height = line_height * len(rendered) + 8
        box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        box.fill((0, 0, 0, 150))
        target_surface.blit(box, (6, 6))

        y = 10
        for surface in rendered:
            target_surface.blit(surface, (11, y))
            y += line_height

    def contains_position(self, pos):
        """Checks if position is in the world.

        Returns:
            True, if Position is in the world.
        """
        pos = self._coerce_position_learning(pos, "pos")
        self._ensure_position_tuple(pos, "pos")
        return self.sensor_manager.contains_position(pos)

    def contains(self, pos):
        """Student-friendly alias for `contains_position(pos)`."""
        return self.contains_position(pos)

    def contains_rect(self, rect: Union[Tuple[int, int, int, int], pygame.Rect]):
        """
        Returns True if the entire rectangle is fully inside the world.

        Useful when ensuring that an object is completely within bounds.
        """
        self._ensure_rect_like(rect, "rect")
        return self.sensor_manager.contains_rect_all(rect)

    def contains_rect_any(self, rect: Union[Tuple[int, int, int, int], pygame.Rect]):
        """
        Returns True if any part of the rectangle is inside the world.

        Useful when ensuring that an object is completely within bounds.
        """
        self._ensure_rect_like(rect, "rect")
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
        self._ensure_dimension(value, "tick_rate")
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
        self._ensure_dimension(value, "fps")
        if self.app.platform.is_web() and value > 60:
            value = 60
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
        self._ensure_dimension(value, "world_size_x")
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
        self._ensure_dimension(value, "world_size_y")
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
        self._ensure_dimension(value, "columns")
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
        self._ensure_dimension(value, "rows")
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
        if self.learning_mode and isinstance(value, list) and len(value) == 2:
            self._student_warn("Learning mode: converted size from list to tuple")
            value = (value[0], value[1])
        self._ensure_size_tuple(value, "size")
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
        self._ensure_background_source(source, "source")
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
        self._ensure_background_selector(background, "background")
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
        if background is not None:
            self._ensure_background_selector(background, "background")
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
        self._ensure_background_source(source, "source")
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
        self._ensure_background_source(source, "source")
        return self._get_background_facade().add_background(source)

    def set_bg(self, source: Union[str, Tuple[int, int, int]]) -> background_mod.Background:
        """Student-friendly alias for `set_background(source)`."""
        return self.set_background(source)

    def add_bg(self, source: Union[str, Tuple[int, int, int]]) -> background_mod.Background:
        """Student-friendly alias for `add_background(source)`."""
        return self.add_background(source)

    def next_bg(self) -> background_mod.Background:
        """Student-friendly alias to switch to the next background."""
        return self.switch_background(-1)

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
        self._ensure_int(frames, "frames")
        if frames < 0:
            raise ValueError(f"frames must be >= 0, got {frames}")
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
        fullscreen = self._coerce_bool_learning(fullscreen, "fullscreen")
        fit_desktop = self._coerce_bool_learning(fit_desktop, "fit_desktop")
        replit = self._coerce_bool_learning(replit, "replit")
        self._ensure_bool(fullscreen, "fullscreen")
        self._ensure_bool(fit_desktop, "fit_desktop")
        self._ensure_bool(replit, "replit")
        if event is not None and not isinstance(event, str):
            raise TypeError(
                f"event must be str or None, got {type(event).__name__}: {event!r}"
            )
        self._run_project_validation()
        self._get_runtime_facade().run(
            fullscreen=fullscreen,
            fit_desktop=fit_desktop,
            replit=replit,
            event=event,
            data=data,
        )


    def _run_project_validation(self) -> None:
        """Emit warnings for project issues relevant to local desktop execution."""
        try:
            if app_mod.App.get_platform().is_web():
                return  # already validated before export; no filesystem in browser
            from pathlib import Path
            from miniworlds.base.project_validator import ProjectValidator, Severity
            main = sys.modules.get("__main__")
            if not (main and getattr(main, "__file__", None)):
                return
            entry = Path(main.__file__).resolve()
            for issue in ProjectValidator(entry.parent, entry).validate():
                if issue.local_severity in (Severity.WARNING, Severity.ERROR):
                    warnings.warn(f"[miniworlds] {issue.message}", stacklevel=4)
        except Exception:
            pass  # validation is best-effort; never break the game

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
        position = self._coerce_position_learning(position, "position")
        self._ensure_position_tuple(position, "position")
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
        if self.learning_mode and not isinstance(message, str):
            self._student_warn(
                f"Learning mode: converted message from {type(message).__name__} to str"
            )
            message = str(message)
        self._ensure_non_empty_str(message, "message")
        self._get_runtime_facade().send_message(message, data)

    def broadcast(self, message: str, data: Optional[object] = None) -> None:
        """Student-friendly alias for `send_message(message, data)`."""
        self.send_message(message, data)

    def switch_world(self, new_world: "World", reset: bool = False) -> None:
        """Switch the active scene to another world.

        Args:
            new_world: The world that should become active.
            reset: If `True`, the new world is reset before it starts.
        """
        reset = self._coerce_bool_learning(reset, "reset")
        if new_world is None:
            raise TypeError(
                "new_world must not be None"
            )
        if not isinstance(new_world, world_base.WorldBase):
            raise TypeError(
                f"new_world must be a World, got {type(new_world).__name__}: {new_world!r}"
            )
        self._ensure_bool(reset, "reset")
        self._get_runtime_facade().switch_world(new_world, reset)


    def quit(self, exit_code: int = 0) -> None:
        """
        Immediately quits the application and closes the game window.

        Args:
            exit_code: Exit code returned by the application. Defaults to 0.

        Example:
            >>> world.quit()
        """
        self._ensure_int(exit_code, "exit_code")
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
        position = self._coerce_position_learning(position, "position")
        self._ensure_position_tuple(position, "position")
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
        position = self._coerce_position_learning(position, "position")
        self._ensure_position_tuple(position, "position")
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
        position = self._coerce_position_learning(position, "position")
        self._ensure_position_tuple(position, "position")
        # overwritten in tiled_sensor_manager
        return self._get_runtime_facade().detect_actors(position)

    def actors_at(self, position: Tuple[float, float]) -> List["actor_mod.Actor"]:
        """Student-friendly alias for `detect_actors(position)`."""
        return self.detect_actors(position)

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
        pixel = self._coerce_position_learning(pixel, "pixel")
        self._ensure_position_tuple(pixel, "pixel")
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
        World._ensure_position_tuple(pos1, "pos1")
        World._ensure_position_tuple(pos2, "pos2")
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
        self._ensure_position_tuple(pos1, "pos1")
        self._ensure_position_tuple(pos2, "pos2")
        return world_runtime_facade.WorldRuntimeFacade.direction_to(pos1, pos2)
