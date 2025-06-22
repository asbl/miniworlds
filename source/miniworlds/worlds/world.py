import math
import pygame
import sys
import asyncio
import time
from typing import Tuple, Union, Optional, List, cast, Callable

import miniworlds.appearances.appearance as appearance
import miniworlds.appearances.background as background_mod
import miniworlds.appearances.backgrounds_manager as backgrounds_manager
import miniworlds.base.app as app
import miniworlds.worlds.world_base as world_base
import miniworlds.worlds.manager.collision_manager as coll_manager
import miniworlds.worlds.manager.event_manager as event_manager
import miniworlds.worlds.manager.mouse_manager as mouse_manager
import miniworlds.worlds.manager.music_manager as world_music_manager
import miniworlds.worlds.manager.sound_manager as world_sound_manager
import miniworlds.worlds.manager.position_manager as position_manager
import miniworlds.worlds.manager.camera_manager as world_camera_manager
import miniworlds.worlds.manager.world_connector as world_connector
import miniworlds.worlds.data.export_factory as export_factory
import miniworlds.worlds.data.import_factory as import_factory
import miniworlds.positions.rect as world_rect
import miniworlds.actors.actor as actor_mod
import miniworlds.tools.world_inspection as world_inspection
import miniworlds.tools.color as color
import miniworlds.tools.timer as timer
import miniworlds.base.app as app_mod

from miniworlds.base.exceptions import (
    WorldArgumentsError,
)


class World(world_base.WorldBase):
    """A world is a playing field on which actors can move.

    A world has a `background` and provides basic functions for the positioning of
    actors and for the collision detection of actors, which can be queried via the sensors of the actors.

    You can create your own world by creating a class that inherits from World or you can directly create a world
    object of type `World` or one of its child classes (`TiledWorld`, `PhysicsWorld`, ...).

    *World*

    A world for pixel accurate games.

    * The position of a actor on a World is the pixel at topleft of actor.

    * New actors are created with top-left corner of actor rect at position.

    * Two actors collide when their sprites overlap.

    .. image:: ../_images/asteroids.jpg
        :alt: Asteroids

    **Other worlds:**

    * TiledWorld: For worlds using Tiles, like rogue-like rpgs, see
      :doc:`TiledWorld <../api/world.tiledworld>`)
    * PhysicsWorld: For worlds using the PhysicsEngine, see
      :doc:`PhysicsWorld <../api/world_physicsworld>`)

    Examples:

        Creating a TiledWorld Object:

        .. code-block:: python

            from miniworlds import *

            my_world = TiledWorld()
            my_world.columns = 30
            my_world.rows = 20
            my_world.tile_size = 20


        Creating a TiledWorld-Subclass.

        .. code-block:: python

            import miniworlds

            class MyWorld(miniworlds.TiledWorld):

                def on_setup(self):
                    self.columns = 30
                    self.rows = 20
                    self.tile_size = 20

        Creating a World Object:

        .. code-block:: python

            from miniworlds import *

            my_world = World()
            my_world.columns = 300
            my_world.rows = 200

        Creating a World Subclass

        .. code-block:: python

            import miniworlds

            class MyWorld(miniworlds.World):

                def on_setup(self):
                    self.columns = 300
                    self.rows = 200


    See also:

        * See: :doc:`World <../api/world>`
        * See: :doc:`TiledWorld <../api/world.tiledworld>`


    Args:
        view_x: columns of new world (default: 40)
        view_y: rows of new world (default:40)
        tile_size: Size of tiles (1 for normal worlds, can differ for Tiledworlds)
    """

    subclasses = None

    def validate_parameters(self, x, y):
        if not isinstance(x, Union[float, int]) or not isinstance(y, Union[float, int]):
            raise TypeError(
                f"World(x, y) x and y must be int or float; Got ({type(x)}, {type(y)})"
            )

    def __init__(
        self,
        x: Union[int, Tuple[int, int]] = 400,
        y: int = 400,
        ):
        # --- Parameter validation ---
        self.validate_parameters(x, y)

        # --- Core state ---
        self._was_setup = False
        self.is_tiled = False
        self._is_acting = True  # Whether the act() method is active

        # --- Camera setup ---
        self.camera = self._get_camera_manager_class()(x, y, self)

        # --- Actor management ---
        self.actors: "pygame.sprite.LayeredDirty" = pygame.sprite.LayeredDirty()

        # --- Event system ---
        self.event_manager: event_manager.EventManager = self._create_event_manager()

        # --- Superclass initialization ---
        super().__init__()

        # --- Timing and frame control ---
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self._fps: int = 60
        self._step: int = 1
        self.frame: int = 0

        # --- State flags ---
        self._key_pressed: bool = False
        self._animated: bool = False
        self._is_filled: bool = False
        self._orientation: int = 0
        self._static: bool = False
        self._default_is_filled = False
        self._default_fill_color = None
        self._default_border_color = None
        self._default_border = None
        self.is_running: bool = True
        self.is_listening: bool = True
        self.actors_fixed_size: bool = False

        # --- Actor & animation systems ---
        self.timed_objects: list = []
        self.dynamic_actors: "pygame.sprite.Group" = pygame.sprite.Group()
        self._registered_methods: List[Callable] = []
        self.reload_costumes_queue: list = []

        # --- Rendering and backgrounds ---
        self.backgrounds_manager: "backgrounds_manager.BackgroundsManager" = backgrounds_manager.BackgroundsManager(self)
        self.background = background_mod.Background(self)
        self.background.update()
        
        # --- Input handling ---
        self.mouse_manager: "mouse_manager.MouseManager" = mouse_manager.MouseManager(self)

        # --- Application & managers ---
        if not app.App.init:
            self.app: "app.App" = app.App("miniworlds", self)
        else:
            self.app = app.App.running_app

        self.music: "world_music_manager.MusicManager" = world_music_manager.MusicManager(self.app)
        self.sound: "world_sound_manager.SoundManager" = world_sound_manager.SoundManager(self.app)
        self.collision_manager: "coll_manager.CollisionManager" = coll_manager.CollisionManager(self)

        # --- Register world in application ---
        self.app.event_manager.to_event_queue("setup", None)
        self.app.worlds_manager.add_topleft(self)



    def add_world_right(self, world: "World", size: int = 100):
        """Adds a world to the right of the current world.

        Args:
            world: The world instance to add.
            size: Width of the new world in pixels (default: 100).

        Returns:
            The added world.
        """
        return self.app.worlds_manager.add_world(world, "right", size)


    def add_world_bottom(self, world: "World", size: int = 100):
        """Adds a world below the current world.

        Args:
            world: The world instance to add.
            size: Height of the new world in pixels (default: 100).

        Returns:
            The added world.
        """
        return self.app.worlds_manager.add_world(world, "bottom", size)


    def remove_world(self, world: "World"):
        """Removes a world from the layout and updates the window.

        Args:
            world: The world instance to remove.

        Returns:
            None
        """
        return self.app.worlds_manager.remove_world(world)

    @staticmethod
    def _get_camera_manager_class():
        return world_camera_manager.CameraManager

    @staticmethod
    def _get_world_connector_class():
        """needed by get_world_connector in parent class"""
        return world_connector.WorldConnector

    def get_world_connector(self, actor) -> world_connector.WorldConnector:
        return self._get_world_connector_class()(self, actor)

    def _create_event_manager(self):
        return event_manager.EventManager(self)

    def detect_position(self, pos):
        """Checks if position is in the world.

        Returns:
            True, if Position is in the world.
        """
        if 0 <= pos[0] < self.world_size_x and 0 <= pos[1] < self.world_size_y:
            return True
        else:
            return False

    def contains_rect(self, rect: Union[tuple, pygame.Rect]):
        """Detects if rect is completely on the world.

        Args:
            rect: A rectangle as tuple (top, left, width, height)
        """
        rectangle = world_rect.Rect.create(rect)
        topleft_on_the_world = self.detect_position(rectangle.topleft)
        bottom_right_on_the_world = self.detect_position(rectangle.bottomright)
        return topleft_on_the_world or bottom_right_on_the_world

    @property
    def surface(self):
        return self.background.surface

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    @property
    def step(self) -> int:
        """Step defines how often the method ``act()`` will be called.

        If e.g. ``step = 30``, the game logic will be called every 30th-frame.

        .. note::

          You can adjust the frame-rate with ``world.fps``

        Examples:

            Set speed and fps.

            .. code-block:: python

                from miniworlds import *

                world = World()
                world.size = (120,210)

                @world.register
                def on_setup(self):
                    world.fps = 1
                    world.speed = 3

                @world.register
                def act(self):

                world.run()

        Output:

            ```
            3
            6
            9
            12
            15
            ```
        """
        return self._step

    @step.setter
    def step(self, value: int):
        self._step = value

    @property
    def fps(self) -> int:
        """
        Frames per second shown on the screen.

        This controls how often the screen is redrawn. However, the game logic
        can be called more often or less often independently of this with ``world.speed.``

        Examples:

            .. code-block:: python

                world.speed = 10
                world.fps = 24
                def act(self):
                    nonlocal i
                    i = i + 1
                    if world.frame == 120:
                        test_instance.assertEqual(i, 13)
                        test_instance.assertEqual(world.frame, 120)
        """
        return self._fps

    @fps.setter
    def fps(self, value: int):
        self._fps = value

    @property
    def world_size_x(self) -> int:
        """The x-world_size (defaults to view_size)"""
        return self.camera.world_size_x

    @world_size_x.setter
    def world_size_x(self, value: int):
        self.camera.world_size_x = value

    @property
    def world_size_y(self) -> int:
        """The y-world_size (defaults to view_size)"""
        return self.camera.world_size_y

    @world_size_y.setter
    def world_size_y(self, value: int):
        self.camera.world_size_y = value

    @property
    def columns(self) -> int:
        return self.camera.width

    @columns.setter
    def columns(self, value: int):
        self.set_columns(value)

    def set_columns(self, value: int):
        self.camera.width = value
        self.world_size_x = value

    @property
    def rows(self) -> int:
        return self.camera.height

    @rows.setter
    def rows(self, value: int):
        self.set_rows(value)

    def set_rows(self, value: int):
        self.camera.height = value
        self.world_size_y = value

    def borders(self, value: Union[tuple, pygame.Rect]) -> list:
        """Gets all borders from a source (`Position` or `Rect`).

        Args:
            value: Position or rect

        Returns:
            A list of borders, e.g. ["left", "top"], if rect is touching the left a top border.

        """
        return []

    @property
    def size(self) -> tuple:
        """Set the size of world

        Examples:

          Create a world with 800 columns and 600 rows:

          .. code-block:: python

            world = miniworlds.PixelWorld()
            world.size = (800, 600)
        """
        return self.world_size_x, self.world_size_y

    @size.setter
    def size(self, value: tuple):
        self.world_size_x = value[0]
        self.world_size_y = value[1]
        self.camera.width = value[0]
        self.camera.height = value[1]

    @property
    def default_fill_color(self):
        """Set default fill color for borders and lines"""
        return self._default_fill_color

    @default_fill_color.setter
    def default_fill_color(self, value):
        self._default_fill_color = color.Color(value).get()

    def default_fill(self, value):
        """Set default fill color for borders and lines"""
        self._is_filled = value
        if self.default_is_filled is not None and self.default_is_filled:
            self._default_fill_color = color.Color(value).get()

    @property
    def default_is_filled(self):
        return self._default_is_filled

    @default_is_filled.setter
    def default_is_filled(self, value):
        self.default_fill(value)

    @property
    def default_stroke_color(self):
        """Set default stroke color for borders and lines. (equivalent to border-color)"""
        return self.default_border_color

    @default_stroke_color.setter
    def default_stroke_color(self, value):
        """Set default stroke color for borders and lines. (equivalent to border-color)"""
        self.default_border_color = value

    @property
    def default_border_color(self):
        """Set default border color for borders and lines.

        .. note::

          ``world.default_border_color`` does not have an effect, if no border is set.

            You must also set ``world.border`` > 0.

        Examples:

            Create actors with and without with border

            .. code-block:: python

                from miniworlds import *

                world = World(210,80)
                world.default_border_color = (0,0, 255)
                world.default_border = 1

                t = Actor((10,10))

                t2 = Actor ((60, 10))
                t2.border_color = (0,255, 0)
                t2.border = 5 # overwrites default border

                t3 = Actor ((110, 10))
                t3.border = None # removes border

                t4 = Actor ((160, 10))
                t4.add_costume("images/player.png") # border for sprite

                world.run()

            Output:

            .. image:: ../_images/border_color.png
                :width: 200px
                :alt: borders

        """
        return self._default_border_color

    @default_border_color.setter
    def default_border_color(self, value):
        self._default_border_color = value

    @property
    def default_border(self):
        """Sets default border color for actors

        .. note::

          You must also set a border for actor.

        Examples:

            Set default border for actors:

            .. code-block:: python

                from miniworlds import *

                world = World(210,80)
                world.default_border_color = (0,0, 255)
                world.default_border = 1

                t = Actor((10,10))

                world.run()
        """
        return self._default_border

    @default_border.setter
    def default_border(self, value):
        self._default_border = value

    @property
    def backgrounds(self) -> list:
        """Returns all backgrounds of the world as list."""
        return self.backgrounds_manager.backgrounds

    @property
    def background(self) -> "background_mod.Background":
        """Returns the current background"""
        return self.get_background()

    @background.setter
    def background(self, source):
        try:
            if isinstance(source, appearance.Appearance):
                self.backgrounds_manager.background = source
            else:
                self.backgrounds_manager.add_background(source)
        except (FileNotFoundError, FileExistsError) as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            raise exc_value.with_traceback(None)

    def get_background(self) -> "background_mod.Background":
        """Returns the current background"""
        return self.backgrounds_manager.background

    def switch_background(
        self, background: Union[int, "appearance.Appearance"]
    ) -> "background_mod.Background":
        """Switches the background

        Args:
            background: The index of the new background or an Appearance.
                If index = -1, the next background will be selected

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

        Returns:
            The new background

        """
        try:
            return cast(
                background_mod.Background,
                self.backgrounds_manager.switch_appearance(background),
            )
        except FileNotFoundError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            raise exc_value.with_traceback(None)

    def remove_background(self, background=None):
        """Removes a background from world

        Args:
            background: The index of the new background. Defaults to -1 (last background) or an Appearance
        """
        return self.backgrounds_manager.remove_appearance(background)

    def set_background(self, source: Union[str, tuple]) -> "background_mod.Background":
        """Adds a new background to the world

        If multiple backgrounds are added, the last adds background will be set as active background.

        Args:
            source: The path to the first image of the background or a color (e.g. (255,0,0) for red or
                    "images/my_background.png" as path to a background.

        Examples:

            Add multiple Backgrounds:

            .. code-block:: pythonlist

                from miniworlds import *

                world = World()
                world.add_background((255, 0 ,0)) # red
                world.add_background((0, 0 ,255)) # blue
                world.run() # Shows a blue world.

        Returns:
            The new created background.
        """
        try:
            return self.backgrounds_manager.set_background(source)
        except FileNotFoundError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            raise exc_value.with_traceback(None)


    def add_background(self, source: Union[str, tuple]) -> "background_mod.Background":
        """Adds a new background to the world

        If multiple backgrounds are added, the last adds background will be set as active background.

        Args:
            source: The path to the first image of the background or a color (e.g. (255,0,0) for red or
                    "images/my_background.png" as path to a background.

        Examples:

            Add multiple Backgrounds:

            .. code-block:: pythonlist

                from miniworlds import *

                world = World()
                world.add_background((255, 0 ,0)) # red
                world.add_background((0, 0 ,255)) # blue
                world.run() # Shows a blue world.

        Returns:
            The new created background.
        """
        try:
            return self.backgrounds_manager.add_background(source)
        except FileNotFoundError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            raise exc_value.with_traceback(None)

    def start(self):
        """Starts the world, if world is not running."""
        self.is_running = True

    def stop(self, frames=0):
        """Stops the world.

        Args:
            frames (int, optional): If ``frames`` is set, world will be stopped in n frames. . Defaults to 0.
        """
        if frames == 0:
            self.is_running = False
        else:
            timer.ActionTimer(frames, self.stop, 0)

    def start_listening(self):
        self.is_listening = True

    def stop_listening(self):
        self.is_listening = False

    def run(
        self,
        fullscreen: bool = False,
        fit_desktop: bool = False,
        replit: bool = False,
        event=None,
        data=None,
    ):
        """
        The method show() should always be called at the end of your program.
        It starts the mainloop.

        Examples:

            A minimal miniworlds-program:

            .. code-block:: python

                from miniworlds import *
                world = TiledWorld()
                actor = Actor()
                world.run()

            Output:

            .. image:: ../_images/min.png
                :width: 200px
                :alt: Minimal program

        """
        self.app.prepare_mainloop()
        if hasattr(self, "on_setup") and not self._was_setup:
            self.on_setup()
            self._was_setup = True
        self.backgrounds_manager.init_display()
        self.is_running = True
        if event:
            self.app.event_manager.to_event_queue(event, data)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        #loop = asyncio.get_event_loop()
        if loop.is_running():
            # Starte main() in der laufenden Event-Loop
            asyncio.ensure_future(self.app.run(
            self.image, fullscreen=fullscreen, fit_desktop=fit_desktop, replit=replit
        ))
        else:
            asyncio.run(self.app.run(
            self.image, fullscreen=fullscreen, fit_desktop=fit_desktop, replit=replit
        ))
        #await self.app.run(
        #    self.image, fullscreen=fullscreen, fit_desktop=fit_desktop, replit=replit
        #)
        

    def play_sound(self, path: str):
        """plays sound from path"""
        self.app.sound_manager.play_sound(path)

    def stop_sounds(self):
        self.app.sound_manager.stop()

    def play_music(self, path: str):
        """plays a music from path

        Args:
            path: The path to the music

        Returns:

        """
        self.music.play(path)

    def stop_music(self):
        """stops a music

        Returns:

        """
        self.music.stop()

    def get_mouse_position(self) -> Optional[tuple]:
        """
        Gets the current mouse_position

        Returns:
            Returns the mouse position if mouse is on the world. Returns None otherwise

        Examples:

            Create circles at current mouse position:


            .. code-block:: python

                from miniworlds import *

                world = PixelWorld()

                @world.register
                def act(self):
                    c = Circle(world.get_mouse_position(), 40)
                    c.color = (255,255,255, 100)
                    c.border = None

                world.run()

            Output:

            .. image:: ../_images/mousepos.png
                :width: 200px
                :alt: Circles at mouse-position


        """
        return self.mouse_manager.mouse_position

    def get_mouse_x(self) -> int:
        """Gets x-coordinate of mouse-position"""
        if self.mouse_manager.mouse_position:
            return self.mouse_manager.mouse_position[0]
        else:
            return 0

    def get_mouse_y(self) -> int:
        """Gets y-coordinate of mouse-position"""
        if self.mouse_manager.mouse_position:
            return self.mouse_manager.mouse_position[1]
        else:
            return 0

    def get_prev_mouse_position(self):
        """gets mouse-position of last frame"""
        return self.mouse_manager.prev_mouse_position

    def is_mouse_pressed(self) -> bool:
        """Returns True, if mouse is pressed"""
        return (
            self.mouse_manager.mouse_left_is_clicked()
            or self.mouse_manager.mouse_left_is_clicked()
        )

    def is_mouse_left_pressed(self) -> bool:
        """Returns True, if mouse left button is pressed"""
        return self.mouse_manager.mouse_left_is_clicked()

    def is_mouse_right_pressed(self) -> bool:
        """Returns True, if mouse right button is pressed"""
        return self.mouse_manager.mouse_right_is_clicked()

    def is_in_world(self, position: Tuple[float, float]) -> bool:
        if (
            position[0] > 0
            and position[1] > 0
            and position[0] < self.camera.world_size_x
            and position[1] < self.camera.world_size_y
        ):
            return True
        return False

    def send_message(self, message, data=None):
        """Sends broadcast message

        A message can be received by the world or any actor on world
        """
        self.app.event_manager.to_event_queue("message", message)

    def quit(self, exit_code=0):
        """quits app and closes the window"""
        self.app.quit(exit_code)

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
        self.clear()
        # Re-Setup the world
        if hasattr(self, "on_setup"):
            self._was_setup = False
            self.on_setup()
            self._was_setup = True
            
    def clear(self):
        self.app.event_manager.event_queue.clear()
        for background in self.backgrounds:
            self.backgrounds_manager.remove_appearance(background)
        # Remove all actors
        for actor in self.actors:
            actor.remove()
        

    def switch_world(self, new_world: "World", reset: bool = False):
        """Switches to another world

        Args:
            new_world (World): _description_
        """
        self.app.worlds_manager.switch_world(new_world, reset)
        

    def get_color_from_pixel(self, position: Tuple[float, float]) -> tuple:
        """
        Returns the color at a specific position

        Examples:

            .. code-block:: python

                from miniworlds import *

                world = World((100,60))

                @world.register
                def on_setup(self):
                    self.add_background((255,0,0))
                    print(self.get_color_from_pixel((5,5)))

                world.run()

            Output: (255, 0, 0, 255)

            .. image:: ../_images/get_color.png
                :width: 100px
                :alt: get color of red screen

        Args:
            position: The position to search for

        Returns:
            The color

        """
        return self.app.window.surface.get_at((int(position[0]), int(position[1])))

    def get_from_pixel(self, position: Tuple) -> Optional[tuple]:
        """Gets Position from pixel

        PixelWorld: the pixel position is returned
        TiledWorld: the tile-position is returned

        :param position: Position as pixel coordinates
        :return: The pixel position, if position is on the world, None if position is not on World.
        """
        column = position[0]
        row = position[1]
        position = (column, row)
        if column < self.camera.width and row < self.camera.height:
            return position
        else:
            return None

    def to_pixel(self, position):
        x = position[0]
        y = position[1]
        return x, y

    def on_setup(self):
        """Overwrite or register this method to call `on_setup`-Actions"""
        pass

    #def __str__(self):
    #    return f"{self.__class__.__name__} with {self.columns} columns and {self.rows} rows"
    

    @property
    def has_background(self) -> bool:
        return self.backgrounds_manager.has_appearance()

    @property
    def registered_events(self) -> set:
        return self.event_manager.registered_events

    @registered_events.setter
    def registered_events(self, value):
        return  # setter is defined so that world_event_manager is not overwritten by world parent class container

    def add_to_world(self, actor, position: tuple):
        """Adds a Actor to the world.
        Is called in __init__-Method if position is set.

        Args:
            actor: The actor, which should be added to the world.
            position: The position on the world where the actor should be added.
        """
        self.get_world_connector(actor).add_to_world(position)

    def detect_actors(self, position: Tuple[float, float]) -> List["actor_mod.Actor"]:
        """Gets all actors which are found at a specific position.

        Args:
            position: Position, where actors should be searched.

        Returns:
            A list of actors

        Examples:

          Get all actors at mouse position:

          .. code-block:: python

              position = world.get_mouse_position()
              actors = world.get_actors_by_pixel(position)

        """
        # overwritten in tiled_sensor_manager
        return cast(
            List["actor_mod.Actor"],
            [
                actor
                for actor in self.actors
                if actor.sensor_manager.detect_point(position)
            ],
        )

    def get_actors_from_pixel(self, pixel: Tuple[float, float]):
        return cast(
            List["actor_mod.Actor"],
            [actor for actor in self.actors if actor.sensor_manager.detect_pixel(pixel)],
        )

    @property
    def image(self) -> pygame.Surface:
        """The current displayed image"""
        return self.backgrounds_manager.image

    def repaint(self):
        self.background.repaint()  # called 1/frame in container.repaint()

    async def update(self):
        """The mainloop, called once per frame.

        Called in app.update() when reload_all_worlds is called.
        """

        if not self.is_running and self.frame != 0:
            self.frame += 1
            self.event_manager.update()
            return


        start = 0
        if self.is_running or self.frame == 0:
            start = time.perf_counter()
            # Acting for all actors@static
            if self.frame > 0 and self.frame % self.step == 0:
                self._act_all()
            self.collision_manager.handle_all_collisions()
            self.mouse_manager.update_positions()
            if self.frame == 0:
                self.backgrounds_manager.init_display()
            # run animations
            self.background.update()
            # update all costumes on current background
            self._update_all_costumes()
            self._tick_timed_objects()
        self.frame += 1
        #self.clock.tick(self.fps)
        self.event_manager.update()
        elapsed = time.perf_counter() - start
        wait = max(0, (1 / self.fps) - elapsed)
        await asyncio.sleep(wait)
        

    def _update_all_costumes(self):
        """updates costumes for all actors on the world"""
        [
            actor.costume.update()
            for actor in self.reload_costumes_queue
            if actor.costume
        ]
        self.reload_costumes_queue = []
        # Dynamic actors are updated every frame
        # All other actors are updated when they are created.
        if hasattr(self, "dynamic_actors"):
            [actor.costume.update() for actor in self.dynamic_actors if actor.costume]

    def _act_all(self):
        """Overwritten in subclasses, e.g. physics_world"""
        self.event_manager.act_all()

    def _tick_timed_objects(self):
        [obj.tick() for obj in self.timed_objects]

    def handle_event(self, event, data=None):
        """
        Event handling

        Args:
            event (str): The event which was thrown, e.g. "key_up", "act", "reset", ...
            data: The data of the event (e.g. ["S","s"], (155,3), ...
        """
        self.event_manager.handler.handle_event(event, data)

    def register(self, method: Callable) -> Callable:
        """
        Used as decorator
        e.g.
        @register
        def method...
        """
        self._registered_methods.append(method)
        bound_method = world_inspection.WorldInspection(self).bind_method(method)
        self.event_manager.register_event(method.__name__, self)
        return bound_method

    def unregister(self, method: Callable):
        self._registered_methods.remove(method)
        world_inspection.WorldInspection(self).unbind_method(method)

    @property
    def fill_color(self):
        return self.background.fill_color

    @fill_color.setter
    def fill_color(self, value):
        self.background.fill(value)

    # Alias
    color = fill_color

    def direction(self, point1, point2):
        pass

    @staticmethod
    def distance_to(pos1: Tuple[float, float], pos2: Tuple[float, float]):
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    def direction_to(
        self, pos1: Tuple[float, float], pos2: Tuple[float, float]
    ) -> float:
        return position_manager.Positionmanager.direction_from_two_points(pos1, pos2)

    @property
    def window(self) -> "app_mod.App":
        """
        Gets the parent window

        Returns:
            The window

        """
        return self._window

    def load_world_from_db(self, file: str):
        """
        Loads a sqlite db file.
        """
        return import_factory.ImportWorldFromDB(file, self.__class__).load()

    def load_actors_from_db(
        self, file: str, actor_classes: list
    ) -> List["actor_mod.Actor"]:
        """Loads all actors from db. Usually you load the actors in __init__() or in on_setup()

        Args:
            file (str): reference to db file
            actor_classes (list): a list of all Actor Classes which should be imported.

        Returns:
            [type]: All Actors
        """
        return import_factory.ImportActorsFromDB(file, actor_classes).load()

    def save_to_db(self, file):
        """
        Saves the current world an all actors to database.
        The file is stored as db file and can be opened with sqlite.

        Args:
            file: The file as relative location

        Returns:

        """
        export = export_factory.ExportWorldToDBFactory(file, self)
        export.remove_file()
        export.save()
        export_factory.ExportActorsToDBFactory(file, self.actors).save()

    def screenshot(self, filename: str = "screenshot.jpg"):
        """Creates a screenshot in given file.

        Args:
            filename: The location of the file. The folder must exist. Defaults to "screenshot.jpg".
        """
        pygame.image.save(self.app.window.surface, filename)

    def get_columns_by_width(self, width):
        return width

    def get_rows_by_height(self, height):
        return height

    def get_events(self):
        """Gets a set of all events you can register"""
        print(self.event_manager.class_events_set)