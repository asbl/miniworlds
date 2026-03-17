from __future__ import annotations
from typing import Union, List, Tuple, Optional, cast, Type, TYPE_CHECKING
import pygame.rect
import collections

import miniworlds.actors.actor_appearance_facade as actor_appearance_facade
import miniworlds.actors.actor_event_facade as actor_event_facade
import miniworlds.actors.actor_initialization_facade as actor_initialization_facade
import miniworlds.actors.actor_movement_facade as actor_movement_facade
import miniworlds.actors.actor_sensor_facade as actor_sensor_facade
import miniworlds.actors.actor_size_facade as actor_size_facade
import miniworlds.appearances.appearance as appearance
import miniworlds.appearances.costume as costume_mod
import miniworlds.appearances.costumes_manager as costumes_manager
import miniworlds.worlds.manager.sensor_manager as sensor_manager
import miniworlds.worlds.manager.position_manager as actor_position_manager
import miniworlds.base.exceptions as exceptions
import miniworlds.actors.actor_base as actor_base

from miniworlds.base.exceptions import (
    NotImplementedOrRegisteredError,
    NoWorldError,
    RegisterError,
    NoValidWorldPositionError,
    Missingworldsensor,
    MissingPositionManager,
)

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod


class Actor(actor_base.ActorBase):
    """Actors are objects on your world. Actors can move around the world and have sensors to detect other actors.

    The appearance of a actor is determined by its costume.

    Examples:

        Create a actor:

        .. code-block:: python

            from miniworlds import *

            world = World()
            world.size = (100,60)
            Actor(position=(10, 10))

            world.run()

        Create a actor with an image:

        .. code-block:: python

            from miniworlds import *

            world = World(100,60)
            actor = Actor((10, 10))
            actor.add_costume("images/player.png")

            world.run()

        Create actor as instance from an custom class

        .. code-block:: python

            import miniworlds

            class MyActor(miniworlds.Actor):

                def on_setup(self):
                    self.add_costume("images/player.png")

            world = World(100,60)
            my_actor = MyActor(position = (40,130))
            world.run()

        Create a Actor at current mouse position:

        .. code-block:: python

            from miniworlds import *

            world = World()

            @world.register
            def act(self):
                Actor(self.mouse.get_position())

            world.run()

    See Also:

        * See: :doc:`Actor <../api/actor>`
        * See: :doc:`Shapes <../api/actor_shapes>`
        * See: :doc:`TextActors and NumberActors <../api/actor_text>`
    """

    actor_count: int = 0
    class_image: str = ""

    def __init__(
        self, position: Optional[Tuple[float, float]] = (0, 0), *args, **kwargs
    ):
        self._initialization_facade = actor_initialization_facade.ActorInitializationFacade(self)
        self._get_initialization_facade().prepare_core_references(kwargs.get("world"))
        self._validate_arguments(position, *args, **kwargs)
        self._get_initialization_facade().initialize_runtime_state(Actor.actor_count + 1)
        self._get_initialization_facade().initialize_world_managers(position)
        self._get_initialization_facade().finalize_sprite_state(kwargs.get("origin"))
        Actor.actor_count += 1

    def _get_initialization_facade(
        self,
    ) -> actor_initialization_facade.ActorInitializationFacade:
        facade = getattr(self, "_initialization_facade", None)
        if facade is None:
            facade = actor_initialization_facade.ActorInitializationFacade(self)
            self._initialization_facade = facade
        return facade

    def _get_appearance_facade(self) -> actor_appearance_facade.ActorAppearanceFacade:
        facade = getattr(self, "_appearance_facade", None)
        if facade is None:
            facade = actor_appearance_facade.ActorAppearanceFacade(self)
            self._appearance_facade = facade
        return facade

    def _get_event_facade(self) -> actor_event_facade.ActorEventFacade:
        facade = getattr(self, "_event_facade", None)
        if facade is None:
            facade = actor_event_facade.ActorEventFacade(self)
            self._event_facade = facade
        return facade

    def _get_sensor_facade(self) -> actor_sensor_facade.ActorSensorFacade:
        facade = getattr(self, "_sensor_facade", None)
        if facade is None:
            facade = actor_sensor_facade.ActorSensorFacade(self)
            self._sensor_facade = facade
        return facade

    def _get_movement_facade(self) -> actor_movement_facade.ActorMovementFacade:
        facade = getattr(self, "_movement_facade", None)
        if facade is None:
            facade = actor_movement_facade.ActorMovementFacade(self)
            self._movement_facade = facade
        return facade

    def _get_size_facade(self) -> actor_size_facade.ActorSizeFacade:
        facade = getattr(self, "_size_facade", None)
        if facade is None:
            facade = actor_size_facade.ActorSizeFacade(self)
            self._size_facade = facade
        return facade

    def _validate_arguments(self, position, *args, **kwargs):
        if not isinstance(position, tuple):
            raise exceptions.NoValidPositionOnInitException(self, position)

    @property
    def origin(self):
        return self._get_size_facade().get_origin()

    @origin.setter
    def origin(self, value: str):
        self._get_size_facade().set_origin(value)

    def switch_origin(self, value: str):
        self._get_size_facade().switch_origin(value)

    @classmethod
    def create_on_world(cls, world):
        """Creates a actor to a specific world

        overwritten in subclasses
        """
        return cls((0, 0), world)

    @property
    def collision_type(self) -> str:
        """collision_type specifies how collisions should be checked:

        * `default`: tile for Tiledworlds, 'mask' for Pixelworlds

        * `tile`: Are actors on the same tile? (only TiledWorld)

        * `rect`: Are actors colliding when checking their bounding - boxes? (Only PixelWorld)

        * `static-rect`: Are actors colliding when checking circle with radius = bounding-box-radius.(Only PixelWorld)

        * `circle`: Are actors colliding when checking circle with radius = bounding-box-radius.(Only PixelWorld)

        * `mask`: Are actors colliding when checking if their image masks are overlapping.
        """
        if self._collision_type == "default":
            return "mask"
        else:
            return self._collision_type

    @collision_type.setter
    def collision_type(self, value: str):
        self._collision_type = value

    @property
    def is_blockable(self):
        """
        A actor with the property ``is_blockable`` cannot move through actors with the property ``is_blocking``.
        """
        return self.position_manager.is_blockable

    @is_blockable.setter
    def is_blockable(self, value: bool):
        self.position_manager.is_blockable = value

    @property
    def is_blocking(self):
        """
        A actor with the property ``is_blockable`` cannot move through actors with the property ``is_blocking``.
        """
        return self.position_manager.is_blocking

    @is_blocking.setter
    def is_blocking(self, value: bool):
        previous_value = self.position_manager.is_blocking
        self.position_manager.is_blocking = value
        world = self.world
        if previous_value == value or world is None:
            return
        if hasattr(world, "get_world_connector"):
            connector = world.get_world_connector(self)
            if connector is not None and hasattr(connector, "sync_blocking_registration"):
                connector.sync_blocking_registration(previous_value, value)
                return
        if hasattr(world, "_blocking_actors"):
            if value:
                world._blocking_actors.add(self)
            else:
                world._blocking_actors.discard(self)

    @property
    def layer(self) -> int:
        """Defines the layer on which the actor is drawn if several actors overlap."""
        return self._layer

    @layer.setter
    def layer(self, value: int):
        self._layer = value
        if self in self.world.actors:
            self.world.actors.change_layer(
                self, value
            )  # changes layer in DirtySpriteGroup.

    @property
    def last_position(self) -> Tuple[float, float]:
        """Actor position in last frame

        Can be used to track changes.
        """
        return self._get_size_facade().get_last_center()

    @property
    def last_direction(self) -> int:
        return self._get_size_facade().get_last_direction()

    @classmethod
    def from_topleft(cls, topleft_position: Tuple[float, float], *args, **kwargs):
        """
        Creates a actor with center at center_position

        Arg`s:
            center_position: Center of actor
        """
        obj = cls(topleft_position, **kwargs)  # temp position
        obj.origin = "topleft"
        return obj

    @classmethod
    def from_center(cls, center_position: Tuple[float, float], *args, **kwargs):
        """
        Creates a actor with center at center_position

        Arg`s:
            center_position: Center of actor
        """
        obj = cls(center_position, **kwargs)  # temp position
        obj.origin = "center"
        return obj

    @property
    def costume_count(self) -> int:
        """Returns number of costumes of actor, 0 if actor has no costume

        Examples:

            Add costume and count costumes

            .. code-block:: python

                from miniworlds import *
                world = World()
                actor = Actor()
                assert actor.costume_count == 0
                actor.add_costume((255,0,0,0))
                assert actor.costume_count == 1
                world.run()


        Returns:
            int: _description_
        """
        return self._get_appearance_facade().costume_count

    @property
    def is_flipped(self) -> bool:
        """
        When a actor is mirrored, it is mirrored across the y-axis.
        You can use this property in 2D platformer games to change the direction of actor.

        .. note::

            It may be necessary to set ``is_rotatable = True``

        Examples:

            Flip a costume after 100 frames.

            .. code-block::

                from miniworlds import *

                world = World(100,100)
                actor = Actor()
                actor.add_costume("images/alien1.png")
                actor.height= 400
                actor.width = 100
                actor.is_rotatable = False
                @actor.register
                def act(self):
                    if self.world.frame % 100 == 0:
                        if self.is_flipped:
                            self.is_flipped = False
                        else:
                            self.is_flipped = True
                world.run()

            Output:

            .. raw:: html

                <video loop autoplay muted width=200>
                <source src="../_static/# It looks like the code `flip_alien` is not a valid Python
                # code. It seems to be a placeholder or a random string. If
                # you provide more context or details about what you are
                # trying to achieve, I can help you with the code.
                flip_alien.webm" type="video/webm">
                Your browser does not support the video tag.
                </video>

        Returns:
            True, if actor is flipped

        """
        return self._get_appearance_facade().is_flipped

    @is_flipped.setter
    def is_flipped(self, value: bool):
        self._get_appearance_facade().is_flipped = value

    def flip_x(self) -> int:
        """Flips the actor by 180° degrees. The costume is flipped and the actor's direction changed by 180 degrees.

        .. image:: ../_images/flip_x.png

        Examples:

            Flip a actor in Example flipthefish.py

            .. code-block:: python

                from miniworlds import *

                world=TiledWorld()
                world.columns = 4
                world.rows = 1
                world.add_background("images/water.png")
                fish = Actor()
                fish.border = 1
                fish.add_costume("images/fish.png")
                fish.direction = "right"
                fish.orientation = -90
                @fish.register
                def act(self):
                    self.move()

                @fish.register
                def on_not_detecting_world(self):
                    self.move_back()
                    self.flip_x()

                world.run()

            Output:

            .. raw:: html

                <video loop autoplay muted width=200>
                <source src="../_static/flipthefish.webm" type="video/webm">
                Your browser does not support the video tag.
                </video>

        """
        return self._get_appearance_facade().flip_x()

    def add_costume(
        self, source: Union[None, Tuple, str, List] = None
    ) -> "costume_mod.Costume":
        """Adds a new costume to actor.
        The costume can be switched with self.switch_costume(index)

        Args:
            source: Path to the first image of new costume or Tuple with color-value

        Examples:

            Add first costume from image:

            .. code-block:: python

                from miniworlds import *

                world = World(100,60))
                actor = Actor((10,10))
                costume = actor.add_costume("images/player.png")

                world.run()


            Output:

            .. image:: ../_images/add_costume1.png
                :width: 100px
                :alt: Create Actor with image as costume

            Add first costume from color:

            .. code-block:: python

                from miniworlds import *

                world = World(100,60))
                actor = Actor((10,10))
                costume = actor.add_costume((255,255,0))

                world.run()

            Output:

            .. image:: ../_images/add_costume2.png
                :width: 100px
                :alt: Create Actor with image as costume


            Create two costumes and switch between costumes

            .. code-block:: python

                from miniworlds import *

                world = World(100,60))
                actor = Actor((10,10))
                world.speed = 30
                costume1 = actor.add_costume((255,255,0))
                costume2 = actor.add_costume((255,0,255))
                @actor.register
                def act(self):
                    if self.costume == costume1:
                        self.switch_costume(costume2)
                    else:
                        self.switch_costume(costume1)

                world.run()

            Output:

            .. image:: ../_images/add_costume3.png
                :width: 100%
                :alt: Create multiple costumes and switch between costumes

        Returns:
            The new costume.

        """
        return self._get_appearance_facade().add_costume(source)

    def add_costumes(self, sources: list) -> "costume_mod.Costume":
        """Adds multiple costumes"""
        return self._get_appearance_facade().add_costumes(sources)

    def remove_costume(self, source: Union[int, "costume_mod.Costume"] = None):
        """Removes a costume from actor

        Args:
            source: The index of the new costume or costume-object. Defaults to actual costume
        """
        return self._get_appearance_facade().remove_costume(source)

    def switch_costume(
        self, source: Union[int, "appearance.Appearance"]
    ) -> "costume_mod.Costume":
        """Switches the costume of actor

        Args:
            source: Number of costume or Costume object

        Examples:

            Switch a costume:

            .. code-block:: python

                from miniworlds import *

                world = World(100,60)
                t = Actor()
                costume =t1.add_costume("images/1.png")
                t.add_costume("images/2.png")
                t.switch_costume(1)

                @timer(frames = 40)
                def switch():
                    t1.switch_costume(0)

                world.run()

        Returns:
            The new costume
        """
        return self._get_appearance_facade().switch_costume(source)

    def set_costume(self, costume: Union[str, tuple, int, "appearance.Appearance"]):
        self._get_appearance_facade().set_costume(costume)

    def reset_costumes(self):
        self._get_appearance_facade().reset_costumes()

    def set_background_color(self, color: tuple):
        self._get_appearance_facade().set_background_color(color)

    def next_costume(self):
        """Switches to the next costume of actor

        Returns:
            The new costume
        """
        self._get_appearance_facade().next_costume()

    @property
    def costume(self) -> costume_mod.Costume:
        """Gets the costume of the actor, if available."""
        return self._get_appearance_facade().costume

    def has_costume(self) -> bool:
        return self._get_appearance_facade().has_costume()

    @costume.setter
    def costume(self, value):
        self._get_appearance_facade().costume = value

    @property
    def costumes(self) -> "costumes_manager.CostumesManager":
        """Gets the costume manager

        The costume manager can be iterated to get all costumes
        """
        return self._get_appearance_facade().costumes

    @property
    def orientation(self) -> float:
        return self._get_appearance_facade().orientation

    @orientation.setter
    def orientation(self, value: float):
        self._get_appearance_facade().orientation = value

    @property
    def direction(self) -> int:
        """Directions are handled exactly as in the Scratch programming language,
        see: `Scratch Wiki <https://en.scratch-wiki.info/wiki/Direction_(value)>`_

        The default direction is ``0°``. All actors are looking ``"up"``

        .. image:: /_images/movement.jpg
            :width: 100%
            :alt: Move on world

        **Values for Direction**

        * ``0°`` or ``"up"``: up
        * ``90°`` or ``"right"``: Move right
        * ``-90°`` or ``"left"``: Move left
        * ``180°`` or ``"down"``: Move down
        * ``"forward"``: Current direction

        Sets direction of the actor.

        You can use an integer or a string to describe the direction

        Options
            * ``0``, ``"up"`` - Look up
            * ``90``, ``"right"``, - Look right
            * ``-90``, ``"left"``, - Look left
            * ``-180``, ``180``, ``"down"`` - Look down

        .. image:: ../_images/direction.png

        Examples:

            Move in a direction with WASD-Keys

            .. code-block:: python

                def on_key_down(self, keys):
                    if "W" in keys:
                        self.direction = "up"
                    elif "S" in keys:
                        self.direction = "down"
                    elif "A" in keys:
                        self.direction = "left"
                    elif "D" in keys:
                        self.direction = "right"
                    self.move()

            Move 45°:

            .. code-block:: python

                from miniworlds import *

                world = World(100, 100)
                c = Circle ((50,50), 10)

                @c.register
                def act(self):
                    c.direction = 45
                    c.move()

                world.run()


            .. raw:: html

                <video loop autoplay muted width=400>
                <source src="../_static/move45.webm" type="video/webm">
                Your browser does not support the video tag.
                </video>

            Move -45°:

            .. code-block:: python

                from miniworlds import *

                world = World(100, 100)
                c = Circle ((50,50), 10)

                @c.register
                def act(self):
                    c.direction = -45
                    c.move()

                world.run()

            .. raw:: html

                <video loop autoplay muted width=400>
                <source src="../_static/moveminus45.webm" type="video/webm">
                Your browser does not support the video tag.
                </video>
        """
        return self._get_movement_facade().get_direction()

    @direction.setter
    def direction(self, value: int):
        self._get_movement_facade().set_direction(value)

    @property
    def direction_at_unit_circle(self) -> int:
        """Gets the direction as value in unit circle (0° right, 90° top, 180° left...)"""
        return self._get_movement_facade().get_direction_at_unit_circle()

    @direction_at_unit_circle.setter
    def direction_at_unit_circle(self, value: int):
        """Sets the direction from unit circle
        Args:
            value: An angle in the unit circle, e.g. 0°: right, 90° top, ...
        """
        self._get_movement_facade().set_direction_at_unit_circle(value)

    def turn_left(self, degrees: int = 90) -> int:
        """Turns actor by *degrees* degrees left

        .. image:: ../_images/turn_left.png

        Options:
          * You can set the value actor.is_rotatable = False if you don't want the actor to be rotated.

        Examples:

            .. code-block:: python

                from miniworlds import *

                world = World(100, 100)
                t = Actor()
                t.add_costume("images/arrow.png")
                t.size = (100,100)

                @t.register
                def act(self):
                    t.turn_left(1)

                world.run()

            Output:

            .. raw:: html

                <video loop autoplay muted width=400>
                <source src="../_static/turnleft.webm" type="video/webm">
                Your browser does not support the video tag.
                </video>

        Args:
            degrees: degrees in left direction

        Returns:
            New direction

        """
        return self._get_movement_facade().turn_left(degrees)

    def turn_right(self, degrees: Union[int, float] = 90):
        """Turns actor by *degrees* degrees right

        .. image:: ../_images/turn_right.png

        Examples:

            .. code-block:: python

                from miniworlds import *

                world = World(100, 100)
                t = Actor()
                t.add_costume("images/arrow.png")
                t.size = (100,100)

                @t.register
                def act(self):
                    t.turn_left(1)

                world.run()

        Output:

        .. raw:: html

            <video loop autoplay muted width=400>
            <source src="../_static/turnright.webm" type="video/webm">
            Your browser does not support the video tag.
            </video>

        Options:
          * You can set the value actor.is_rotatable = False if you don't want the actor to be rotated.

        Args:
            degrees: degrees in left direction

        Returns:
            New direction

        """
        return self._get_movement_facade().turn_right(degrees)

    def set_direction(self, direction: Union[str, int, float]) -> float:
        """Actor points in given direction.

        You can use a integer or a string to describe the direction

        Args:
            The direction as integer or string (see options)

        Options
            * ``0``, ``"up"`` - Look up
            * ``90``, ``"right"``, - Look right
            * ``-90``, ``"left"``, - Look left
            * ``-180``, ``180``, ``"down"`` - Look down

        .. image:: ../_images/direction.png

        Examples:

            Move in a direction with WASD-Keys

            .. code-block:: python

              def on_key_down(self, keys):
                  if "W" in keys:
                      self.direction = "up"
                  elif "S" in keys:
                      self.direction = "down"
                  elif "A" in keys:
                      self.direction = "left"
                  elif "D" in keys:
                      self.direction = "right"
                  self.move()
        """
        return self._get_movement_facade().set_direction_value(direction)

    def point_towards_position(
        self, destination: Tuple[float, float]
    ) -> Union[int, float]:
        """
        Actor points towards a given position

        Args:
            destination: The position to which the actor should pointing

        Returns:
            The new direction

        Examples:

            Point towards mouse_position:

            .. code-block:: python

                def act(self):
                    mouse = self.world.mouse.get_position()
                if mouse:
                    self.point_towards_position(mouse)
                self.move()
        """
        return self._get_movement_facade().point_towards_position(destination)

    def point_towards_actor(self, other: "Actor") -> int:
        """Actor points towards another actor.

        Args:
            other: The other actor

        Returns:
            The new direction

        """
        return self._get_movement_facade().point_towards_actor(other)

    @property
    def size(self) -> tuple:
        """Size of the actor"""
        return self._get_size_facade().get_size()

    @size.setter
    def size(self, value: tuple):
        self.set_size(value)

    def set_size(self, value: tuple):
        self._get_size_facade().set_size(value)

    @property
    def width(self):
        """The width of the actor in pixels.

        When the width of a actor is changed, the height is scaled proportionally.

        Examples:

            Create a actor and scale width/height proportionally:

            .. code-block:: python

                from miniworlds import *

                world = World(800,400)

                def create_actor(x, y):
                t = Actor()
                t.position = (x, y)
                t.add_costume("images/alien1.png")
                t.border = 1
                return t

                t0 = create_actor(0,0)
                t1 = create_actor(50,0)
                t1.height = 400
                t2 = create_actor(300,0)
                t2.width = 180

                world.run()

            .. image:: ../_images/widthheight.png
                :alt: Textured image
        """
        return self._get_size_facade().get_width()

    @width.setter
    def width(self, value):
        self._get_size_facade().set_width(value)

    def scale_width(self, value):
        self._get_size_facade().scale_width(value)

    @property
    def height(self):
        """The height of the actor in pixels.

        When the height of a actor is changed, the width is scaled proportionally.

        Examples:

            Create a actor and scale width/height proportionally:

            .. code-block:: python

                from miniworlds import *

                world = World(800,400)

                def create_actor(x, y):
                t = Actor()
                t.position = (x, y)
                t.add_costume("images/alien1.png")
                t.border = 1
                return t

                t0 = create_actor(0,0)
                t1 = create_actor(50,0)
                t1.height = 400
                t2 = create_actor(300,0)
                t2.width = 180

                world.run()

            .. image:: ../_images/widthheight.png
                :alt: Textured image
        """
        return self._get_size_facade().get_height()

    @height.setter
    def height(self, value):
        self._get_size_facade().set_height(value)

    def scale_height(self, value):
        self._get_size_facade().scale_height(value)

    @property
    def x(self) -> float:
        """The x-value of a actor"""
        return self._get_movement_facade().get_x()

    @x.setter
    def x(self, value: float):
        self._get_movement_facade().set_x(value)

    @property
    def y(self) -> float:
        """The y-value of a actor"""
        return self._get_movement_facade().get_y()

    @y.setter
    def y(self, value: float):
        self._get_movement_facade().set_y(value)

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    @property
    def topleft_x(self) -> float:
        """x-value of actor topleft-position"""
        return self._get_movement_facade().get_topleft_x()

    @property
    def topleft_y(self) -> float:
        """x-value of actor topleft-position"""
        return self._get_movement_facade().get_topleft_y()

    @topleft_x.setter
    def topleft_x(self, value: float):
        self._get_movement_facade().set_topleft_x(value)

    @topleft_y.setter
    def topleft_y(self, value: float):
        self._get_movement_facade().set_topleft_y(value)

    @property
    def topleft(self) -> Tuple[float, float]:
        return self._get_movement_facade().get_topleft()

    @topleft.setter
    def topleft(self, value: Tuple[float, float]):
        self._get_movement_facade().set_topleft(value)

    @property
    def local_center(self) -> Tuple[float, float]:
        """x-value of actor center-position inside the current camera-screen"""
        return self._get_movement_facade().get_local_center()

    @property
    def center_x(self) -> float:
        """x-value of actor center-position"""
        return self._get_movement_facade().get_center_x()

    @center_x.setter
    def center_x(self, value: float):
        self._get_movement_facade().set_center_x(value)

    @property
    def center_y(self) -> float:
        """y-value of actor center-position"""
        return self._get_movement_facade().get_center_y()

    @center_y.setter
    def center_y(self, value: float):
        self._get_movement_facade().set_center_y(value)

    @property
    def center(self) -> Tuple[float, float]:
        return self._get_movement_facade().get_center()

    @center.setter
    def center(self, value: Tuple[float, float]):
        self._get_movement_facade().set_center(value)

    def move(self, distance: int = 0, direction: int = 0):
        """Moves actor *distance* steps in current direction

        .. image:: ../_images/move.png

        Args:
            distance: Number of steps to move.
              If distance = 0, the actor speed will be used.

        Returns:
            The moved actor

        Examples:

            if actor is on the world, move forward:

            .. code-block:: python

                class Robot(Actor):

                    def act(self):
                        if self.detecting_world():
                            self.move()
        """
        return self._get_movement_facade().move(distance, direction)

    def move_vector(self, vector):
        """Moves actor in direction defined by the vector

        Returns:
            The moved actor

        """
        return self._get_movement_facade().move_vector(vector)

    def move_back(self, distance):
        """ """
        return self._get_movement_facade().move_back(distance)

    def undo_move(self):
        """Undo the last move. Moves the actor to the last position and resets direction.

        .. image:: ../_images/move_back.png

        Returns:
            The moved actor

        Examples:

            move_back when field is blocked:

            .. code-block:: python

                def on_detecting_wall(self, wall):
                    self.undo_move()

        """
        return self._get_movement_facade().undo_move()

    def move_towards(self, target: Union[Tuple[float, float], "Actor"]):
        return self._get_movement_facade().move_towards(target)

    def move_in_direction(
        self,
        direction: Union[int, str, Tuple[float, float]],
        distance=1,
    ):
        """Moves actor *distance* steps into a *direction* or towards a position

        .. image:: ../_images/move_in_direction.png

        Options
            * 0, "up" - Look up
            * 90, "right", - Look right
            * -90, "left", - Look left
            * -180, 180, "down" - Look down

        .. image:: ../_images/direction.png

        Args:
            direction: Direction as angle
            distance: Detects obj "distance" steps in front of current actor.

        Returns:
            The actor itself

        """
        return self._get_movement_facade().move_in_direction(direction, distance)

    def move_to(self, position: Tuple[float, float]):
        """Moves actor *distance* to a specific world_posiition

        Args:
            position: The position to which the actor should move. The position can be a 2-tuple (x, y)
            which will be converted to a world_position

        .. image:: ../_images/move_to.png

        Returns:
            The actor itself

        Examples:

            move to (3, 2) on mouse_click

            .. code-block:: python

                def on_clicked_left(self, position):
                    self.move_to((3,2))


        """
        return self._get_movement_facade().move_to(position)

    def remove(self, kill=True) -> collections.defaultdict:
        """
        Removes this actor from world

        Examples:

            Removes robots in thecrash.py :

            .. code-block:: python

               def act(self):
                   self.move()
                   other = self.detecting_actor(distance = 0, actor_type=Robot)
               if other:
                   explosion = Explosion(position=self.position)
                   self.remove()
                   other.remove()
        """
        return self.world.get_world_connector(self).remove_actor_from_world(kill=kill)
        
        
    def before_remove(self):
        pass
    
    @property
    def is_rotatable(self) -> bool:
        """Defines if the costume of a actor should be rotatable. The actor can still be rotated with
        the ``direction`` property, but its costume won't be changed

        .. note::

            You can also use ``actor.costume.is_rotatable``

        Examples:

            Create a rotatable and a not rotatable actor

            .. code-block::

                from miniworlds import *
                world = World()

                t1 = Actor((100,100))
                t1.add_costume("images/alien1.png")

                t2 = Actor((200,200))
                t2.add_costume("images/alien1.png")
                t2.is_rotatable = False

                @t1.register
                def act(self):
                    self.move()
                    self.direction += 1

                @t2.register
                def act(self):
                    self.move()
                    self.direction += 1

                world.run()


            Output:

            .. raw:: html

                <video loop autoplay muted width=400>
                <source src="../_static/rotatable.webm" type="video/webm">
                Your browser does not support the video tag.
                </video>

        """
        return self.costume.is_rotatable

    @is_rotatable.setter
    def is_rotatable(self, value: bool):
        self.costume.is_rotatable = value

    def bounce_from_border(self, borders: List[str]) -> Actor:
        """The actor "bounces" from a border.

        The direction is set according to the principle input angle = output angle.

        .. note::

          You must check for borders first!

        Args:
            borders: A list of borders as strings e.g. ["left", "right"]

        Examples:

            .. code-block:: python

                from miniworlds import *
                import random

                world = World(150, 150)
                actor = Actor((50,50))
                actor.add_costume("images/ball.png")
                actor.direction = 10

                @actor.register
                def act(self):
                    self.move()
                    borders = self.detecting_borders()
                    if borders:
                        self.bounce_from_border(borders)

                world.run()

            Output:

            .. raw:: html

                <video loop autoplay muted width=240>
                <source src="../_static/bouncing_ball.webm" type="video/webm">
                Your browser does not support the video tag.
                </video>


        Returns:
            The actor

        """
        return self.position_manager.bounce_from_border(borders)

    def detect_all(
        self,
        actors: Union[str, "Actor", Type["Actor"]] = None,
        direction: int = 0,
        distance: int = 0,
    ) -> List["Actor"]:
        """Detects if actors are on actor position.
        Returns a list of actors.

        Args:
            actors: filter by actor type. Enter a class_name of actors to look for here
            direction: The direction in which actors should be detected.
            distance:  The distance in which actors should be detected (Start-Point is actor.center)

        Returns:
            All actors found by Sensor

        """
        return self._get_sensor_facade().detect_all(actors, direction, distance)

    def detect(self, *args, **kwargs) -> Union["Actor", None]:
        """Detects if actors are on actor position.
        Returns the first found actor.

        Args:
            actors: filter by actor type. Enter a class_name of actors to look for heredirection: int = 0, distance: int = 0
            direction: The direction in which actors should be detected.
            distance:  The distance in which actors should be detected (Start-Point is actor.center)

        Returns:

            First actor found by Sensor

        Examples:

            The green robot pushes the yellow robot:

            .. code-block:: python

                from miniworlds import *

                world = TiledWorld(8,3)
                actor = Actor((1,1))
                actor.add_costume("images/robo_green.png")
                actor.orientation = -90
                actor.direction = 90

                actor2 = Actor((4,1))
                actor2.add_costume("images/robo_yellow.png")
                actor2.orientation = -90
                actor2.direction = -90

                @actor.register
                def act(self):
                    self.move()
                    actor = self.detecting_actor()
                    if actor:
                        actor.move_right()
                world.run()

            Output:

            .. raw:: html

                <video loop autoplay muted width=240>
                <source src="../_static/pushing.webm" type="video/webm">
                Your browser does not support the video tag.
                </video>
        """
        return self._get_sensor_facade().detect(*args, **kwargs)

    def detect_borders(
        self,
        distance: int = 0,
    ) -> List:
        """
        Detects borders

        Args:

            distance: Specifies the distance in front of the actuator to which the sensors reacts.

        Returns:

            True if border was found.

        """
        return self._get_sensor_facade().detect_borders(distance)

    def detect_left_border(self) -> bool:
        """Does the actor touch the left border?

        Returns:
            True if border was found.

        """
        return self._get_sensor_facade().detect_left_border()

    def detect_right_border(self) -> bool:
        """Does the actor touch the right border?

        Returns:
            True if border was found.

        """
        return self._get_sensor_facade().detect_right_border()

    def detect_top_border(self) -> bool:
        """Does the actor touch the lower border?

        Returns:
            True if border was found.

        """
        return self._get_sensor_facade().detect_top_border()

    def detecting_bottom_border(self) -> bool:
        """Does the actor touch the lower border?

        Returns:
            True if border was found.

        """
        return self._get_sensor_facade().detecting_bottom_border()

    def detect_color(self, color: Tuple = None) -> bool:
        """Detects colors in world-background at actor center-position

        Args:
            color: color as tuple

        Returns:
            True, if color was found

        """
        return self._get_sensor_facade().detect_color(color)

    def detect_color_at(
        self, direction: int = None, distance: int = 0
    ) -> Union[Tuple, List]:
        """Detects colors in world-background at actor-position

        Args:
            direction: Specifies the direction where the sensors is searching.
            distance: Specifies the distance in front of the actuator to which the sensors reacts.

        Returns:
            All colors found by Sensor

        """
        return self._get_sensor_facade().detect_color_at(direction, distance)

    def detect_actors_at(self, direction=None, distance=0, actors=None) -> list:
        """Detects a actor in given direction and distance.

        Examples:

          .. code-block:: python

            from miniworlds import *
            world = World()
            wall=Rectangle((200,0))
            wall.size = (20, 400)

            for i in range(7):
                actor = Circle((10,i*60 + 20))
                actor.range = i * 10
                @actor.register
                def act(self):
                    if not self.detect_actors_at(self.direction, self.range):
                        self.direction = "right"
                        self.move()

            world.run()


        :param direction: The direction in which actors should be detected.
        :param distance:  The distance in which actors should be detected (Start-Point is actor.center)
        :return: A list of actors
        """
        return self._get_sensor_facade().detect_actors_at(direction, distance, actors)

    def detect_actor_at(self, direction=None, distance=0, actors=None) -> "Actor":
        return self._get_sensor_facade().detect_actor_at(direction, distance, actors)

    def detect_actors_in_front(
        self,
        actors=None,
        distance=1,
    ) -> list:
        return self._get_sensor_facade().detect_actors_in_front(actors, distance)

    def detect_actor_in_front(
        self,
        actors=None,
        distance=1,
    ) -> "Actor":
        return self._get_sensor_facade().detect_actor_in_front(actors, distance)

    def detect_point(self, position: Tuple[float, float]) -> bool:
        """Is the actor colliding with a specific (global) point?

        Warning:
            If your want to check if an actor detects a specific pixel, use detect_pixel
            
        Returns:
            True if point is below actor
        """
        return self._get_sensor_facade().detect_point(position)
    
    def detect_pixel(self, position: Tuple[float, float]) -> bool:
        """Is the actor colliding with a pixel?

        Returns:
            True if pixel is below actor
        """
        return self._get_sensor_facade().detect_pixel(position)

    def detect_rect(self, rect: Union[Tuple, pygame.rect.Rect]):
        """Is the actor colliding with a static rect?"""
        return self._get_sensor_facade().detect_rect(rect)

    def is_inside_world(self):
        """Is the actor colliding with current ...."""
        return self._get_sensor_facade().is_inside_world()

    def bounce_from_actor(self, other: "Actor"):
        self._get_sensor_facade().bounce_from_actor(other)

    def animate(self, speed: int = 10):
        self.costume_manager.animate(speed)

    def animate_costume(self, costume: "costume_mod.Costume", speed: int = 10):
        self.costume_manager.animate_costume(costume, speed)

    def animate_loop(self, speed: int = 10):
        """Animates a costume with a looping animation

        Switches through all costume-images every ``speed``-frame.

        Examples:

            .. code-block:: python

                from miniworlds import *

                world = World(columns=280, rows=100)
                robo = Actor(position=(0, 0))
                robo.costume.add_images(["images/1.png", "images/2.png","images/3.png","images/4.png"])
                robo.size = (99, 99)
                robo.animate_loop()
                world.run()

        Args:
            speed (int, optional): Every ``speed`` frame, the image is switched. Defaults to 10.
        """
        self.costume.loop = True
        self.costume_manager.animate(speed)

    def stop_animation(self):
        """Stops current animation.
        Costume ``is_animated`` is set to False


        Examples:

            .. code-block:: python

                from miniworlds import *

                world = World(columns=280, rows=100)
                robo = Actor(position=(0, 0))
                robo.costume.add_images(["images/1.png", "images/2.png","images/3.png","images/4.png"])
                robo.size = (99, 99)
                robo.animate_loop()
                @timer(frames = 100)
                def stop():
                    robo.stop_animation()
                world.run()
        """
        self.costume.is_animated = False

    def send_message(self, message: str):
        """Sends a message to world.

        The message can be received with the ``on_message``-event

        Examples:

            Send and receive messages:

            .. code-block:: python

                from miniworlds import *

                world = World()

                actor1 = Actor((2, 2))
                actor1.add_costume((100,0,100,100))

                @actor1.register
                def on_message(self, message):
                    print("Received message:" + message)

                actor2 = Actor((100,100))
                actor2.send_message("Hello from actor2")

                @actor2.register
                def on_key_down_s(self):
                    self.send_message("Hello")
                world.run()

        Args:
            message (str): A string containing the message.
        """
        self._get_event_facade().send_message(message)

    def on_key_down(self, key: list):
        """**on_key_down**  is called one time when a key is pressed down.

        .. note::
            Instead of **on_key_down** you can use **on_key_down_letter**, e.g. **on_key_down_a** or **on_key_down_w**
            , if you want to handle an on_key_down event for a specific letter.

        Examples:

            Register a key_down event:

            .. code-block::

                actor1 = miniworlds.Actor(position = (2, 2) )
                actor1.add_costume((100,0,100,100))

                @actor1.register
                def on_key_down(self, key):
                    print(key)

            Register on_key_down_a event

            .. code-block::

                actor1 = miniworlds.Actor(position = (2, 2) )
                actor1.add_costume((100,0,100,100))

                @actor1.register
                def on_key_down_a(self):
                    print("a")

        Args:
            key (list): The typed key as list (e.g. ['A', 'a']) containing both uppercase and lowercase of typed letter.

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_key_down)

    def on_key_pressed(self, key: list):
        """**on_key_pressed** is called when while key is pressed. If you hold the key, on_key_pressed
        is repeatedly called again and again until the key is released.

        .. note::

            Like `on_key_down` the method can be called in the variant `on_key_pressed_[letter]`
            (e.g. `on_key_pressed_w(self)`).

        Examples:

            Register on_key_pressed event:

            .. code-block::

                actor1 = miniworlds.Actor(position = (2, 2) )
                actor1.add_costume((100,0,100,100))

                @actor1.register
                def on_key_pressed(self, key):
                    print("pressed", key)

                @actor1.register
                def on_key_pressed_s(self):
                    print("pressed s")

        Args:
            key (list): The typed key as list (e.g. ['C', 'c', 'D', 'd']) containing both uppercase and lowercase
            of typed letter.

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_key_pressed)

    def on_key_up(self, key):
        raise NotImplementedOrRegisteredError(self.on_key_up)

    def on_mouse_over(self, position):
        """on_mouse_over is called, when mouse is moved over actor
        :param position: The mouse position
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_over)

    def on_mouse_leave(self, position):
        """on_mouse_over is called, when mouse is moved over actor
        :param position: The mouse position
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_over)

    def on_mouse_left_down(self, position: tuple):
        raise NotImplementedOrRegisteredError(self.on_mouse_left_down)

    def on_mouse_right_down(self, position: tuple):
        raise NotImplementedOrRegisteredError(self.on_mouse_left_down)

    def on_mouse_left(self, position: tuple):
        """on_mouse_left is called when left mouse button was pressed.
        You must *register* or *implement* this method as an event.

        .. note::

            The event is triggered, when mouse-left was clicked, even when the current mouse position
            is not related to actor position.

            You can use :py:meth:`Actor.detect_pixel` to check, if the mouse_position is *inside* the actor.

        Examples:

            A circle will be moved, if you click on circle.

            .. code-block::

                from miniworlds import *

                world = World(120,40)
                circle = Circle((20, 20))
                circle.direction = 90

                @circle.register
                def on_mouse_left(self, mouse_pos):
                    if self.detect_pixel(mouse_pos):
                        self.move()

                world.run()

        Args:
            position (tuple): Actual mouse position as tuple (x,y)

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """

        raise NotImplementedOrRegisteredError(self.on_mouse_left)

    def on_mouse_right(self, position: tuple):
        """Method is called when right mouse button was pressed.
        You must *register* or *implement* this method as an event.

        .. note::

            The event is triggered, when mouse was clicked,even when the current mouse position is not related
            to actor position.

            You can use :py:meth:`Actor.detect_pixel` to check, if the mouse_position is *inside* the actor.

        Examples:

            See: :py:meth:`Actor.on_mouse_left`.

        Args:
            position (tuple): Actual mouse position as tuple (x,y)

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_right)

    def on_mouse_motion(self, position: tuple):
        """Method is called when mouse moves. You must *register* or *implement* this method as an event.

        .. note::

            The event is triggered, when mouse is moved, even when the current mouse position
            is not related to actor position.

            You can use :py:meth:`Actor.detect_pixel` to check, if the mouse_position is *inside* the actor.

        Examples:

            A circle will be moved, if you click on circle.

            .. code-block::

                from miniworlds import *

                world = World(120,40)
                circle = Circle((20, 20))
                circle.direction = 90

                @circle.register
                def on_mouse_motion(self, mouse_pos):
                    if self.detect_pixel(mouse_pos):
                        self.move()

                world.run()

        Args:
            position (tuple): Actual mouse position as tuple (x,y)

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_motion)

    def on_mouse_left_released(self, position: tuple):
        """Method is called when left mouse key is released.

        Examples:

            You can use on_mouse_left_release to implement a drag_and_drop event

            .. code-block::

                from miniworlds import *

                world = World(200, 200)
                circle = Circle((30, 30), 60)
                circle.direction = 90
                circle.dragged = False

                @circle.register
                def on_mouse_left(self, mouse_pos):
                    if self.detect_pixel(mouse_pos):
                        self.dragged = True

                @circle.register
                def on_mouse_left_released(self, mouse_pos):
                    if not world.is_mouse_pressed():
                        self.dragged = False
                        self.center = mouse_pos

                world.run()

            Output:

            .. raw:: html

                <video loop autoplay muted width=200>
                <source src="../_static/draganddrop.webm" type="video/webm">
                Your browser does not support the video tag.
                </video>


        Args:
            position (tuple): Actual mouse position as tuple (x,y)

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_left_released)

    def on_mouse_right_released(self, position: tuple):
        """Method is called when right mouse key is released. See :py:meth:`Actor.on_mouse_left_released`.


        Args:
            position (tuple): Actual mouse position as tuple (x,y)

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_right_released)

    def on_clicked_left(self, position: tuple):
        """The mouse is on top of a actor and mouse was clicked.

        Examples:

            Registering a on_click event:

            .. code-block::

                actor = miniworlds.Actor((2,2))

                @actor.register
                def on_clicked_left(self, position):
                    print("clicked" + str(position))


        Args:
            position (tuple): Actual mouse position as tuple (x,y)

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_clicked_left)

    def on_clicked_right(self, position):
        """The mouse is on top of a actor and mouse was clicked.

        Examples:

            Registering a on_click event:

            .. code-block::

                actor = miniworlds.Actor((2,2))

                @actor.register
                def on_clicked_right(self, position):
                    print("clicked" + str(position))


        Args:
            position (tuple): Actual mouse position as tuple (x,y)

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_clicked_right)

    def on_detecting_world(self):
        """`on_detecting_world` is called, when actor is on the world

        Examples:

            Register on_detecting_world method:

            .. code-block::

                @player.register
                    def on_detecting_world(self):
                        print("Player 3: I'm on the world:")

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.

        """
        raise NotImplementedOrRegisteredError(self.on_detecting_world)

    def on_not_detecting_world(self):
        """`on_detecting_world` is called, when actor is on the world

        Examples:

            Register on_detecting_world method:

            .. code-block::

                @player.register
                    def on_detecting_world(self):
                        print("Player 3: I'm on the world:")

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.

        """
        raise NotImplementedOrRegisteredError(self.on_detecting_world)

    def on_detecting_actor(self, actor: "Actor"):
        """*on_detecting_actor* is called, when actor is detects a actor on same position

        Args:
            actor (Actor): The found actor

        Examples:

            Register detect_actor event

            .. code-block::

                @player.register
                def on_detecting_actor(self, actor):
                    print("Player 1: detecting actor:")
                    if actor == player2:
                    print("Am i detecting player2?" + str(actor == player2))

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_detecting_actor)

    def on_detecting_borders(self, borders: List[str]):
        """*on_detecting_border* is called, when actor is near a border

        Args:
            borders (List): A list of strings with found borders, e.g.: ['left', 'top']

        Examples:

            Register on_detecting_border_event:

            .. code-block::

                @player.register
                def on_detecting_borders(self, borders):
                    print("Player 4: detecting borders:")
                    print("Borders are here!", str(borders))

        Raises:
            NotImplementedOrRegisteredError: The error is raised when method is not overwritten or registered.
        """
        raise NotImplementedOrRegisteredError(self.on_detecting_borders)

    @property
    def static(self):
        """Should actor react to events?
        You can turn this option off for additional performance boost.
        """
        return self._static

    @static.setter
    def static(self, value):
        _world_connector = self.world.get_world_connector(self)
        _world_connector.set_static(value)

    @property
    def fill_color(self):
        """
        The fill color of actor as rgba value, e.g. (255, 0, 0) for red.

        When ``fill_color`` is set to a color, the attribute ``is_filled`` of costume
        (See: :py:attr:`.appearances.appearance.Appearance.is_filled`) is set to ``True``.

        .. note::

            Aliases: :py:attr:`Actor.color`

        .. warning::

            If you fill a costume with an image, the image will be completely overwritten,
            even if `fill_color` is transparent.

            This behaviour may change in later releases!

        Examples:

        .. code-block:: python

            from miniworlds import *

            world = World(200,80)
            world.default_fill_color = (0,0, 255)

            t = Actor()

            t2 = Actor((40,0))
            t2.is_filled = (0, 255, 0)

            t3 = Actor((80, 0))
            t3.fill_color = (255, 0, 0)

            t4 = Actor((120, 0))
            t4.add_costume((0,0,0))
            t4.fill_color = (255, 255, 0)

            t5 = Actor((160, 0))
            t5.add_costume("images/player.png")
            t5.fill_color = (255, 255, 0, 100) # image is overwritten

            t6 = Circle((0, 40), 20)
            t6.position = t6.center
            t6.fill_color = (255, 255, 255)

            t7 = Ellipse((40, 40), 40, 40)
            t7.fill_color = (255, 0, 255)

            world.run()

        Output:

        .. image:: ../_images/fill_color.png
            :width: 200px
            :alt: Set borders

        """
        return self._get_appearance_facade().fill_color

    @fill_color.setter
    def fill_color(self, value):
        self._get_appearance_facade().fill_color = value

    # Alias
    color = fill_color

    def fill(self, value):
        """Set fill color for borders and lines"""
        self._get_appearance_facade().fill(value)

    @property
    def is_filled(self):
        """Is actor filled with color?"""
        return self._get_appearance_facade().is_filled

    @is_filled.setter
    def is_filled(self, value):
        self._get_appearance_facade().is_filled = value

    @property
    def border_color(self):
        """border color of actor.

        The border-color is a rgba value, for example (255, 0, 0) for red, (0, 255, 0) for green and (255, 0, 0, 100).

        If the color-value has 4 values, the last value defines the transparency:
          * 0: Full transparent,
          * 255: No transparency


        .. note::

            You must also set :py:attr:`Actor.border` to a value > 0

            Aliases:  :py:attr:`Actor.stroke_color`

        Examples:

            See :py:attr:`Actor.border`


        """
        return self._get_appearance_facade().border_color

    @border_color.setter
    def border_color(self, value):
        self._get_appearance_facade().border_color = value

    # Alias

    stroke_color = border_color

    @property
    def border(self):
        """The border-size of actor.

        The value is 0, if actor has no border.

        .. note::

            You can also set border with ``costume.border`` or you can set the border with ``world.default_border``

        Examples:

            Set border of actor:

            .. code-block::

                from miniworlds import *

                world = World(210,80)
                world.default_border_color = (0,0, 255)
                world.default_border = 1

                t = Actor((10,10)) # default-border and color from world
                t.add_costume("images/player.png")

                t2 = Actor ((60, 10)) # overwrites default border values
                t2.add_costume("images/player.png")
                t2.border_color = (0,255, 0)
                t2.border = 5

                t3 = Actor ((110, 10)) # removes border
                t3.add_costume("images/player.png")
                t3.border = None

                world.run()

            Output:

            .. image:: ../_images/borders.png
                :width: 200px
                :alt: Set borders
        """
        return self._get_appearance_facade().border

    @border.setter
    def border(self, value):
        self._get_appearance_facade().border = value

    @property
    def visible(self):
        return self._get_appearance_facade().visible

    @visible.setter
    def visible(self, value):
        self._get_appearance_facade().visible = value

    def hide(self):
        """Hides a actor (the actor will be invisible)"""
        self._get_appearance_facade().hide()

    def show(self):
        """Displays a actor ( an invisible actor will be visible)"""
        self._get_appearance_facade().show()

    def register_sensor(self, *args, **kwargs):
        """This method is used for the @register_sensor decorator.
        """
        return self._get_event_facade().register_sensor(*args, **kwargs)

    def get_local_rect(self) -> pygame.Rect:
        local_rect = self.position_manager.get_local_rect()
        return local_rect

    @property
    def world(self):
        return self._world

    @world.setter
    def world(self, new_world):
        self.set_world(new_world)

    def set_world(self, new_world : "world_mod.World") -> "Actor":
        return self._get_event_facade().set_world(new_world)

    def new_costume(self):
        return self._get_appearance_facade().new_costume()

    @property
    def image(self) -> pygame.Surface:
        """
        The image of the actor:

        .. warning::

            Warning: You should not directly draw on the image (with pygame functions)
            as the image will be reloaded during animations

        """
        return self._get_appearance_facade().image
    @property
    def position(self) -> Tuple[float, float]:
        """The position of the actor as Position(x, y)"""
        return self._get_movement_facade().get_position()

    @position.setter
    def position(self, value: Tuple[float, float]):
        self.set_position(value)

    def set_position(self, value: Tuple[float, float]):
        self._get_movement_facade().set_position(value)

    def get_distance_to(self, obj: Union["Actor", Tuple[float, float]]) -> float:
        """Gets the distance to another actor or a position

        Args:
            obj: Actor or Position

        Returns:
            float: The distance between actor (measured from actor.center) to actor or position.
        """
        return self._get_sensor_facade().get_distance_to(obj)

    def on_shape_change(self):
        pass
