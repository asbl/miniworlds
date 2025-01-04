from typing import Union, Tuple, List
import pygame
import math

import miniworlds.positions.vector as world_vector
import miniworlds.appearances.costume as costume
import miniworlds.worlds.world as world
import miniworlds.base.exceptions as miniworlds_exceptions
import miniworlds.actors.actor as actor_mod
import miniworlds.base.exceptions as exceptions


class Positionmanager:
    """A Position manager connects an actor to a world.

    The position manager behaves differently depending on the world it is connected to.
    It is overwritten in World subclasses
    """

    def __init__(self, actor: "actor_mod.Actor", world: "world.World", position):
        self.actor = actor
        self.last_position = position
        self.position = position
        self._origin = "center"
        self._last_size = (40, 40)
        self._size = (40, 40)
        self.last_direction = 0
        self._direction = 0
        self.is_static = False
        self._initial_direction = 0
        self.is_blockable = False
        self.is_blocking = False
        self._stored_origin = (0, 0)

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        if value not in ["center", "topleft"]:
            raise exceptions.OriginException(self.actor)
        self._origin = value
        self.actor.costume.origin_changed()

    def switch_origin(self, value: str):
        if self.origin == "center" and value == "topleft":
            self.set_position(self._shift_center_to_topleft(self.get_position()))
            self.origin = "topleft"
        elif self.origin == "topleft" and value == "center":
            self.set_position(self._shift_topleft_to_center(self.get_position()))
            self.origin = "center"

    def move_vector(self, vector: "world_vector.Vector") -> "actor_mod.Actor":
        position = self.get_position()
        position = vector.add_to_position(position)
        self.set_position(position)
        return self.actor

    def get_global_rect(self) -> pygame.Rect:
        """Global rect is the the position of the actor on the global
        world.
        This position can be outside the current screen.

        Returns:
            pygame.Rect: A rect with the token coordinates.
        """
        if self.actor.costume:
            _rect = self.actor.costume.get_rect()
        else:
            _rect = pygame.Rect(0, 0, self.actor.size[0], self.actor.size[1])
        if self.origin == "center":
            _rect.center = self.get_center()
        elif self.origin == "topleft":
            _rect.topleft = self.get_topleft()
        return _rect

    def get_local_rect(self) -> pygame.Rect:
        """
        Local rect is the position of the actor on the view
        (defined by camera view)
        """
        _rect = self.get_global_rect()
        if self.origin == "center":
            _rect.center = self.actor.world.camera.get_local_position(
                self.get_center()
            )
        elif self.origin == "topleft":
            _rect.topleft = self.actor.world.camera.get_local_position(
                self.get_topleft()
            )
        else:
            raise Exception
        return _rect
    
    def get_screen_rect(self) -> pygame.Rect:
        """
        Screen rect is the position of the actor inside the current screen.
        (defined by camera view and window position of world)
        """
        _rect = self.get_global_rect()
        if self.origin == "center":
            _rect.center = self.actor.world.camera.get_screen_position(self.get_center())
        elif self.origin == "topleft":
            _rect.topleft = self.actor.world.camera.get_screen_position(self.get_topleft())
        else:
            raise Exception
        return _rect
    
    def get_direction(self):
        direction = (self._direction + 180) % 360 - 180
        return direction

    def set_direction(self, direction: Union[int, float, str, float]):
        if type(direction) not in [
            int,
            float,
            str,
            world_vector.Vector,
        ]:
            raise ValueError(
                f"Direction must be int, float or Vector but is {type(direction)}"
            )
        direction = self.validate_direction(direction)
        self.store_origin()
        self.last_direction = self.get_direction()
        self._direction = direction
        if self.last_direction != self.get_direction():
            self.actor.costume.rotated()
        self.restore_origin()
        return self._direction

    def get_size(self):
        return self._size

    def set_size(self, value: Union[int, float, tuple], scale=False):
        """Sets size of actor

        Args:
            value (Union[int, float, tuple]):
                An int or float will be converted to tuple (e.g. 2 => (2,2) )
            scale: Should size set or should actor be scaled.

        Raises:
            ValueError: Raises ValueError, if type not in [int, float, tuple]

        Returns:
            The actor with changed values
        """
        # Error handling
        if type(value) in [int, float]:
            if value < 0:
                raise ValueError("actor.size must be >= 0")
            else:
                value = (value, value)
        if type(value) != tuple:
            raise ValueError("actor size must be int, float or tuple")
        # Save old position
        self.store_origin()
        # Set the size
        if not scale:  # Set new size absolute
            if value != self._size:
                self._last_size = self._size
                self._size = value
                if self.actor.costume:
                    self.actor.costume.set_dirty(
                        "scale", costume.Costume.RELOAD_ACTUAL_IMAGE
                    )
        else:  # set new size (scaled, relative)
            if value != (1, 1):
                self._last_size = self._size
                self._size = self._size[0] * value[0], self._size[1] * value[1]
                if self.actor.costume:
                    self.actor.costume.set_dirty(
                        "scale", costume.Costume.RELOAD_ACTUAL_IMAGE
                    )
        # Set position to old position (so that size does not move an actor)
        self.restore_origin()
        return self.actor

    def scale_width(self, value):
        old_width = self.actor.size[0]
        old_height = self.actor.size[1]
        scale_factor = value / old_width
        self.set_size((value, old_height * scale_factor))

    def scale_height(self, value):
        old_width = self.actor.size[0]
        old_height = self.actor.size[1]
        scale_factor = value / old_height
        self.set_size((old_width * scale_factor, value))

    def set_width(self, value):
        if value < 0:
            raise ValueError("actor width must be >= 0")
        self.set_size((value, self.actor.size[1]))

    def set_height(self, value):
        if value < 0:
            raise ValueError("actor height must be >= 0")
        self.set_size((self.actor.size[0], value))

    def _shift_center_to_topleft(self, value: Tuple[float, float]):
        rect_center = value
        shift_x = self.get_size()[0] / 2
        shift_y = self.get_size()[1] / 2
        return rect_center[0] - shift_x, rect_center[1] - shift_y

    def _shift_topleft_to_center(self, value: Tuple[float, float]):
        """shift topleft position of actor to center position"""
        shift_x = self.get_size()[0] / 2.0
        shift_y = self.get_size()[1] / 2.0
        return (value[0] + shift_x, value[1] + shift_y)

    def get_position(self) -> Tuple[float, float]:
        """gets center position"""
        return self.position

    def set_position(self, value: Tuple[float]) -> "actor_mod.Actor":
        """sets topleft position

        Args:
            value (Tuple[float, float]): The top-left position of the Actor

        Raises:
            exceptions.NoValidWorldPositionError: Raised, when no valid world position was given

        Returns:
            "actor_mod.Actor": The Actor
        """
        if not value or not isinstance(value, Tuple):
            raise exceptions.NoValidWorldPositionError(value)
        self.last_position = self.get_position()
        self.position = value
        if self.last_position != self.get_position():
            self.actor.dirty = 1
        return self.position

    def store_origin(self):
        if self.origin == "center":
            self._stored_origin = self.get_center()
        elif self.origin == "topleft":
            self._stored_origin = self.get_topleft()

    def restore_origin(self):
        self.position = self._stored_origin

    @property
    def local_center(self) -> Tuple[float, float]:
        """local center in current camera view

        Returns:
            Tuple[float, float]: Center position in camera view
        """
        return self.get_local_rect().center

    def get_center(self) -> Tuple[float, float]:
        if self.origin == "center":
            return self.position
        elif self.origin == "topleft":
            return self._shift_topleft_to_center(self.position)

    def set_center(self, value: Tuple[float, float]) -> "actor_mod.Actor":
        """Sets center position of actor

        Args:
            value (Tuple[float, float]): A position as Tuple, e.g. (200, 10).

        Returns:
            actor_mod.Actor: The actor
        """
        if self.origin == "center":
            self.set_position(value)
        elif self.origin == "topleft":
            self.set_position(self._shift_center_to_topleft(value))
        else:
            raise exceptions.OriginException(self.actor)
        return self.actor

    def get_topleft(self):
        if self.origin == "center":
            return self._shift_center_to_topleft(self.position)
        elif self.origin == "topleft":
            return self.position

    def set_topleft(self, value: Tuple[float, float]):
        if self.origin == "topleft":
            self.set_position(value)
        elif self.origin == "center":
            self.set_position(self._shift_topleft_to_center(value))
        else:
            raise Exception

    def move(self, distance: int = 0) -> "actor_mod.Actor":
        # Set distance
        if distance == 0:
            distance = self.actor.speed
        # set destination
        if distance >= 0:
            destination = self.actor.sensor_manager.get_destination(
            self.get_position(), self.get_direction(), distance
        )
        elif distance < 0:
            destination = self.actor.sensor_manager.get_destination(
            self.get_position(), -self.get_direction(), distance
        )
        if self.is_blockable:
            found_actors = self.actor.sensor_manager.detect_actors_at_destination(destination)
            found_blocking = False
            for actor in found_actors:
                if actor.is_blocking:
                    found_blocking = True
                    break
            if not found_blocking:
                self.set_position(destination)
        else:
            self.set_position(destination)
            self.last_direction = self.get_direction()
        return self.actor

    def move_towards_position(
        self, position: Tuple[float, float], distance=1
    ) -> "actor_mod.Actor":
        if self.__class__.is_close(self.get_position(), position):
            return self.actor
        else:
            direction = self.direction_from_two_points(self.actor.position, position)
            self.set_direction(direction)
            self.move(distance)
            return self.actor

    def move_in_direction(
        self, direction: Union[float, str, Tuple[float, float]], distance: int = 1
    ):
        direction = self.validate_direction(direction)
        if type(direction) in [
            int,
            float,
            str,
        ]:  
            self.set_direction(direction)
            self.move(distance)
            return self
        elif type(direction) in [tuple]:
            return self.move_towards_position(direction)
        else:
            raise miniworlds_exceptions.MiniworldsError(
                f"No valid type in method move_in_direction - Expected int, str, Position or tuple, got {type(direction)}"
            )
    

    def undo_move(self) -> "actor_mod.Actor":
        self.set_position(self.last_position)
        return self.actor

    def move_to(self, new_position: Tuple[float, float]) -> "actor_mod.Actor":
        self.position = new_position
        return self.actor

    @staticmethod
    def dir_to_unit_circle(direction: float) -> float:
        """
        Transforms the current direction into standard-unit-circle direction

        Args:
            value: The direction in scratch-style
        """
        return -(direction + 90) % 360 - 180

    @staticmethod
    def unit_circle_to_dir(direction: float) -> float:
        """
        Transforms the current direction from standard-unit-circle direction
        into scratch-style coordinates

        Args:
            value: The direction in math unit circle style.
        """
        return -(direction + 90) % 360 - 180

    def bounce_from_border(self, borders: Union[Tuple, List]):
        """Bounces the actor from a border.

        Args:
            borders: A list of borders as strings e.g. ["left", "right"]

        Returns: The actor

        """
        angle = self.get_direction()
        if "top" in borders and (
            self.get_direction() <= 0
            and self.get_direction() > -90
            or self.get_direction() <= 90
            and self.get_direction() >= 0
        ):
            self.set_direction(0)
            incidence = self.get_direction() - angle
            self.turn_left(180 - incidence)
        elif "bottom" in borders and (
            (self.get_direction() < -90 and self.get_direction() >= -180)
            or (self.get_direction() > 90 and self.get_direction() <= 180)
        ):
            self.set_direction(180)
            incidence = self.get_direction() - angle
            self.turn_left(180 - incidence)
        elif "left" in borders and self.get_direction() <= 0:
            self.set_direction(-90)
            incidence = self.get_direction() - angle
            self.turn_left(180 - incidence)
        elif "right" in borders and (self.get_direction() >= 0):
            self.set_direction(90)
            incidence = self.get_direction() - angle
            self.turn_left(180 - incidence)
        return self

    def bounce_from_actor(self, other):
        """experimental: Bounces actor from another actor
        Args:
            actor: the actor

        Returns: the actor

        """
        angle = self.actor.direction
        self.actor.move(-self.actor.speed)
        self.actor.point_towards_actor(other)
        incidence = self.actor.direction - angle
        self.actor.turn_left(180 - incidence)
        return self.actor

    def turn_left(self, degrees: float = 90) -> int:
        return self.set_direction(self.get_direction() - degrees)

    def turn_right(self, degrees: float = 90):
        return self.set_direction(self.get_direction() + degrees)

    def flip_x(self) -> int:
        """Flips actor

        Returns:
            int: new direction
        """
        self.turn_left(180)
        self.actor.costume.flip(not self.actor.costume.is_flipped)
        return self.get_direction()

    def self_remove(self):
        """Method is overwritten in subclasses"""
        pass

    @property
    def x(self) -> float:
        return self.get_position()[0]

    @x.setter
    def x(self, value) -> float:
        self.set_position((value, self.y))

    @property
    def y(self) -> float:
        return self.get_position()[1]

    @y.setter
    def y(self, value: float):
        self.set_position((self.x, value))

    def draw_position(self):
        return (self.x, self.y)

    def point_towards_position(self, destination: Union[float, str]) -> float:
        """
        Actor points towards a given position

        Args:
            destination: The position to which the actor should pointing

        Returns:
            The new direction

        """
        direction = self.direction_from_two_points(
            self.actor.center, destination
        )
        self.set_direction(direction)
        return self.get_direction()

    @staticmethod
    def validate_direction(value: [float, str]) -> float:
        """
        Transforms a string value ("top", "left", "right", "bottom)
        into a position

        Args:
            value: The String value ("top", "left", "right", or "bottom)

        Returns:
            The position as scratch-style degrees

        """
        if value == "top" or value == "up":
            value = 0
        elif value == "left":
            value = 270
        elif value == "right":
            value = 90
        elif value == "down":
            value = 180
        elif isinstance(value, world_vector.Vector):
            value = value.to_direction() % 360
        else:
            value = value % 360
        return value

    @staticmethod
    def direction_from_two_points(
        pos1: Tuple[float, float], pos2: Tuple[float, float]
    ) -> float:
        x = pos2[0] - pos1[0]
        y = pos2[1] - pos1[1]
        if x != 0:
            m = y / x
            if x < 0:
                # destination is left
                direction = math.degrees(math.atan(m)) - 90
            else:
                # destination is right
                direction = math.degrees(math.atan(m)) + 90
            return direction
        else:
            m = 0
            if pos2[1] > pos1[1]:
                direction = 180
            else:
                direction = 0
            return direction

    def is_close(
        pos1: Tuple[float, float], pos2: Tuple[float, float], error: float = 1
    ) -> bool:
        """Is a position close to another position

        Args:
            pos1 (Tuple[float, float]): The first position
            pos2 (Tuple[float, float]): The second position
            error (float): Allowed error in difference between the two positions. Defaults to 1

        Returns:
            bool: True, if positions are close to each other
        """
        if abs(pos1[0] - pos2[0]) < error and abs(pos2[1] - pos2[1]) < error:
            return True
        return False

    def get_screen_position(self, coordinates):
        return (coordinates[0] + self.actor.world.topleft[0], coordinates[1] + self.actor.world.topleft[1])
