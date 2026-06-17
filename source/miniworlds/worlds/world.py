import asyncio
import math
import sys
import time
import warnings
from functools import cached_property
from typing import Callable, List, Optional, Set, Tuple, Union, cast

import pygame

import miniworlds.actors.actor as actor_mod
import miniworlds.appearances.appearance as appearance
import miniworlds.appearances.background as background_mod
import miniworlds.appearances.backgrounds_manager as backgrounds_manager
import miniworlds.base.api_validation as api_validation
import miniworlds.base.app as app
import miniworlds.base.app as app_mod
import miniworlds.positions.rect as world_rect
import miniworlds.tools.timer as timer
import miniworlds.worlds.dialog as dialog_mod
import miniworlds.worlds.manager.camera_manager as world_camera_manager
import miniworlds.worlds.manager.collision_manager as coll_manager
import miniworlds.worlds.manager.data_manager as data_manager
import miniworlds.worlds.manager.draw_manager as draw_manager
import miniworlds.worlds.manager.event_manager as event_manager
import miniworlds.worlds.manager.layout_manager as layout_manager
import miniworlds.worlds.manager.mainloop_manager as mainloop_manager
import miniworlds.worlds.manager.mouse_manager as mouse_manager
import miniworlds.worlds.manager.music_manager as world_music_manager
import miniworlds.worlds.manager.position_manager as position_manager
import miniworlds.worlds.manager.sound_manager as world_sound_manager
import miniworlds.worlds.world_background_facade as world_background_facade
import miniworlds.worlds.world_base as world_base
import miniworlds.worlds.world_initialization_facade as world_initialization_facade
import miniworlds.worlds.world_runtime_facade as world_runtime_facade
from miniworlds.base.exceptions import (
    WorldArgumentsError,
)


class World(world_base.WorldBase):
    """Pixel-based scene that owns actors, backgrounds, input, and events.

    Positions in a `World` are pixel coordinates. Actors are placed by their
    top-left position by default unless their origin is changed.

    Notes:
        Collision checks use sprite masks by default.

    Examples:
        ::

            Create and run a world:

                from miniworlds import World
                world = World(300, 200)
                world.run()

            Configure a subclass during setup:

                import miniworlds

                class MyWorld(miniworlds.World):
                    def on_setup(self):
                        self.columns = 300
                        self.rows = 200
    """

    __slots__ = (
        # Facades
        "_initialization_facade",
        # Other instance attributes
        "_debug",
        "_learning_mode",
        "_active_dialog",
        "dialog",
        # Note: __dict__ is inherited from object (via WorldBase),
        # so dynamic attributes (including @cached_property) work normally
    )

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
    def _ensure_background_selector(
        cls, value, parameter_name: str = "background"
    ) -> None:
        if isinstance(value, bool):
            raise TypeError(
                f"{parameter_name} must be int index or Appearance, got {cls._type_name(value)}: {value!r}"
            )
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
            if not isinstance(actor_class, type) or not issubclass(
                actor_class, actor_mod.Actor
            ):
                raise TypeError(
                    f"actor_classes must contain Actor subclasses, got {cls._type_name(actor_class)}: {actor_class!r}"
                )

    @classmethod
    def _normalize_constructor_dimensions(cls, x, y):
        if isinstance(x, tuple):
            if y != 400:
                raise TypeError(
                    "World((width, height)) cannot be combined with a second y value"
                )
            cls._ensure_size_tuple(x, "x")
            return x
        return x, y

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
            raise ValueError(f"World dimensions must be positive (> 0), got ({x}, {y})")

    def __init__(
        self,
        x: Union[int, Tuple[int, int]] = 400,
        y: int = 400,
    ):
        """Create a world with the given size.

        Args:
            x: Width in pixels, or a `(width, height)` tuple.
            y: Height in pixels. Ignored when `x` is a tuple.

        Examples:
            ::

                world = World(400, 300)
                square_world = World((200, 200))
        """
        # Initialization facade is created directly during __init__
        # (not via cached_property) because it's needed immediately
        self._initialization_facade = (
            world_initialization_facade.WorldInitializationFacade(self)
        )
        self._initialization_facade.initialize_pre_base_state(x, y)
        super().__init__()
        self._initialization_facade.initialize_post_base_state()
        self._debug = False
        self._learning_mode = False
        self._active_dialog = None
        self.dialog = dialog_mod.DialogService(self)

    @cached_property
    def _background_facade(self) -> world_background_facade.WorldBackgroundFacade:
        return world_background_facade.WorldBackgroundFacade(self)

    @cached_property
    def _runtime_facade(self) -> world_runtime_facade.WorldRuntimeFacade:
        return world_runtime_facade.WorldRuntimeFacade(self)

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
        """bool: Whether to draw a compact runtime debug overlay.

        Examples:
            ::

                world.debug = True
        """
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
        """bool: Whether beginner-friendly conversions and hints are enabled.

        Examples:
            ::

                world.learning_mode = True
        """
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
        """Return whether a position lies inside the world.

        Args:
            pos: Position as `(x, y)`.

        Returns:
            `True` if the position is inside the world.

        Examples:
            ::

                if world.contains_position(actor.center):
                    actor.move()
        """
        pos = self._coerce_position_learning(pos, "pos")
        self._ensure_position_tuple(pos, "pos")
        return self.sensor_manager.contains_position(pos)

    def contains(self, pos):
        """Return whether a position lies inside the world.

        This is a short alias for `contains_position()`.
        """
        return self.contains_position(pos)

    def contains_rect(self, rect: Union[Tuple[int, int, int, int], pygame.Rect]):
        """Return whether a rectangle is fully inside the world.

        Args:
            rect: Rectangle as `(x, y, width, height)` or `pygame.Rect`.

        Returns:
            `True` if the whole rectangle is inside the world.

        Examples:
            ::

                if world.contains_rect(actor.rect):
                    actor.move()
        """
        self._ensure_rect_like(rect, "rect")
        return self.sensor_manager.contains_rect_all(rect)

    def contains_rect_any(self, rect: Union[Tuple[int, int, int, int], pygame.Rect]):
        """Return whether any part of a rectangle is inside the world.

        Args:
            rect: Rectangle as `(x, y, width, height)` or `pygame.Rect`.

        Returns:
            `True` if at least one part of the rectangle is inside the world.

        Examples:
            ::

                if not world.contains_rect_any(actor.rect):
                    actor.remove()
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
        """int: Horizontal world size in pixels.

        Examples:
            ::

                world.world_size_x = 800
                print(world.world_size_x)
        """
        return self.camera.world_size_x

    @world_size_x.setter
    def world_size_x(self, value: int) -> None:
        self._ensure_dimension(value, "world_size_x")
        self.camera.world_size_x = value

    @property
    def world_size_y(self) -> int:
        """int: Vertical world size in pixels.

        Examples:
            ::

                world.world_size_y = 600
                print(world.world_size_y)
        """
        return self.camera.world_size_y

    @world_size_y.setter
    def world_size_y(self, value: int) -> None:
        self._ensure_dimension(value, "world_size_y")
        self.camera.world_size_y = value

    @property
    def columns(self) -> int:
        """int: Width of the visible world area in pixels.

        Examples:
            ::

                world.columns = 640
        """
        return self.camera.width

    @columns.setter
    def columns(self, value: int) -> None:
        self.set_columns(value)

    def set_columns(self, value: int) -> None:
        """Set the visible world width in pixels.

        Args:
            value: New width in pixels.

        Examples:
            ::

                world.set_columns(640)
        """
        self._ensure_dimension(value, "columns")
        self.camera.width = value
        self.world_size_x = value

    @property
    def rows(self) -> int:
        """int: Height of the visible world area in pixels.

        Examples:
            ::

                world.rows = 480
        """
        return self.camera.height

    @rows.setter
    def rows(self, value: int) -> None:
        self.set_rows(value)

    def set_rows(self, value: int) -> None:
        """Set the visible world height in pixels.

        Args:
            value: New height in pixels.

        Examples:
            ::

                world.set_rows(480)
        """
        self._ensure_dimension(value, "rows")
        self.camera.height = value
        self.world_size_y = value

    @property
    def size(self) -> Tuple[int, int]:
        """tuple[int, int]: World size as `(width, height)` in pixels.

        Examples:
            ::

                width, height = world.size
                world.size = (800, 600)
        """
        return self.world_size_x, self.world_size_y

    @size.setter
    def size(self, value: Tuple[int, int]) -> None:
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
        """Background: Currently active world background.

        Examples:
            ::

                world.background = (30, 30, 30)
                world.background = "images/sky.png"
                current = world.background
        """
        return self._background_facade.background

    @background.setter
    def background(
        self, source: Union[str, Tuple[int, int, int], appearance.Appearance]
    ) -> None:
        """Set the active background from a color, image path, or appearance.

        Args:
            source: Image path, RGB/RGBA color tuple, or `Appearance`.

        Examples:
            ::

                world.background = (0, 0, 0)
                world.background = "images/background.png"
        """
        self._ensure_background_source(source, "source")
        self._background_facade.set_background_property(source)

    def get_background(self) -> background_mod.Background:
        """Return the active background.

        Returns:
            The current `Background`.

        Examples:
            ::

                bg = world.get_background()
                bg.fill_color = (0, 0, 0)
        """
        return self._background_facade.background

    def switch_background(
        self, background: Union[int, appearance.Appearance]
    ) -> background_mod.Background:
        """Switch to another background.

        Pass an index, an existing appearance, or `-1` for the next background.

        Args:
            background: Background index, `Appearance`, or `-1`.

        Returns:
            The new active `Background`.

        Examples:
            ::

                world.add_background("images/day.png")
                world.add_background("images/night.png")
                world.switch_background(1)
                world.switch_background(-1)
        """
        self._ensure_background_selector(background, "background")
        return self._background_facade.switch_background(background)

    def remove_background(
        self, background: Optional[Union[int, appearance.Appearance]] = None
    ) -> None:
        """Remove a background.

        Args:
            background: Background index or `Appearance`. If omitted, the last
                background is removed.

        Examples:
            ::

                world.remove_background()
                world.remove_background(0)
        """
        if background is not None:
            self._ensure_background_selector(background, "background")
        self._background_facade.remove_background(background)

    def set_background(
        self, source: Union[str, Tuple[int, int, int]]
    ) -> background_mod.Background:
        """Replace the active background.

        Args:
            source: Image path or RGB/RGBA color tuple.

        Returns:
            The new active `Background`.

        Examples:
            ::

                world.set_background("images/sky.png")
                world.set_background((30, 30, 30))
        """
        self._ensure_background_source(source, "source")
        return self._background_facade.set_background(source)

    def add_background(
        self, source: Union[str, Tuple[int, int, int]]
    ) -> background_mod.Background:
        """Add a background and make it active.

        Args:
            source: Image path or RGB/RGBA color tuple.

        Returns:
            The newly created `Background`.

        Examples:
            ::

                world.add_background((255, 0, 0))
                world.add_background("images/background.png")
        """
        self._ensure_background_source(source, "source")
        return self._background_facade.add_background(source)

    def set_bg(
        self, source: Union[str, Tuple[int, int, int]]
    ) -> background_mod.Background:
        """Student-friendly alias for `set_background(source)`."""
        return self.set_background(source)

    def add_bg(
        self, source: Union[str, Tuple[int, int, int]]
    ) -> background_mod.Background:
        """Student-friendly alias for `add_background(source)`."""
        return self.add_background(source)

    def next_bg(self) -> background_mod.Background:
        """Student-friendly alias to switch to the next background."""
        return self.switch_background(-1)

    def start(self) -> None:
        """Start or resume world updates.

        Examples:
            ::

                world.start()
        """
        self._runtime_facade.start()

    def stop(self, frames: int = 0) -> None:
        """Stop world updates immediately or after a number of frames.

        Args:
            frames: Frames to wait before stopping. `0` stops immediately.

        Examples:
            ::

                world.stop()
                world.stop(frames=5)
        """
        self._ensure_int(frames, "frames")
        if frames < 0:
            raise ValueError(f"frames must be >= 0, got {frames}")
        self._runtime_facade.stop(frames)

    def run(
        self,
        fullscreen: bool = False,
        fit_desktop: bool = False,
        replit: bool = False,
        event: Optional[str] = None,
        data: Optional[object] = None,
    ) -> None:
        """Start the Miniworlds main loop.

        Call this once at the end of a Miniworlds program.

        Args:
            fullscreen: Whether to launch in fullscreen mode.
            fit_desktop: Whether to adapt the window to the desktop.
            replit: Whether to use Replit-specific display adjustments.
            event: Optional event name to queue at startup.
            data: Optional data to include with the startup event.

        Examples:
            ::

                world = World(800, 600)
                world.run()
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
        self._runtime_facade.run(
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
        """Return whether a position lies inside the world.

        Args:
            position: Position as `(x, y)`.

        Returns:
            `True` if the position is inside the world.

        Examples:
            ::

                if world.is_in_world((100, 100)):
                    print("inside")
        """
        position = self._coerce_position_learning(position, "position")
        self._ensure_position_tuple(position, "position")
        return self._runtime_facade.is_in_world(position)

    def send_message(self, message: str, data: Optional[object] = None) -> None:
        """Broadcast a message to the world and its actors.

        The message is dispatched through the event system and can be handled
        by registered message handlers.

        Args:
            message: Message name.
            data: Optional payload for message-specific handlers.

        Examples:
            ::

                world.send_message("game_over")

                @world.register
                def on_message(self, message):
                    if message == "game_over":
                        self.stop()
        """
        if self.learning_mode and not isinstance(message, str):
            self._student_warn(
                f"Learning mode: converted message from {type(message).__name__} to str"
            )
            message = str(message)
        self._ensure_non_empty_str(message, "message")
        self._runtime_facade.send_message(message, data)

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
            raise TypeError("new_world must not be None")
        if not isinstance(new_world, world_base.WorldBase):
            raise TypeError(
                f"new_world must be a World, got {type(new_world).__name__}: {new_world!r}"
            )
        self._ensure_bool(reset, "reset")
        self._runtime_facade.switch_world(new_world, reset)

    def quit(self, exit_code: int = 0) -> None:
        """Quit the application and close the game window.

        Args:
            exit_code: Process exit code.

        Examples:
            ::

                world.quit()
        """
        self._ensure_int(exit_code, "exit_code")
        self._runtime_facade.quit(exit_code)

    def reset(self):
        """Reset the world to its initial state.

        Examples:
            ::

                @player.register
                def on_detecting_actor(self, other):
                    if isinstance(other, Enemy):
                        self.world.reset()
        """
        self._runtime_facade.reset()

    def _clear(self) -> None:
        """
        Clears the world's state: event queue, all backgrounds, and all actors.

        This method is typically used during a world reset.

        Example:
            >>> world.clear()
        """
        self._runtime_facade.clear()

    def get_from_pixel(
        self, position: Tuple[float, float]
    ) -> Optional[Tuple[float, float]]:
        """Convert a screen pixel position to a world position.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            World position, or `None` if the pixel is outside the world.

        Examples:
            ::

                @world.register
                def on_mouse_left(self, position):
                    world_position = self.get_from_pixel(position)
                    if world_position:
                        Actor(world_position)
        """
        position = self._coerce_position_learning(position, "position")
        self._ensure_position_tuple(position, "position")
        return self._runtime_facade.get_from_pixel(position)

    def to_pixel(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """Convert a world position to a screen pixel position.

        Args:
            position: World position as `(x, y)`.

        Returns:
            Pixel position as `(x, y)`.

        Examples:
            ::

                pixel = world.to_pixel(actor.position)
        """
        position = self._coerce_position_learning(position, "position")
        self._ensure_position_tuple(position, "position")
        return self._runtime_facade.to_pixel(position)

    def on_setup(self) -> None:
        """Hook for initial world setup.

        Override this in subclasses or register a function with `@world.register`.

        Examples:
            ::

                @world.register
                def on_setup(self):
                    self.background = (0, 0, 0)
                    Actor((20, 20))
        """
        pass

    @property
    def has_background(self) -> bool:
        """bool: Whether the world has at least one background.

        Examples:
            ::

                if world.has_background:
                    world.next_bg()
        """
        return self._background_facade.has_background()

    def detect_actors(self, position: Tuple[float, float]) -> List["actor_mod.Actor"]:
        """Return all actors at a world position.

        Args:
            position: World position as `(x, y)`.

        Returns:
            Actors found at the position.

        Examples:
            ::

                actors = world.detect_actors(player.position)
                for actor in actors:
                    if isinstance(actor, Coin):
                        actor.remove()
        """
        position = self._coerce_position_learning(position, "position")
        self._ensure_position_tuple(position, "position")
        # overwritten in tiled_sensor_manager
        return self._runtime_facade.detect_actors(position)

    def actors_at(self, position: Tuple[float, float]) -> List["actor_mod.Actor"]:
        """Student-friendly alias for `detect_actors(position)`."""
        return self.detect_actors(position)

    def get_actors_from_pixel(
        self, pixel: Tuple[float, float]
    ) -> List[actor_mod.Actor]:
        """Return all actors under a screen pixel.

        Args:
            pixel: Screen pixel as `(x, y)`.

        Returns:
            Actors whose screen rectangle overlaps the pixel.

        Examples:
            ::

                @world.register
                def on_mouse_left(self, position):
                    for actor in self.get_actors_from_pixel(position):
                        actor.hide()
        """
        pixel = self._coerce_position_learning(pixel, "pixel")
        self._ensure_position_tuple(pixel, "pixel")
        return self._runtime_facade.get_actors_from_pixel(pixel)

    @staticmethod
    def distance_to(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Return the Euclidean distance between two positions.

        Args:
            pos1: First position as `(x, y)`.
            pos2: Second position as `(x, y)`.

        Returns:
            Distance between both positions.

        Examples:
            ::

                distance = World.distance_to((0, 0), (3, 4))
        """
        World._ensure_position_tuple(pos1, "pos1")
        World._ensure_position_tuple(pos2, "pos2")
        return world_runtime_facade.WorldRuntimeFacade.distance_to(pos1, pos2)

    def direction_to(
        self, pos1: Tuple[float, float], pos2: Tuple[float, float]
    ) -> float:
        """Return the Miniworlds direction from one position to another.

        Args:
            pos1: Start position as `(x, y)`.
            pos2: Target position as `(x, y)`.

        Returns:
            Direction angle in degrees.

        Examples:
            ::

                mouse_position = world.mouse.get_position()
                actor.direction = world.direction_to(actor.center, mouse_position)
        """
        self._ensure_position_tuple(pos1, "pos1")
        self._ensure_position_tuple(pos2, "pos2")
        return world_runtime_facade.WorldRuntimeFacade.direction_to(pos1, pos2)
