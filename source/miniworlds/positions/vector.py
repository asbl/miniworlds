import math
from typing import Union, Tuple, Any

import numpy as np


class Vector:
    """
    Represents a 2D vector for use in movement, geometry, and physics.

    Supports arithmetic with both other Vectors and 2D tuples.

    Examples:
        >>> v = Vector(1, 2)
        >>> v2 = Vector(3, 4)
        >>> v + v2
        Vector(4.0, 6.0)
        >>> v + (1, 1)
        Vector(2.0, 3.0)
        >>> (1, 1) + v
        Vector(2.0, 3.0)
    """

    def __init__(self, x: float, y: float) -> None:
        self.vec = np.array([x, y], dtype=float)

    @staticmethod
    def _to_vector(value: Union["Vector", Tuple[float, float]]) -> "Vector":
        if isinstance(value, Vector):
            return value
        if isinstance(value, tuple) and len(value) == 2:
            return Vector(*value)
        raise TypeError(f"Expected Vector or 2-tuple, got {type(value)}.")

    def __getitem__(self, index: int) -> float:
        return self.vec[index]

    @property
    def x(self) -> float:
        return self.vec[0]

    @x.setter
    def x(self, value: float) -> None:
        self.vec[0] = value

    @property
    def y(self) -> float:
        return self.vec[1]

    @y.setter
    def y(self, value: float) -> None:
        self.vec[1] = value

    @property
    def angle(self) -> float:
        return self.to_direction()

    def to_position(self) -> Tuple[float, float]:
        return (self.x, self.y)

    @classmethod
    def from_position(cls, position: Tuple[float, float]) -> "Vector":
        if not (isinstance(position, tuple) and len(position) == 2):
            raise TypeError("Position must be a tuple of two float values.")
        return cls(*position)

    @classmethod
    def from_positions(cls, p1: Tuple[float, float], p2: Tuple[float, float]) -> "Vector":
        return cls(p2[0] - p1[0], p2[1] - p1[1])

    @classmethod
    def from_direction(cls, direction: Union[str, int, float, str]) -> "Vector":
        """Creates a vector from miniworlds direction."""
        if direction >= 90:
            x = 0 + math.sin(math.radians(direction)) * 1
            y = 0 - math.cos(math.radians(direction)) * 1
        else:
            x = 0 + math.sin(math.radians(direction)) * 1
            y = 0 - math.cos(math.radians(direction)) * 1
        return cls(x, y)

    @classmethod
    def from_actors(cls, t1: "actor_mod.Actor", t2: "actor_mod.Actor") -> "Vector":
        """Create a vector from two actors.

        The vector describes is generated from:
        actor2.center - actor1.center
        """
        x = t2.center[0] - t1.center[0]
        y = t2.center[1] - t1.center[1]
        return cls(x, y)

    @classmethod
    def from_actor_and_position(cls, t1: "actor_mod.Actor", pos) -> "Vector":
        """Create a vector from actor and position

        The vector describes is generated from:
        actor2.center - position
        """
        x = pos[0] - t1.center[0]
        y = pos[1] - t1.center[1]
        return cls(x, y)

    @classmethod
    def from_actor_direction(cls, actor: "actor_mod.Actor") -> "Vector":
        """Creates a vector from actor direction

        Examples:

            Creates rotating rectangle

            .. code-block:: python

                from miniworlds import *

                world = World()

                player = Rectangle((200,200),40, 40)
                player.speed = 1
                player.direction = 80

                @player.register
                def act(self):
                    v1 = Vector.from_actor_direction(self)
                    v1.rotate(-1)
                    self.direction = v1

                world.run()

        .. raw:: html

             <video loop autoplay muted width="400">
            <source src="../_static/mp4/rotating_rectangle.mp4" type="video/mp4">
            <source src="../_static/rotating_rectangle.webm" type="video/webm">
            Your browser does not support the video tag.
            </video>
        """
        return Vector.from_direction(actor.direction)


    def rotate(self, theta: float) -> "Vector":
        radians = np.deg2rad(theta % 360)
        rot = np.array([[math.cos(radians), -math.sin(radians)],
                        [math.sin(radians), math.cos(radians)]])
        self.vec = np.dot(rot, self.vec)
        return self

    def to_direction(self) -> float:
        if self.length() == 0:
            return 0.0
        axis = np.array([0, -1])
        unit_vector = self.vec / np.linalg.norm(self.vec)
        dot = np.dot(unit_vector, axis)
        angle = math.degrees(math.acos(dot))
        if self.x < 0:
            angle = 360 - angle
        return angle

    def normalize(self) -> "Vector":
        norm = np.linalg.norm(self.vec)
        if norm == 0:
            return self
        self.vec = self.vec / norm
        return self

    def length(self) -> float:
        return float(np.linalg.norm(self.vec))

    def limit(self, max_length: float) -> "Vector":
        if self.length() > max_length:
            self.vec = self.normalize().vec * max_length
        return self

    def multiply(self, other: Union[float, int, "Vector"]) -> Union["Vector", float]:
        if isinstance(other, (int, float)):
            return Vector(self.x * other, self.y * other)
        if isinstance(other, Vector):
            return self.dot(other)
        raise TypeError("Unsupported operand type for multiply.")

    def add_to_position(self, position: Tuple[float, float]) -> Tuple[float, float]:
        return (self.x + position[0], self.y + position[1])

    def get_normal(self) -> "Vector":
        return Vector(-self.y, self.x)

    def dot(self, other: "Vector") -> float:
        return float(np.dot(self.vec, other.vec))

    def distance_to(self, other: Union["Vector", Tuple[float, float]]) -> float:
        """
        Calculates Euclidean distance to another vector or position.

        Args:
            other: A Vector or tuple.

        Returns:
            The distance as float.

        Examples:
            >>> Vector(0, 0).distance_to((3, 4))
            5.0
        """
        other = self._to_vector(other)
        return float(np.linalg.norm(self.vec - other.vec))

    def angle_to(self, other: Union["Vector", Tuple[float, float]]) -> float:
        """
        Computes the angle between this vector and another in degrees.

        Args:
            other: A Vector or tuple.

        Returns:
            Angle in degrees between 0 and 180.

        Examples:
            >>> Vector(1, 0).angle_to((0, 1))
            90.0
        """
        other = self._to_vector(other)
        norm_self = self.vec / np.linalg.norm(self.vec)
        norm_other = other.vec / np.linalg.norm(other.vec)
        dot = np.clip(np.dot(norm_self, norm_other), -1.0, 1.0)
        return math.degrees(math.acos(dot))

    def __add__(self, other: Union["Vector", Tuple[float, float]]) -> "Vector":
        other = self._to_vector(other)
        return Vector(self.x + other.x, self.y + other.y)

    def __radd__(self, other: Union["Vector", Tuple[float, float]]) -> "Vector":
        return self.__add__(other)

    def __sub__(self, other: Union["Vector", Tuple[float, float]]) -> "Vector":
        other = self._to_vector(other)
        return Vector(self.x - other.x, self.y - other.y)

    def __rsub__(self, other: Union["Vector", Tuple[float, float]]) -> "Vector":
        other = self._to_vector(other)
        return Vector(other.x - self.x, other.y - self.y)

    def __mul__(self, other: Union[float, int, "Vector", Tuple[float, float]]) -> Union["Vector", float]:
        if isinstance(other, (int, float)):
            return Vector(self.x * other, self.y * other)
        other = self._to_vector(other)
        return self.dot(other)

    def __rmul__(self, other: Union[float, int, "Vector", Tuple[float, float]]) -> Union["Vector", float]:
        return self.__mul__(other)

    def __neg__(self) -> "Vector":
        return Vector(-self.x, -self.y)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Vector):
            return np.allclose(self.vec, other.vec)
        if isinstance(other, tuple) and len(other) == 2:
            return np.allclose(self.vec, np.array(other, dtype=float))
        return False

    def __str__(self) -> str:
        return f"({round(self.x, 3)}, {round(self.y, 3)})"

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"
