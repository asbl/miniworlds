from __future__ import annotations

import collections
import warnings
from difflib import get_close_matches
from functools import cached_property
from typing import TYPE_CHECKING, List, Optional, Tuple, Type, Union, cast

import pygame.rect

import miniworlds.actors.actor_appearance_facade as actor_appearance_facade
import miniworlds.actors.actor_base as actor_base
import miniworlds.actors.actor_event_facade as actor_event_facade
import miniworlds.actors.actor_initialization_facade as actor_initialization_facade
import miniworlds.actors.actor_movement_facade as actor_movement_facade
import miniworlds.actors.actor_sensor_facade as actor_sensor_facade
import miniworlds.actors.actor_size_facade as actor_size_facade
import miniworlds.appearances.appearance as appearance
import miniworlds.appearances.costume as costume_mod
import miniworlds.appearances.costumes_manager as costumes_manager
import miniworlds.base.api_validation as api_validation
import miniworlds.base.exceptions as exceptions
import miniworlds.worlds.manager.position_manager as actor_position_manager
import miniworlds.worlds.manager.sensor_manager as sensor_manager
from miniworlds.base.exceptions import (
    MissingPositionManager,
    Missingworldsensor,
    NotImplementedOrRegisteredError,
    NoValidWorldPositionError,
    NoWorldError,
    RegisterError,
)

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod


class Actor(actor_base.ActorBase):
    """Interactive object placed in a world.

    Actors can move, change costumes, detect collisions, send messages, and
    react to keyboard, mouse, and lifecycle events.

    Examples:
        ::

            Create a basic actor:

                from miniworlds import Actor, World

                world = World(100, 60)
                Actor((10, 10), world=world)
                world.run()

            Create an actor with a costume:

                from miniworlds import Actor, World

                world = World(100, 60)
                player = Actor((10, 10), world=world)
                player.add_costume("images/player.png")
                world.run()
    """

    actor_count: int = 0
    class_image: str = ""
    __slots__ = (
        # Facades (initialized in __init__)
        "_initialization_facade",
        # Other instance attributes
        "_collision_type",
        "_layer",
        "_world",
        "_static",
        # Note: __dict__ is inherited from DirtySprite (via ActorBase),
        # so dynamic attributes (including @cached_property) work normally
    )

    def __init__(
        self, position: Optional[Tuple[float, float]] = (0, 0), *args, **kwargs
    ):
        position, args = self._normalize_constructor_arguments(position, args)
        # Initialization facade is created directly during __init__
        # (not via cached_property) because it's needed immediately
        self._initialization_facade = (
            actor_initialization_facade.ActorInitializationFacade(self)
        )
        self._initialization_facade.prepare_core_references(kwargs.get("world"))
        self._validate_arguments(position, *args, **kwargs)
        self._initialization_facade.initialize_runtime_state(Actor.actor_count + 1)
        self._initialization_facade.initialize_world_managers(position)
        self._initialization_facade.finalize_sprite_state(kwargs.get("origin"))
        Actor.actor_count += 1

    @classmethod
    def _normalize_constructor_arguments(
        cls,
        position: Optional[Tuple[float, float]] = (0, 0),
        args: tuple = (),
    ) -> tuple[Optional[Tuple[float, float]], tuple]:
        if cls is not Actor and cls.__init__ is not Actor.__init__:
            return position, args
        if isinstance(position, tuple):
            return position, args
        if (
            len(args) >= 1
            and isinstance(position, (int, float))
            and isinstance(args[0], (int, float))
        ):
            return (position, args[0]), args[1:]
        return position, args

    # _initialization_facade is set directly in __init__, not via cached_property
    # because it's needed immediately for initialization

    @cached_property
    def _appearance_facade(self) -> actor_appearance_facade.ActorAppearanceFacade:
        return actor_appearance_facade.ActorAppearanceFacade(self)

    @cached_property
    def _event_facade(self) -> actor_event_facade.ActorEventFacade:
        return actor_event_facade.ActorEventFacade(self)

    @cached_property
    def _sensor_facade(self) -> actor_sensor_facade.ActorSensorFacade:
        return actor_sensor_facade.ActorSensorFacade(self)

    @cached_property
    def _movement_facade(self) -> actor_movement_facade.ActorMovementFacade:
        return actor_movement_facade.ActorMovementFacade(self)

    @cached_property
    def _size_facade(self) -> actor_size_facade.ActorSizeFacade:
        return actor_size_facade.ActorSizeFacade(self)

    def _validate_arguments(self, position, *args, **kwargs):
        if position is None:
            raise exceptions.NoValidPositionOnInitException(self, None)
        if not isinstance(position, tuple):
            raise exceptions.NoValidPositionOnInitException(self, position)

    @staticmethod
    def _type_name(value) -> str:
        return api_validation.type_name(value)

    @staticmethod
    def _with_try_hint(message: str, example: str | None = None) -> str:
        return api_validation.with_try_hint(message, example)

    def _is_learning_mode(self) -> bool:
        world = getattr(self, "_world", None)
        return bool(getattr(world, "learning_mode", False))

    @staticmethod
    def _student_warn(message: str) -> None:
        warnings.warn(message, RuntimeWarning, stacklevel=3)

    def _coerce_bool_learning(self, value, parameter_name: str):
        return api_validation.coerce_bool_learning(
            value,
            parameter_name,
            self._is_learning_mode(),
            self._student_warn,
        )

    def _coerce_position_learning(self, value, parameter_name: str):
        return api_validation.coerce_position_learning(
            value,
            parameter_name,
            self._is_learning_mode(),
            self._student_warn,
        )

    @staticmethod
    def _ensure_bool(value, parameter_name: str):
        api_validation.ensure_bool(
            value,
            parameter_name,
            Actor._with_try_hint,
            f"{parameter_name} = True",
        )

    @staticmethod
    def _ensure_real(value, parameter_name: str):
        api_validation.ensure_real(
            value,
            parameter_name,
            Actor._with_try_hint,
            f"{parameter_name} = 10",
        )

    @staticmethod
    def _ensure_int(value, parameter_name: str):
        api_validation.ensure_int(
            value,
            parameter_name,
            Actor._with_try_hint,
            f"{parameter_name} = 1",
        )

    @classmethod
    def _ensure_position_tuple(cls, value, parameter_name: str):
        api_validation.ensure_position_tuple(
            value,
            parameter_name,
            cls._ensure_real,
            cls._with_try_hint,
        )

    @classmethod
    def _ensure_rect_like(cls, value, parameter_name: str):
        api_validation.ensure_rect_like(
            value,
            parameter_name,
            pygame.rect.Rect,
            cls._ensure_real,
            cls._with_try_hint,
        )

    @classmethod
    def _ensure_color_like(cls, value, parameter_name: str):
        api_validation.ensure_color_like(
            value,
            parameter_name,
            cls._ensure_real,
            cls._with_try_hint,
        )

    @classmethod
    def _ensure_actor_instance(cls, value, parameter_name: str):
        if not isinstance(value, Actor):
            raise TypeError(
                f"{parameter_name} must be an Actor, got {cls._type_name(value)}: {value!r}"
            )

    @classmethod
    def _ensure_actor_filter(cls, value, parameter_name: str = "actors"):
        if value is None:
            return
        if isinstance(value, str):
            return
        if isinstance(value, Actor):
            return
        if isinstance(value, type) and issubclass(value, Actor):
            return
        raise TypeError(
            f"{parameter_name} must be None, Actor instance, Actor class, or class name string, got {cls._type_name(value)}: {value!r}"
        )

    @classmethod
    def _ensure_direction_value(
        cls, value, parameter_name: str = "direction", allow_none: bool = False
    ):
        api_validation.DirectionInput.ensure(
            value,
            parameter_name,
            allow_none,
            cls._ensure_position_tuple,
            cls._with_try_hint,
        )

    @classmethod
    def _normalize_direction_input(cls, value, parameter_name: str = "direction"):
        del parameter_name
        return api_validation.DirectionInput.normalize(value)

    @property
    def origin(self):
        """Current origin mode used for size and position operations."""
        return self._size_facade.get_origin()

    @origin.setter
    def origin(self, value: str):
        if not isinstance(value, str):
            raise TypeError(
                f"origin must be str ('center' or 'topleft'), got {type(value).__name__}: {value!r}"
            )
        self._size_facade.set_origin(value)

    def switch_origin(self, value: str):
        """Switch the actor origin while preserving its screen position.

        Args:
            value: `"center"` or `"topleft"`.

        Examples:
            ::

                actor.switch_origin("center")
        """
        if not isinstance(value, str):
            raise TypeError(
                f"value must be str ('center' or 'topleft'), got {type(value).__name__}: {value!r}"
            )
        self._size_facade.switch_origin(value)

    @classmethod
    def create_on_world(cls, world):
        """Create an actor on a specific world.

        Args:
            world: World to place the actor on.

        Returns:
            The created actor.

        Examples:
            ::

                actor = Actor.create_on_world(world)
        """
        return cls((0, 0), world)

    @property
    def collision_type(self) -> str:
        """str: Collision strategy used by this actor.

        Values:
            `default`: Use the world default.
            `tile`: Match actors on the same tile.
            `rect`: Check bounding rectangles.
            `static-rect`: Check cached bounding rectangles.
            `circle`: Check bounding circles.
            `mask`: Check overlapping image masks.

        Examples:
            ::

                actor.collision_type = "rect"

                if actor.detect(wall):
                    actor.undo_move()
        """
        if self._collision_type == "default":
            return "mask"
        else:
            return self._collision_type

    @collision_type.setter
    def collision_type(self, value: str):
        allowed_values = {"default", "tile", "rect", "static-rect", "circle", "mask"}
        if not isinstance(value, str):
            raise TypeError(
                f"collision_type must be str, got {type(value).__name__}: {value!r}"
            )
        value = value.strip().lower().replace("_", "-")
        if value not in allowed_values and self._is_learning_mode():
            close_match = get_close_matches(
                value, sorted(allowed_values), n=1, cutoff=0.75
            )
            if close_match:
                self._student_warn(
                    f"Learning mode: converted collision_type from {value!r} to {close_match[0]!r}"
                )
                value = close_match[0]
        if value not in allowed_values:
            raise ValueError(
                f"collision_type must be one of {sorted(allowed_values)}, got {value!r}"
            )
        self._collision_type = value

    @property
    def is_blockable(self):
        """bool: Whether this actor is stopped by blocking actors.

        Examples:
            ::

                player.is_blockable = True
                wall.is_blocking = True
        """
        return self.position_manager.is_blockable

    @is_blockable.setter
    def is_blockable(self, value: bool):
        value = self._coerce_bool_learning(value, "is_blockable")
        self._ensure_bool(value, "is_blockable")
        self.position_manager.is_blockable = value

    @property
    def is_blocking(self):
        """bool: Whether this actor blocks blockable actors.

        Examples:
            ::

                wall.is_blocking = True
        """
        return self.position_manager.is_blocking

    @is_blocking.setter
    def is_blocking(self, value: bool):
        value = self._coerce_bool_learning(value, "is_blocking")
        self._ensure_bool(value, "is_blocking")
        previous_value = self.position_manager.is_blocking
        self.position_manager.is_blocking = value
        world = self.world
        if previous_value == value or world is None:
            return
        if hasattr(world, "get_world_connector"):
            connector = world.get_world_connector(self)
            if connector is not None and hasattr(
                connector, "sync_blocking_registration"
            ):
                connector.sync_blocking_registration(previous_value, value)
                return
        if hasattr(world, "_blocking_actors"):
            if value:
                world._blocking_actors.add(self)
            else:
                world._blocking_actors.discard(self)

    @property
    def layer(self) -> int:
        """int: Drawing layer used when actors overlap.

        Higher layers are drawn above lower layers.

        Examples:
            ::

                player.layer = 10
        """
        return self._layer

    @layer.setter
    def layer(self, value: int):
        self._ensure_int(value, "layer")
        self._layer = value
        if self in self.world.actors:
            self.world.actors.change_layer(
                self, value
            )  # changes layer in DirtySpriteGroup.

    @property
    def last_position(self) -> Tuple[float, float]:
        """tuple[float, float]: Actor center from the previous frame.

        Examples:
            ::

                if actor.center != actor.last_position:
                    print("actor moved")
        """
        return self._size_facade.get_last_center()

    @property
    def last_direction(self) -> int:
        """Direction value from the previous frame."""
        return self._size_facade.get_last_direction()

    @classmethod
    def from_topleft(cls, topleft_position: Tuple[float, float], *args, **kwargs):
        """Create an actor positioned by its top-left corner.

        Args:
            topleft_position: Top-left position as `(x, y)`.

        Returns:
            The created actor.

        Examples:
            ::

                actor = Actor.from_topleft((20, 40))
        """
        cls._ensure_position_tuple(topleft_position, "topleft_position")
        obj = cls(topleft_position, **kwargs)  # temp position
        obj.origin = "topleft"
        return obj

    @classmethod
    def from_center(cls, center_position: Tuple[float, float], *args, **kwargs):
        """Create an actor positioned by its center.

        Args:
            center_position: Center position as `(x, y)`.

        Returns:
            The created actor.

        Examples:
            ::

                actor = Actor.from_center((100, 80))
        """
        cls._ensure_position_tuple(center_position, "center_position")
        obj = cls(center_position, **kwargs)  # temp position
        obj.origin = "center"
        return obj

    @property
    def costume_count(self) -> int:
        """int: Number of costumes attached to the actor.

        Examples:
            ::

                actor.add_costume((255, 0, 0))
                print(actor.costume_count)
        """
        return self._appearance_facade.costume_count

    @property
    def is_flipped(self) -> bool:
        """bool: Whether the current costume is mirrored horizontally.

        Examples:
            ::

                actor.is_flipped = True
        """
        return self._appearance_facade.is_flipped

    @is_flipped.setter
    def is_flipped(self, value: bool):
        value = self._coerce_bool_learning(value, "is_flipped")
        self._ensure_bool(value, "is_flipped")
        self._appearance_facade.is_flipped = value

    def flip_x(self) -> int:
        """Flip the costume horizontally and turn the actor around.

        Returns:
            The new actor direction.

        Examples:
            ::

                if actor.detect_borders():
                    actor.flip_x()
        """
        return self._appearance_facade.flip_x()

    def add_costume(
        self, source: Union[None, Tuple, str, List, "appearance.Appearance"] = None
    ) -> "costume_mod.Costume":
        """Add a costume to the actor.

        Args:
            source: Image path, color tuple, list of image sources, existing
                `Costume`, or `None` for an empty costume.

        Returns:
            The new costume.

        Examples:
            ::

                player = Actor((20, 20))
                player.add_costume("images/player.png")
                player.add_costume((255, 255, 0))

                idle = player.add_costume("images/idle.png")
                run = player.add_costume("images/run.png")
                player.switch_costume(run)
        """
        return self._appearance_facade.add_costume(source)

    def add_costumes(self, sources: list) -> "costume_mod.Costume":
        """Add several costumes.

        Args:
            sources: List of image paths, color tuples, or costume sources.

        Returns:
            The last added costume.

        Examples:
            ::

                actor.add_costumes(["images/idle.png", "images/run.png"])
        """
        if not isinstance(sources, list):
            raise TypeError(
                f"sources must be list, got {type(sources).__name__}: {sources!r}"
            )
        return self._appearance_facade.add_costumes(sources)

    def remove_costume(self, source: Union[int, "costume_mod.Costume"] = None):
        """Remove a costume.

        Args:
            source: Costume index or costume object. If omitted, the current
                costume is removed.

        Examples:
            ::

                actor.remove_costume()
                actor.remove_costume(0)
        """
        return self._appearance_facade.remove_costume(source)

    def switch_costume(
        self, source: Union[int, "appearance.Appearance"]
    ) -> "costume_mod.Costume":
        """Switch to another costume.

        Args:
            source: Costume index or costume object.

        Returns:
            The new active costume.

        Examples:
            ::

                actor.add_costume("images/idle.png")
                actor.add_costume("images/run.png")
                actor.switch_costume(1)
        """
        return self._appearance_facade.switch_costume(source)

    def set_costume(self, costume: Union[str, tuple, int, "appearance.Appearance"]):
        """Set the current costume from an index, source, or appearance object."""
        self._appearance_facade.set_costume(costume)

    def reset_costumes(self):
        """Remove all costumes and reset appearance state."""
        self._appearance_facade.reset_costumes()

    def set_background_color(self, color: tuple):
        """Set a background color behind the actor costume image."""
        self._ensure_color_like(color, "color")
        self._appearance_facade.set_background_color(color)

    def next_costume(self):
        """Switch to the next costume.

        Returns:
            The new active costume.

        Examples:
            ::

                actor.next_costume()
        """
        self._appearance_facade.next_costume()

    @property
    def costume(self) -> costume_mod.Costume:
        """Costume: Current active costume.

        Examples:
            ::

                actor.costume.is_rotatable = False
        """
        return self._appearance_facade.costume

    def has_costume(self) -> bool:
        """Return `True` when the actor currently has a costume."""
        return self._appearance_facade.has_costume()

    @costume.setter
    def costume(self, value):
        self._appearance_facade.costume = value

    @property
    def costumes(self) -> "costumes_manager.CostumesManager":
        """CostumesManager: Manager containing all actor costumes.

        Examples:
            ::

                for costume in actor.costumes:
                    costume.border = 1
        """
        return self._appearance_facade.costumes

    @property
    def orientation(self) -> float:
        """float: Costume orientation offset in degrees.

        Examples:
            ::

                actor.orientation = -90
        """
        return self._appearance_facade.orientation

    @orientation.setter
    def orientation(self, value: float):
        self._ensure_real(value, "orientation")
        self._appearance_facade.orientation = value

    @property
    def direction(self) -> int:
        """int: Actor direction in Miniworlds/Scratch convention.

        Common values are `0` or `"up"`, `90` or `"right"`, `-90` or
        `"left"`, and `180` or `"down"`.

        Examples:
            ::

                @player.register
                def on_key_down(self, key):
                    if "left" in key:
                        self.direction = "left"
                    elif "right" in key:
                        self.direction = "right"
                    self.move()

                actor.direction = 45
                actor.move()
        """
        return self._movement_facade.get_direction()

    @direction.setter
    def direction(self, value: int):
        value = self._normalize_direction_input(value, "direction")
        self._ensure_direction_value(value, "direction")
        self._movement_facade.set_direction(value)

    @property
    def direction_at_unit_circle(self) -> int:
        """int: Direction in unit-circle convention.

        In this convention, `0` points right and `90` points up.

        Examples:
            ::

                actor.direction_at_unit_circle = 0
        """
        return self._movement_facade.get_direction_at_unit_circle()

    @direction_at_unit_circle.setter
    def direction_at_unit_circle(self, value: int):
        self._ensure_real(value, "direction_at_unit_circle")
        self._movement_facade.set_direction_at_unit_circle(value)

    def turn_left(self, degrees: int = 90) -> int:
        """Turn the actor left.

        Args:
            degrees: Degrees to turn.

        Returns:
            The new direction.

        Examples:
            ::

                actor.turn_left()
                actor.turn_left(45)
        """
        self._ensure_real(degrees, "degrees")
        return self._movement_facade.turn_left(degrees)

    def turn_right(self, degrees: Union[int, float] = 90):
        """Turn the actor right.

        Args:
            degrees: Degrees to turn.

        Returns:
            The new direction.

        Examples:
            ::

                actor.turn_right()
                actor.turn_right(45)
        """
        self._ensure_real(degrees, "degrees")
        return self._movement_facade.turn_right(degrees)

    def set_direction(self, direction: Union[str, int, float]) -> float:
        """Point the actor in a direction.

        Args:
            direction: Direction as an angle or string such as `"up"`,
                `"right"`, `"down"`, or `"left"`.

        Returns:
            The new direction.

        Examples:
            ::

                actor.set_direction("left")
                actor.set_direction(45)
        """
        direction = self._normalize_direction_input(direction, "direction")
        self._ensure_direction_value(direction, "direction")
        return self._movement_facade.set_direction_value(direction)

    def point_towards_position(
        self, destination: Tuple[float, float]
    ) -> Union[int, float]:
        """Point the actor toward a position.

        Args:
            destination: Target position as `(x, y)`.

        Returns:
            The new direction.

        Examples:
            ::

                def act(self):
                    mouse = self.world.mouse.get_position()
                    if mouse:
                        self.point_towards_position(mouse)
                    self.move()
        """
        self._ensure_position_tuple(destination, "destination")
        return self._movement_facade.point_towards_position(destination)

    def point_towards_actor(self, other: "Actor") -> int:
        """Point the actor toward another actor.

        Args:
            other: Target actor.

        Returns:
            The new direction.

        Examples:
            ::

                enemy.point_towards_actor(player)
        """
        self._ensure_actor_instance(other, "other")
        return self._movement_facade.point_towards_actor(other)

    @property
    def size(self) -> tuple:
        """tuple[float, float]: Actor size as `(width, height)`.

        Examples:
            ::

                actor.size = (40, 30)
        """
        return self._size_facade.get_size()

    @size.setter
    def size(self, value: tuple):
        self.set_size(value)

    def set_size(self, value: tuple):
        """Set actor size.

        Args:
            value: Size as `(width, height)` or a scalar size.

        Examples:
            ::

                actor.set_size((40, 30))
        """
        value = self._coerce_position_learning(value, "value")
        if isinstance(value, tuple):
            self._ensure_position_tuple(value, "value")
        else:
            self._ensure_real(value, "value")
        self._size_facade.set_size(value)

    @property
    def width(self):
        """float: Actor width in pixels.

        Examples:
            ::

                actor.width = 80
        """
        return self._size_facade.get_width()

    @width.setter
    def width(self, value):
        self._ensure_real(value, "width")
        self._size_facade.set_width(value)

    def scale_width(self, value):
        """Scale actor width by a factor.

        Args:
            value: Scale factor.

        Examples:
            ::

                actor.scale_width(1.5)
        """
        self._ensure_real(value, "value")
        self._size_facade.scale_width(value)

    @property
    def height(self):
        """float: Actor height in pixels.

        Examples:
            ::

                actor.height = 60
        """
        return self._size_facade.get_height()

    @height.setter
    def height(self, value):
        self._ensure_real(value, "height")
        self._size_facade.set_height(value)

    def scale_height(self, value):
        """Scale actor height by a factor.

        Args:
            value: Scale factor.

        Examples:
            ::

                actor.scale_height(0.5)
        """
        self._ensure_real(value, "value")
        self._size_facade.scale_height(value)

    @property
    def x(self) -> float:
        """float: Actor x-position."""
        return self._movement_facade.get_x()

    @x.setter
    def x(self, value: float):
        self._ensure_real(value, "x")
        self._movement_facade.set_x(value)

    @property
    def y(self) -> float:
        """float: Actor y-position."""
        return self._movement_facade.get_y()

    @y.setter
    def y(self, value: float):
        self._ensure_real(value, "y")
        self._movement_facade.set_y(value)

    @property
    def class_name(self) -> str:
        """Class name of this actor instance."""
        return self.__class__.__name__

    @property
    def topleft_x(self) -> float:
        """float: X-coordinate of the actor's top-left corner."""
        return self._movement_facade.get_topleft_x()

    @property
    def topleft_y(self) -> float:
        """float: Y-coordinate of the actor's top-left corner."""
        return self._movement_facade.get_topleft_y()

    @topleft_x.setter
    def topleft_x(self, value: float):
        self._ensure_real(value, "topleft_x")
        self._movement_facade.set_topleft_x(value)

    @topleft_y.setter
    def topleft_y(self, value: float):
        self._ensure_real(value, "topleft_y")
        self._movement_facade.set_topleft_y(value)

    @property
    def topleft(self) -> Tuple[float, float]:
        """tuple[float, float]: Top-left position in world coordinates.

        Examples:
            ::

                actor.topleft = (10, 20)
        """
        return self._movement_facade.get_topleft()

    @topleft.setter
    def topleft(self, value: Tuple[float, float]):
        value = self._coerce_position_learning(value, "topleft")
        self._ensure_position_tuple(value, "topleft")
        self._movement_facade.set_topleft(value)

    @property
    def local_center(self) -> Tuple[float, float]:
        """tuple[float, float]: Actor center in camera-local coordinates."""
        return self._movement_facade.get_local_center()

    @property
    def center_x(self) -> float:
        """float: X-coordinate of the actor center."""
        return self._movement_facade.get_center_x()

    @center_x.setter
    def center_x(self, value: float):
        self._ensure_real(value, "center_x")
        self._movement_facade.set_center_x(value)

    @property
    def center_y(self) -> float:
        """float: Y-coordinate of the actor center."""
        return self._movement_facade.get_center_y()

    @center_y.setter
    def center_y(self, value: float):
        self._ensure_real(value, "center_y")
        self._movement_facade.set_center_y(value)

    @property
    def center(self) -> Tuple[float, float]:
        """tuple[float, float]: Center position in world coordinates.

        Examples:
            ::

                actor.center = (100, 80)
        """
        return self._movement_facade.get_center()

    @center.setter
    def center(self, value: Tuple[float, float]):
        value = self._coerce_position_learning(value, "center")
        self._ensure_position_tuple(value, "center")
        self._movement_facade.set_center(value)

    def move(self, distance: int = 0, direction=None):
        """Move the actor.

        Args:
            distance: Number of steps to move.
            direction: Optional direction. If omitted, the current actor
                direction is used.

        Returns:
            The moved actor.

        Examples:
            ::

                actor.direction = "right"
                actor.move(5)
        """
        direction = self._normalize_direction_input(direction, "direction")
        self._ensure_real(distance, "distance")
        self._ensure_direction_value(direction, "direction", allow_none=True)
        return self._movement_facade.move(distance, direction)

    def move_vector(self, vector):
        """Move the actor by a vector.

        Args:
            vector: Vector-like movement delta.

        Returns:
            The moved actor.

        Examples:
            ::

                actor.move_vector(Vector(2, 0))
        """
        return self._movement_facade.move_vector(vector)

    def move_back(self, distance):
        """Move the actor backward.

        Args:
            distance: Number of steps to move backward.

        Returns:
            The actor itself.

        Examples:
            ::

                actor.move()
                if actor.detect(Wall):
                    actor.move_back(5)
        """
        self._ensure_real(distance, "distance")
        return self._movement_facade.move_back(distance)

    def undo_move(self):
        """Undo the last move.

        Returns:
            The moved actor.

        Examples:
            ::

                def on_detecting_wall(self, wall):
                    self.undo_move()
        """
        return self._movement_facade.undo_move()

    def move_towards(
        self,
        target: Union[Tuple[float, float], "Actor"],
        distance: float = 1,
    ):
        """Move toward a target actor or position.

        Args:
            target: Target actor or position.
            distance: Step size.

        Returns:
            The moved actor.

        Examples:
            ::

                enemy.move_towards(player, 2)
                enemy.move_towards((100, 80), 2)
        """
        if isinstance(target, tuple):
            self._ensure_position_tuple(target, "target")
        else:
            self._ensure_actor_instance(target, "target")
        self._ensure_real(distance, "distance")
        return self._movement_facade.move_towards(target, distance)

    def move_away(
        self,
        target: Union[Tuple[float, float], "Actor"],
        distance: float = 1,
    ):
        """Move away from a target actor or position.

        Args:
            target: Target actor or position.
            distance: Step size.

        Returns:
            The moved actor.

        Examples:
            ::

                @player.register
                def act(self):
                    if self.detect(enemy):
                        self.move_away(enemy, 3)
        """
        if isinstance(target, tuple):
            self._ensure_position_tuple(target, "target")
        else:
            self._ensure_actor_instance(target, "target")
        self._ensure_real(distance, "distance")
        return self._movement_facade.move_away(target, distance)

    def move_in_direction(
        self,
        direction: Union[int, str, Tuple[float, float]],
        distance=1,
    ):
        """Move in a direction.

        `direction` may be a number, a direction string, or a target position.

        Args:
            direction: Direction angle, direction name, or target position.
            distance: Number of steps to move.

        Returns:
            The moved actor.

        Examples:
            ::

                @player.register
                def on_key_pressed(self, key):
                    if "right" in key:
                        self.move_in_direction("right", 5)
                    if "up" in key:
                        self.move_in_direction("up", 5)

                player.move_in_direction((100, 80), 2)
        """
        direction = self._normalize_direction_input(direction, "direction")
        try:
            self._ensure_direction_value(direction, "direction")
        except TypeError as exc:
            raise exceptions.MoveInDirectionTypeError(direction) from exc
        self._ensure_real(distance, "distance")
        return self._movement_facade.move_in_direction(direction, distance)

    def move_to(self, position: Tuple[float, float]):
        """Move the actor to a world position.

        Args:
            position: Target position as `(x, y)`.

        Returns:
            The moved actor.

        Examples:
            ::

                @player.register
                def on_clicked_left(self, position):
                    self.move_to(position)
        """
        position = self._coerce_position_learning(position, "position")
        self._ensure_position_tuple(position, "position")
        return self._movement_facade.move_to(position)

    def go_to(self, position: Tuple[float, float]):
        """Student-friendly alias for `move_to(position)`."""
        return self.move_to(position)

    def move_forward(self, distance: int = 0):
        """Student-friendly alias for `move(distance)`."""
        return self.move(distance)

    def face(self, direction: Union[str, int, float]):
        """Student-friendly alias for `set_direction(direction)`."""
        return self.set_direction(direction)

    def turn(self, degrees: Union[int, float] = 90):
        """Student-friendly alias for `turn_right(degrees)`."""
        return self.turn_right(degrees)

    def touching(self, *args, **kwargs):
        """Student-friendly alias for `detect(...)`."""
        return self.detect(*args, **kwargs)

    def touching_all(self, *args, **kwargs):
        """Student-friendly alias for `detect_all(...)`."""
        return self.detect_all(*args, **kwargs)

    def remove(self, kill=True) -> collections.defaultdict:
        """Remove this actor from its world.

        Args:
            kill: Whether to remove the underlying pygame sprite too.

        Returns:
            Removed actor data from the world connector.

        Examples:
            ::

                coin = actor.detect(Coin)
                if coin:
                    coin.remove()
        """
        kill = self._coerce_bool_learning(kill, "kill")
        self._ensure_bool(kill, "kill")
        return self.world.get_world_connector(self).remove_actor_from_world(kill=kill)

    def before_remove(self):
        """Hook called immediately before the actor is removed from the world."""
        pass

    @property
    def is_rotatable(self) -> bool:
        """bool: Whether the costume rotates with the actor direction.

        The actor direction still changes when this is `False`; only the
        rendered costume stays unrotated.

        Examples:
            ::

                actor.is_rotatable = False
                actor.direction = "right"
        """
        return self.costume.is_rotatable

    @is_rotatable.setter
    def is_rotatable(self, value: bool):
        value = self._coerce_bool_learning(value, "is_rotatable")
        self._ensure_bool(value, "is_rotatable")
        self.costume.is_rotatable = value

    def bounce_from_border(self, borders: List[str]) -> Actor:
        """Bounce the actor away from world borders.

        Args:
            borders: Border names such as `"left"` or `"top"`.

        Returns:
            The actor itself.

        Examples:
            ::

                @ball.register
                def act(self):
                    self.move()
                    borders = self.detect_borders()
                    if borders:
                        self.bounce_from_border(borders)

        """
        if not isinstance(borders, list):
            raise TypeError(
                f"borders must be list[str], got {type(borders).__name__}: {borders!r}"
            )
        invalid_border = next(
            (border for border in borders if not isinstance(border, str)), None
        )
        if invalid_border is not None:
            raise TypeError(
                f"borders must contain only str values, got {type(invalid_border).__name__}: {invalid_border!r}"
            )
        return self.position_manager.bounce_from_border(borders)

    def detect_all(
        self,
        actors: Union[str, "Actor", Type["Actor"]] = None,
        direction: int = 0,
        distance: int = 0,
    ) -> List["Actor"]:
        """Return all actors detected at an offset from this actor.

        Args:
            actors: Optional actor filter; use `None` for all actors.
            direction: Direction to check.
            distance: Distance from the actor center.

        Returns:
            All matching actors found by the sensor.

        Examples:
            ::

                coins = player.detect_all(Coin)
                for coin in coins:
                    coin.remove()

                walls_ahead = player.detect_all(Wall, direction="right", distance=10)
        """
        self._ensure_actor_filter(actors, "actors")
        self._ensure_real(direction, "direction")
        self._ensure_real(distance, "distance")
        return self._sensor_facade.detect_all(actors, direction, distance)

    def detect(self, *args, **kwargs) -> Union["Actor", None]:
        """Return the first detected actor.

        Args:
            args: Positional arguments forwarded to `detect_all()`.
            kwargs: Keyword arguments forwarded to `detect_all()`.

        Returns:
            First matching actor, or `None`.

        Examples:
            ::

                wall = player.detect(Wall)
                if wall:
                    player.undo_move()

                coin = player.detect(Coin)
                if coin:
                    player.score += 1
                    coin.remove()
        """
        return self._sensor_facade.detect(*args, **kwargs)

    def detect_borders(
        self,
        distance: int = 0,
    ) -> List:
        """Return borders detected near the actor.

        Args:
            distance: Distance in front of the actor to check.

        Returns:
            List of border names such as `"left"`, `"right"`, `"top"`, or
            `"bottom"`.

        Examples:
            ::

                @ball.register
                def act(self):
                    self.move()
                    borders = self.detect_borders()
                    if borders:
                        self.bounce_from_border(borders)
        """
        self._ensure_real(distance, "distance")
        return self._sensor_facade.detect_borders(distance)

    def detect_left_border(self) -> bool:
        """Return whether the actor touches the left border.

        Returns:
            `True` if the left border is detected.

        """
        return self._sensor_facade.detect_left_border()

    def detecting_left_border(self) -> bool:
        """Return whether the actor touches the left border.

        Returns:
            `True` if the left border is detected.

        """
        return self.detect_left_border()

    def detect_right_border(self) -> bool:
        """Return whether the actor touches the right border.

        Returns:
            `True` if the right border is detected.

        """
        return self._sensor_facade.detect_right_border()

    def detecting_right_border(self) -> bool:
        """Return whether the actor touches the right border.

        Returns:
            `True` if the right border is detected.

        """
        return self.detect_right_border()

    def detect_top_border(self) -> bool:
        """Return whether the actor touches the top border.

        Returns:
            `True` if the top border is detected.

        """
        return self._sensor_facade.detect_top_border()

    def detecting_top_border(self) -> bool:
        """Return whether the actor touches the top border.

        Returns:
            `True` if the top border is detected.

        """
        return self.detect_top_border()

    def detecting_bottom_border(self) -> bool:
        """Return whether the actor touches the bottom border.

        Returns:
            `True` if the bottom border is detected.

        """
        return self._sensor_facade.detecting_bottom_border()

    def detect_bottom_border(self) -> bool:
        """Return whether the actor touches the bottom border.

        Returns:
            `True` if the bottom border is detected.

        """
        return self.detecting_bottom_border()

    def detect_color(self, color: Tuple = None) -> bool:
        """Return whether the actor detects a background color.

        Args:
            color: Optional RGB/RGBA color tuple. If omitted, any color is
                detected.

        Returns:
            `True` if the color is detected at the actor center.

        Examples:
            ::

                @player.register
                def act(self):
                    if self.detect_color((0, 0, 0)):
                        self.remove()
        """
        if color is not None:
            self._ensure_color_like(color, "color")
        return self._sensor_facade.detect_color(color)

    def detect_color_at(
        self, direction: int = None, distance: int = 0
    ) -> Union[Tuple, List]:
        """Return background colors at an offset from the actor.

        Args:
            direction: Direction to check; omit it to use the actor position.
            distance: Distance from the actor center.

        Returns:
            Color or colors found by the sensor.

        Examples:
            ::

                color = actor.detect_color_at("right", 5)
        """
        direction = self._normalize_direction_input(direction, "direction")
        self._ensure_direction_value(direction, "direction", allow_none=True)
        self._ensure_real(distance, "distance")
        return self._sensor_facade.detect_color_at(direction, distance)

    def detect_actors_at(self, direction=None, distance=0, actors=None) -> list:
        """Return all actors at an offset from this actor.

        Args:
            direction: Direction to check; omit it to use the actor position.
            distance: Distance from the actor center.
            actors: Optional actor filter.

        Returns:
            List of matching actors.

        Examples:
            ::

                @player.register
                def on_key_pressed_right(self):
                    if not self.detect_actors_at("right", 20, Wall):
                        self.move_in_direction("right", 5)
        """
        direction = self._normalize_direction_input(direction, "direction")
        self._ensure_direction_value(direction, "direction", allow_none=True)
        self._ensure_real(distance, "distance")
        self._ensure_actor_filter(actors, "actors")
        return self._sensor_facade.detect_actors_at(direction, distance, actors)

    def detect_actor_at(self, direction=None, distance=0, actors=None) -> "Actor":
        """Return the first actor at an offset from this actor.

        Args:
            direction: Direction to check.
            distance: Distance from the actor center.
            actors: Optional actor filter.

        Returns:
            First matching actor, or `None`.

        Examples:
            ::

                wall = player.detect_actor_at("right", 20, Wall)
                if wall:
                    player.undo_move()
        """
        direction = self._normalize_direction_input(direction, "direction")
        self._ensure_direction_value(direction, "direction", allow_none=True)
        self._ensure_real(distance, "distance")
        self._ensure_actor_filter(actors, "actors")
        return self._sensor_facade.detect_actor_at(direction, distance, actors)

    def detect_actors_in_front(
        self,
        actors=None,
        distance=1,
    ) -> list:
        """Return all actors directly in front of this actor.

        Args:
            actors: Optional actor filter.
            distance: Distance in front of the actor.

        Returns:
            Matching actors.

        Examples:
            ::

                enemies = player.detect_actors_in_front(Enemy)
                for enemy in enemies:
                    player.move_away(enemy, 3)
        """
        self._ensure_actor_filter(actors, "actors")
        self._ensure_real(distance, "distance")
        return self._sensor_facade.detect_actors_in_front(actors, distance)

    def detect_actor_in_front(
        self,
        actors=None,
        distance=1,
    ) -> "Actor":
        """Return the first actor directly in front.

        Args:
            actors: Optional actor filter.
            distance: Distance in front of the actor.

        Returns:
            First matching actor, or `None`.

        Examples:
            ::

                wall = player.detect_actor_in_front(Wall)
                if wall:
                    player.turn_left()
        """
        self._ensure_actor_filter(actors, "actors")
        self._ensure_real(distance, "distance")
        return self._sensor_facade.detect_actor_in_front(actors, distance)

    def detect_point(self, position: Tuple[float, float]) -> bool:
        """Return whether the actor overlaps a world point.

        Args:
            position: World position as `(x, y)`.

        Returns:
            `True` if the actor overlaps the point.

        Examples:
            ::

                if actor.detect_point((100, 80)):
                    actor.hide()
        """
        self._ensure_position_tuple(position, "position")
        return self._sensor_facade.detect_point(position)

    def detect_pixel(self, position: Tuple[float, float]) -> bool:
        """Return whether the actor overlaps a screen pixel.

        Args:
            position: Pixel position as `(x, y)`.

        Returns:
            `True` if the actor overlaps the pixel.

        Examples:
            ::

                @actor.register
                def on_mouse_left(self, position):
                    if self.detect_pixel(position):
                        self.hide()
        """
        self._ensure_position_tuple(position, "position")
        return self._sensor_facade.detect_pixel(position)

    def detect_rect(self, rect: Union[Tuple, pygame.rect.Rect]):
        """Return whether the actor overlaps a rectangle.

        Args:
            rect: Rectangle as `(x, y, width, height)` or `pygame.Rect`.

        Returns:
            `True` if the actor overlaps the rectangle.
        """
        self._ensure_rect_like(rect, "rect")
        return self._sensor_facade.detect_rect(rect)

    def is_inside_world(self):
        """Return whether the actor is completely inside the world.

        Returns:
            `True` if the entire actor rectangle is inside the world.
        """
        return self._sensor_facade.is_inside_world()

    def bounce_from_actor(self, other: "Actor"):
        """Reflect movement direction after colliding with another actor.

        Args:
            other: Actor to bounce from.

        Examples:
            ::

                other = ball.detect()
                if other:
                    ball.bounce_from_actor(other)
        """
        self._ensure_actor_instance(other, "other")
        self._sensor_facade.bounce_from_actor(other)

    def animate(self, speed: int = 10):
        """Animate the current costume.

        Args:
            speed: Frames between animation steps.

        Examples:
            ::

                actor.animate(speed=5)
        """
        self._ensure_int(speed, "speed")
        self.costume_manager.animate(speed)

    def animate_costume(self, costume: "costume_mod.Costume", speed: int = 10):
        """Animate a specific costume.

        Args:
            costume: Costume to animate.
            speed: Frames between animation steps.

        Examples:
            ::

                actor.animate_costume(run_costume, speed=5)
        """
        if costume is None:
            raise TypeError("costume must not be None")
        self._ensure_int(speed, "speed")
        self.costume_manager.animate_costume(costume, speed)

    def animate_loop(self, speed: int = 10):
        """Animate the current costume in a loop.

        Args:
            speed: Frames between animation steps.

        Examples:
            ::

                player.costume.add_images(["images/walk1.png", "images/walk2.png"])
                player.animate_loop(speed=8)
        """
        self._ensure_int(speed, "speed")
        self.costume.loop = True
        self.costume_manager.animate(speed)

    def stop_animation(self):
        """Stop the current costume animation.

        Examples:
            ::

                actor.animate_loop()
                actor.stop_animation()
        """
        self.costume.is_animated = False

    def send_message(self, message: str):
        """Send a message through the world event system.

        Args:
            message: Message name.

        Examples:
            ::

                player.send_message("hit")

                @enemy.register
                def on_message(self, message):
                    if message == "hit":
                        self.remove()
        """
        if not isinstance(message, str):
            raise TypeError(
                f"message must be str, got {type(message).__name__}: {message!r}"
            )
        self._event_facade.send_message(message)

    def on_key_down(self, key: list):
        """Called once when a key is pressed.

        Register `on_key_down_<letter>` (for example `on_key_down_a`) if you
        want to react to a specific letter only.

        For arrow keys use `on_key_down_left`, `on_key_down_right`,
        `on_key_down_up`, or `on_key_down_down`.

        Args:
            key: List of key name variants, for example `["A", "a"]` or
                `["left"]`.

        Examples:
            ::

                @player.register
                def on_key_down(self, key):
                    if "left" in key:
                        self.direction = "left"
                    elif "right" in key:
                        self.direction = "right"
                    self.move()

                @player.register
                def on_key_down_space(self):
                    self.send_message("jump")
        """
        raise NotImplementedOrRegisteredError(self.on_key_down)

    def on_key_pressed(self, key: list):
        """Called repeatedly every frame while a key is held down.

        This is the right choice for smooth, continuous movement. Like
        `on_key_down`, this event supports per-letter handlers such as
        `on_key_pressed_w` or `on_key_pressed_left`.

        Args:
            key: List of key name variants currently held, for example
                `["W", "w"]` or `["up"]`.

        Examples:
            ::

                @player.register
                def on_key_pressed(self, key):
                    if "left" in key:
                        self.x -= 3
                    elif "right" in key:
                        self.x += 3
        """
        raise NotImplementedOrRegisteredError(self.on_key_pressed)

    def on_key_up(self, key):
        """Called once when a previously pressed key is released.

        Args:
            key: List of key name variants, same format as in `on_key_down()`.

        Examples:
            ::

                @player.register
                def on_key_up(self, key):
                    if "space" in key:
                        self.stop_animation()
        """
        raise NotImplementedOrRegisteredError(self.on_key_up)

    def on_mouse_over(self, position):
        """Called when the mouse cursor enters or moves over the actor area.

        Args:
            position: Current mouse position as `(x, y)`.

        Examples:
            ::

                @actor.register
                def on_mouse_over(self, position):
                    self.costume.transparency = 100
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_over)

    def on_mouse_leave(self, position):
        """Called when the mouse cursor leaves the actor area.

        Args:
            position: The mouse position when it left the actor.

        Examples:
            ::

                @actor.register
                def on_mouse_leave(self, position):
                    self.costume.transparency = 0
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_leave)

    def on_mouse_left_down(self, position: tuple):
        """Called when the left mouse button is pressed down.

        Args:
            position: Current mouse position as `(x, y)`.
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_left_down)

    def on_mouse_right_down(self, position: tuple):
        """Called when the right mouse button is pressed down.

        Args:
            position: Current mouse position as `(x, y)`.
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_right_down)

    def on_mouse_left(self, position: tuple):
        """Called when the left mouse button is clicked.

        The event is triggered for the click itself, independent of whether
        the click happened on the actor. Use `detect_pixel(position)` if you
        only want clicks on the actor body.

        Args:
            position: Current mouse position as `(x, y)`.
        """

        raise NotImplementedOrRegisteredError(self.on_mouse_left)

    def on_mouse_right(self, position: tuple):
        """Called when the right mouse button is clicked.

        Use `detect_pixel(position)` if you only want clicks on the actor
        body.

        Args:
            position: Current mouse position as `(x, y)`.
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_right)

    def on_mouse_motion(self, position: tuple):
        """Called when the mouse moves.

        The event is triggered for movement events in general. Use
        `detect_pixel(position)` if you only want motion over the actor body.

        Args:
            position: Current mouse position as `(x, y)`.
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_motion)

    def on_mouse_left_released(self, position: tuple):
        """Called when the left mouse button is released.

        Args:
            position: Current mouse position as `(x, y)`.

        Examples:
            ::

                @actor.register
                def on_mouse_left_released(self, position):
                    self.center = position
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_left_released)

    def on_mouse_right_released(self, position: tuple):
        """Called when the right mouse button is released.

        Args:
            position: Current mouse position as `(x, y)`.
        """
        raise NotImplementedOrRegisteredError(self.on_mouse_right_released)

    def on_clicked_left(self, position: tuple):
        """Called when the actor is clicked with the left mouse button.

        Args:
            position: Current mouse position as `(x, y)`.

        Examples:
            ::

                @actor.register
                def on_clicked_left(self, position):
                    self.hide()
        """
        raise NotImplementedOrRegisteredError(self.on_clicked_left)

    def on_clicked_right(self, position):
        """Called when the actor is clicked with the right mouse button.

        Args:
            position: Current mouse position as `(x, y)`.

        Examples:
            ::

                @actor.register
                def on_clicked_right(self, position):
                    self.remove()
        """
        raise NotImplementedOrRegisteredError(self.on_clicked_right)

    def on_detecting_world(self):
        """Called when the actor is inside the world.

        Examples:
            ::

                @player.register
                def on_detecting_world(self):
                    self.move()
        """
        raise NotImplementedOrRegisteredError(self.on_detecting_world)

    def on_not_detecting_world(self):
        """Called when the actor is **not** touching the world (i.e. outside world bounds).

        Useful to remove actors that fly off-screen.

        Examples:
            ::

                @rocket.register
                def on_not_detecting_world(self):
                    self.remove()
        """
        raise NotImplementedOrRegisteredError(self.on_not_detecting_world)

    def on_detecting_not_on_world(self):
        """Alias for ``on_not_detecting_world``.

        Both names are accepted so older teaching material and newer examples
        can use the wording that reads best in context.

        Examples:
            ::

                @actor.register
                def on_detecting_not_on_world(self):
                    self.remove()
        """
        raise NotImplementedOrRegisteredError(self.on_detecting_not_on_world)

    def on_detecting_actor(self, actor: "Actor"):
        """Called when this actor detects another actor.

        Args:
            actor: Detected actor.

        Examples:
            ::

                @player.register
                def on_detecting_actor(self, actor):
                    if isinstance(actor, Coin):
                        actor.remove()
        """
        raise NotImplementedOrRegisteredError(self.on_detecting_actor)

    def on_detecting_borders(self, borders: List[str]):
        """Called when the actor detects one or more world borders.

        Args:
            borders: Border names, for example `["left", "top"]`.

        Examples:
            ::

                @player.register
                def on_detecting_borders(self, borders):
                    self.bounce_from_border(borders)
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
        """Fill color of the actor as RGBA tuple.

        Setting this value also enables filling on the costume.

        Notes:
            - Alias: `Actor.color`
            - Filling an image costume replaces the visible image content.
        """
        return self._appearance_facade.fill_color

    @fill_color.setter
    def fill_color(self, value):
        self._ensure_color_like(value, "fill_color")
        self._appearance_facade.fill_color = value

    # Alias
    color = fill_color

    def fill(self, value):
        """Set fill color for borders and lines"""
        self._ensure_color_like(value, "value")
        self._appearance_facade.fill(value)

    @property
    def is_filled(self):
        """Is actor filled with color?"""
        return self._appearance_facade.is_filled

    @is_filled.setter
    def is_filled(self, value):
        if isinstance(value, tuple):
            self._ensure_color_like(value, "is_filled")
        else:
            value = self._coerce_bool_learning(value, "is_filled")
            self._ensure_bool(value, "is_filled")
        self._appearance_facade.is_filled = value

    @property
    def border_color(self):
        """Border color as RGBA tuple.

        Notes:
            - Set `Actor.border` to a value greater than `0` for a visible border.
            - Alias: `Actor.stroke_color`.
        """
        return self._appearance_facade.border_color

    @border_color.setter
    def border_color(self, value):
        self._ensure_color_like(value, "border_color")
        self._appearance_facade.border_color = value

    # Alias

    stroke_color = border_color

    @property
    def border(self):
        """Border width of the actor.

        A value of `0` means no border.

        Notes:
            You can also configure borders via `costume.border` or
            `world.default_border`.
        """
        return self._appearance_facade.border

    @border.setter
    def border(self, value):
        if value is None:
            self._appearance_facade.border = None
            return
        self._ensure_real(value, "border")
        self._appearance_facade.border = value

    @property
    def visible(self):
        """Whether the actor is currently visible."""
        return self._appearance_facade.visible

    @visible.setter
    def visible(self, value):
        value = self._coerce_bool_learning(value, "visible")
        self._ensure_bool(value, "visible")
        self._appearance_facade.visible = value

    def hide(self):
        """Hides a actor (the actor will be invisible)"""
        self._appearance_facade.hide()

    def show(self):
        """Displays a actor ( an invisible actor will be visible)"""
        self._appearance_facade.show()

    def register_sensor(self, *args, **kwargs):
        """This method is used for the @register_sensor decorator."""
        return self._event_facade.register_sensor(*args, **kwargs)

    def get_local_rect(self) -> pygame.Rect:
        """Return actor rect in camera-local coordinates."""
        local_rect = self.position_manager.get_local_rect()
        return local_rect

    @property
    def world(self):
        """World this actor belongs to."""
        return self._world

    @world.setter
    def world(self, new_world):
        self.set_world(new_world)

    def set_world(self, new_world: "world_mod.World") -> "Actor":
        """Move the actor to another world and return the actor."""
        if new_world is None:
            raise TypeError("new_world must not be None")
        if not hasattr(new_world, "get_world_connector"):
            raise TypeError(
                f"new_world must provide get_world_connector(actor), got {type(new_world).__name__}: {new_world!r}"
            )
        return self._event_facade.set_world(new_world)

    def new_costume(self):
        """Create and attach a new empty costume to this actor."""
        return self._appearance_facade.new_costume()

    @property
    def image(self) -> pygame.Surface:
        """
        The image of the actor:

        .. warning::

            Warning: You should not directly draw on the image (with pygame functions)
            as the image will be reloaded during animations

        """
        return self._appearance_facade.image

    @property
    def position(self) -> Tuple[float, float]:
        """The position of the actor as Position(x, y)"""
        return self._movement_facade.get_position()

    @position.setter
    def position(self, value: Tuple[float, float]):
        self.set_position(value)

    def set_position(self, value: Tuple[float, float]):
        """Set actor position in world coordinates."""
        if value is None:
            return
        value = self._coerce_position_learning(value, "value")
        self._ensure_position_tuple(value, "value")
        self._movement_facade.set_position(value)

    def get_distance_to(self, obj: Union["Actor", Tuple[float, float]]) -> float:
        """Gets the distance to another actor or a position

        Args:
            obj: Actor or Position

        Returns:
            float: The distance between actor (measured from actor.center) to actor or position.
        """
        return self._sensor_facade.get_distance_to(obj)

    def on_shape_change(self):
        """Hook called when actor shape-related properties change."""
        pass
