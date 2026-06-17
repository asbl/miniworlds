import math
from typing import Union, Tuple, Any

import numpy as np


class Vector:
    """2D vector for movement, geometry, and physics.

    Supports arithmetic with both other Vectors and 2D tuples.

    Examples:
        ::

            direction = Vector.from_actors(enemy, player)
            enemy.move_vector(direction.normalize() * 2)
    """

    def __init__(self, x: float, y: float) -> None:
        """Create a 2D vector.

        Args:
            x: Horizontal component.
            y: Vertical component.
        """
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
        """The x-component of the vector."""
        return self.vec[0]

    @x.setter
    def x(self, value: float) -> None:
        self.vec[0] = value

    @property
    def y(self) -> float:
        """The y-component of the vector."""
        return self.vec[1]

    @y.setter
    def y(self, value: float) -> None:
        self.vec[1] = value

    @property
    def angle(self) -> float:
        """float: Direction angle in Miniworlds convention.

        `0` points up and `90` points right. Equivalent to `to_direction()`.
        """
        return self.to_direction()

    def to_position(self) -> Tuple[float, float]:
        """Return the vector as an `(x, y)` tuple."""
        return (self.x, self.y)

    @classmethod
    def from_position(cls, position: Tuple[float, float]) -> "Vector":
        """Create a vector from a position.

        Args:
            position: Position as `(x, y)`.

        Returns:
            A new Vector with the same x and y components.

        Examples:
            ::

                vector = Vector.from_position(actor.position)
        """
        if not (isinstance(position, tuple) and len(position) == 2):
            raise TypeError("Position must be a tuple of two float values.")
        return cls(*position)

    @classmethod
    def from_positions(cls, p1: Tuple[float, float], p2: Tuple[float, float]) -> "Vector":
        """Create a vector pointing from `p1` to `p2`.

        Args:
            p1: Start position as `(x, y)`.
            p2: End position as `(x, y)`.

        Returns:
            Vector equal to `p2 - p1`.
        """
        return cls(p2[0] - p1[0], p2[1] - p1[1])

    @classmethod
    def from_direction(cls, direction: Union[str, int, float]) -> "Vector":
        """Create a unit vector from a Miniworlds direction.

        Args:
            direction: Direction in Miniworlds convention. Common values are
                `0` or `"up"`, `90` or `"right"`, `-90` or `"left"`, and
                `180` or `"down"`.

        Returns:
            A new unit Vector pointing in the given direction.

        Examples:
            ::

                @player.register
                def on_key_pressed_right(self):
                    step = Vector.from_direction("right") * 5
                    self.move_vector(step)
        """
        if isinstance(direction, str):
            normalized = direction.strip().lower()
            mapping = {
                "up": 0,
                "top": 0,
                "right": 90,
                "down": 180,
                "bottom": 180,
                "left": 270,
            }
            if normalized in mapping:
                direction = mapping[normalized]
            else:
                raise ValueError(
                    f"Unsupported direction string '{direction}'. "
                    "Use one of: up, right, down, left, top, bottom."
                )

        direction = float(direction)
        x = math.sin(math.radians(direction))
        y = -math.cos(math.radians(direction))
        return cls(x, y)

    @classmethod
    def from_actors(cls, t1: "actor_mod.Actor", t2: "actor_mod.Actor") -> "Vector":
        """Create a vector from one actor to another actor.

        Args:
            t1: Start actor.
            t2: Target actor.

        Returns:
            A vector equal to `t2.center - t1.center`.

        Examples:
            ::

                enemy_vector = Vector.from_actors(player, enemy)
                if enemy_vector.length() < 50:
                    player.move_away(enemy, 3)
        """
        x = t2.center[0] - t1.center[0]
        y = t2.center[1] - t1.center[1]
        return cls(x, y)

    @classmethod
    def from_actor_and_position(cls, t1: "actor_mod.Actor", pos) -> "Vector":
        """Create a vector from an actor center to a target position.

        Args:
            t1: The start actor.
            pos: Target position as `(x, y)`.

        Returns:
            A vector equal to `pos - t1.center`.

        Examples:
            ::

                vector = Vector.from_actor_and_position(player, (100, 80))
        """
        x = pos[0] - t1.center[0]
        y = pos[1] - t1.center[1]
        return cls(x, y)

    @classmethod
    def from_actor_direction(cls, actor: "actor_mod.Actor") -> "Vector":
        """Create a unit vector from an actor direction.

        Args:
            actor: Actor whose direction is used.

        Returns:
            A unit vector pointing in the actor direction.

        Examples:
            ::

                step = Vector.from_actor_direction(player) * 5
                player.move_vector(step)
        """
        return Vector.from_direction(actor.direction)


    def rotate(self, theta: float) -> "Vector":
        """Rotate the vector in-place.

        Args:
            theta: Rotation angle in degrees.

        Returns:
            The vector itself.

        Examples:
            ::

                vector.rotate(90)
        """
        radians = np.deg2rad(theta % 360)
        rot = np.array([[math.cos(radians), -math.sin(radians)],
                        [math.sin(radians), math.cos(radians)]])
        self.vec = np.dot(rot, self.vec)
        return self

    def to_direction(self) -> float:
        """Convert the vector to a Miniworlds direction.

        Returns:
            Direction in degrees. Returns `0` for a zero-length vector.
        """
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
        """Normalize the vector to length 1 in-place.

        Returns:
            The vector itself. A zero-length vector is returned unchanged.
        """
        norm = np.linalg.norm(self.vec)
        if norm == 0:
            return self
        self.vec = self.vec / norm
        return self

    def length(self) -> float:
        """Return the Euclidean length of the vector.

        Returns:
            Length as a float.
        """
        return float(np.linalg.norm(self.vec))

    def limit(self, max_length: float) -> "Vector":
        """Cap the vector length without changing its direction.

        Args:
            max_length: Maximum allowed length.

        Returns:
            The vector itself.

        Examples:
            ::

                velocity.limit(10)
        """
        if self.length() > max_length:
            self.vec = self.normalize().vec * max_length
        return self

    def multiply(self, other: Union[float, int, "Vector"]) -> Union["Vector", float]:
        """Multiply by a scalar or compute a dot product.

        Args:
            other: Scalar value or another `Vector`.

        Returns:
            A scaled `Vector` for scalar input, or a dot product for vectors.
        """
        if isinstance(other, (int, float)):
            return Vector(self.x * other, self.y * other)
        if isinstance(other, Vector):
            return self.dot(other)
        raise TypeError(
            f"Can't multiply Vector by {type(other).__name__}. "
            f"Multiply Vector by a number instead. "
            f"Example: my_vector * 2 or my_vector * 0.5"
        )

    def add_to_position(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """Add the vector to a position.

        Args:
            position: Position as `(x, y)`.

        Returns:
            New position as `(x + self.x, y + self.y)`.
        """
        return (self.x + position[0], self.y + position[1])

    def get_normal(self) -> "Vector":
        """Return a vector perpendicular to this one.

        Returns:
            A new Vector rotated 90° counter-clockwise.
        """
        return Vector(-self.y, self.x)

    def dot(self, other: "Vector") -> float:
        """Compute the dot product.

        Args:
            other: The other Vector.

        Returns:
            Dot product as a float.
        """
        return float(np.dot(self.vec, other.vec))

    def distance_to(self, other: Union["Vector", Tuple[float, float]]) -> float:
        """Calculate the Euclidean distance to another vector or position.

        Args:
            other: A Vector or tuple.

        Returns:
            The distance as float.

        Examples:
            ::

                distance = Vector(0, 0).distance_to((3, 4))
        """
        other = self._to_vector(other)
        return float(np.linalg.norm(self.vec - other.vec))

    def angle_to(self, other: Union["Vector", Tuple[float, float]]) -> float:
        """Compute the angle to another vector or position.

        Args:
            other: A Vector or tuple.

        Returns:
            Angle in degrees between 0 and 180.

        Examples:
            ::

                angle = Vector(1, 0).angle_to((0, 1))
        """
        other = self._to_vector(other)
        len_self = np.linalg.norm(self.vec)
        len_other = np.linalg.norm(other.vec)
        if len_self == 0 or len_other == 0:
            return 0.0
        norm_self = self.vec / len_self
        norm_other = other.vec / len_other
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
