from numbers import Real
from typing import Tuple, Union, TYPE_CHECKING, Any

import pygame
import pygame.gfxdraw

import miniworlds.actors.actor as actor
import miniworlds.actors.shapes.shape_costume as shape_costume
import miniworlds.positions.vector as world_vector
from miniworlds.base.exceptions import (
    EllipseWrongArgumentsError,
    LineFirstArgumentError,
    LineSecondArgumentError,
)

if TYPE_CHECKING:
    import miniworlds.appearances.costume as costume_mod


def _is_real_number(value) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _ensure_point(value, parameter_name: str) -> None:
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or not all(_is_real_number(coord) for coord in value)
    ):
        raise TypeError(
            f"{parameter_name} must be a tuple (x, y) of int or float values, got {type(value).__name__}: {value!r}"
        )


def _ensure_real(value, parameter_name: str) -> None:
    if not _is_real_number(value):
        raise TypeError(
            f"{parameter_name} must be int or float, got {type(value).__name__}: {value!r}"
        )


def _ensure_non_negative_real(value, parameter_name: str) -> None:
    _ensure_real(value, parameter_name)
    if value < 0:
        raise ValueError(f"{parameter_name} must be >= 0, got {value}")


def _ensure_pointlist(pointlist, parameter_name: str = "pointlist") -> None:
    if not isinstance(pointlist, (list, tuple)) or len(pointlist) < 3:
        raise TypeError(
            f"{parameter_name} must contain at least three points, got {pointlist!r}"
        )
    for index, point in enumerate(pointlist):
        _ensure_point(point, f"{parameter_name}[{index}]")


class Shape(actor.Actor):
    """Base class for geometric actors.

    Shapes share the common actor appearance properties `border`,
    `is_filled`, `fill_color`, and `border_color`.

    Examples:
        ::

            shape.fill_color = (255, 0, 0)
            shape.border = 2
    """

    def __init__(self, position: Tuple[float, float] = (0, 0), *args, **kwargs):
        super().__init__(position, *args, **kwargs)
        self.costume_manager.has_appearance = True

    def new_costume(self) -> "shape_costume.ShapeCostume":
        return shape_costume.ShapeCostume(self)

    def get_costume_class(self) -> "shape_costume.ShapeCostume":
        return shape_costume.ShapeCostume

class Circle(Shape):
    """Circular shape.

    Args:
        position: Center position as `(x, y)`.
        radius: Circle radius in pixels.

    Examples:
        ::

            circle = Circle((200, 100), 20)
            circle.fill_color = (255, 0, 0)

            circle = Circle.from_topleft((100, 100), 50)
    """

    def __init__(
            self,
            position: Tuple[float, float] = (0.0, 0.0),
            radius: float = 10.0,
            *args: Any,
            **kwargs: Any
        ) -> None:
            """Create a circle.

            Args:
                position: Center position as `(x, y)`.
                radius: Circle radius in pixels.
            """
            _ensure_point(position, "position")
            _ensure_non_negative_real(radius, "radius")

            self._radius = float(radius)
            super().__init__(position, *args, **kwargs)
            self.costume = shape_costume.CircleCostume(self)
            self.position_manager.set_size((self._radius * 2, self._radius * 2), scale=False)
        
    @property
    def radius(self):
        """float: Circle radius in pixels.

        Examples:
            ::

                circle.radius = 30
        """
        return self._radius

    @radius.setter
    def radius(self, value):
        _ensure_non_negative_real(value, "radius")
        self._radius = float(value)
        self.position_manager.set_size((self._radius * 2, self._radius * 2), scale=False)
        self.costume.set_dirty("scale", self.costume.RELOAD_ACTUAL_IMAGE)

    def _set_physics(self):
        self.physics.shape_type = "circle"
        self.physics.can_move = True
        self.physics.stable = False

    @classmethod
    def from_topleft(cls, position: tuple, radius: int, **kwargs):
        """Create a circle positioned by its top-left corner.

        Args:
            position: Top-left position as `(x, y)`.
            radius: Circle radius in pixels.

        Returns:
            The created circle.
        """
        circle = cls(position, radius, **kwargs)
        circle.origin = "topleft"
        return circle

    @classmethod
    def from_center(cls, position: tuple, radius: float, **kwargs):
        """Create a circle positioned by its center.

        Args:
            position: Center position as `(x, y)`.
            radius: Circle radius in pixels.

        Returns:
            The created circle.
        """
        circle = cls(position, radius, **kwargs)
        circle.origin = "center"
        return circle

    def new_costume(self):
        return shape_costume.CircleCostume(self)

    def get_costume_class(self) -> type["costume_mod.Costume"]:
        return shape_costume.CircleCostume


class Point(Circle):
    """Circle with radius 1.

    Args:
        position: Point position as `(x, y)`.

    Examples:
        ::

            point = Point((10, 10))
    """

    def __init__(self, position: tuple):
        """Create a point at a position."""
        super().__init__(position, 1)


class Ellipse(Shape):
    """Elliptic shape.

    Args:
        position: Top-left position as `(x, y)`.
        width: Ellipse width in pixels.
        height: Ellipse height in pixels.

    Examples:
        ::

            ellipse = Ellipse((200, 100), 20, 30)
            ellipse = Ellipse.from_center((100, 100), 10, 10)
    """

    def __init__(
        self, position=(0, 0), width: float = 10, height: float = 10, *args, **kwargs
    ):
        self.check_arguments(position, width, height)
        super().__init__(position, *args, **kwargs)
        self.costume = shape_costume.EllipseCostume(self)
        self._border = 1
        self.size = (width, height)

    def check_arguments(self, position, width, height):
        """Validate constructor arguments for `Ellipse`.

        Args:
            position: Position as `(x, y)`.
            width: Ellipse width in pixels.
            height: Ellipse height in pixels.

        Raises:
            EllipseWrongArgumentsError: If *position* is not a tuple.
        """
        if position is None:
            return
        if not isinstance(position, tuple):
            raise EllipseWrongArgumentsError()
        _ensure_point(position, "position")
        _ensure_non_negative_real(width, "width")
        _ensure_non_negative_real(height, "height")

    @classmethod
    def from_topleft(cls, position: tuple, width: float, height: float, **kwargs):
        """Create an ellipse positioned by its top-left corner."""
        ellipse = cls(position, width, height, **kwargs)
        ellipse.origin = "topleft"
        return ellipse

    @classmethod
    def from_center(cls, position: tuple, width: float, height: float, **kwargs):
        """Create an ellipse positioned by its center."""
        ellipse = cls(position, width, height, **kwargs)
        ellipse.origin = "center"
        return ellipse

    def new_costume(self):
        return shape_costume.EllipseCostume(self)

    def get_costume_class(self) -> type["costume_mod.Costume"]:
        return shape_costume.EllipseCostume

class Arc(Ellipse):
    """Elliptic arc shape.

    Args:
        position: Top-left position as `(x, y)`.
        width: Arc width in pixels.
        height: Arc height in pixels.
        start_angle: Start angle in degrees.
        end_angle: End angle in degrees.

    Examples:
        ::

            arc = Arc((20, 20), 100, 60, 0, 180)
    """

    def __init__(
        self,
        position=(0, 0),
        width: float = 10,
        height: float = 10,
        start_angle: float = 0,
        end_angle: float = 0,
        *args,
        **kwargs,
    ):
        _ensure_real(start_angle, "start_angle")
        _ensure_real(end_angle, "end_angle")
        self._start_angle = start_angle
        self._end_angle = end_angle
        if start_angle == end_angle:
            self._end_angle = start_angle + 360
        super().__init__(position, width, height, *args, **kwargs)
        self.costume = shape_costume.ArcCostume(self)

    @property
    def start_angle(self):
        """float: Start angle in degrees."""
        return self._start_angle

    @start_angle.setter
    def start_angle(self, value):
        _ensure_real(value, "start_angle")
        self._start_angle = value
        self.costume.set_dirty("draw_shapes", self.costume.RELOAD_ACTUAL_IMAGE)

    @property
    def end_angle(self):
        """float: End angle in degrees."""
        return self._end_angle

    @end_angle.setter
    def end_angle(self, value):
        _ensure_real(value, "end_angle")
        self._end_angle = value
        self.costume.set_dirty("draw_shapes", self.costume.RELOAD_ACTUAL_IMAGE)

    @classmethod
    def from_center(
        cls,
        position: tuple,
        width: float,
        height: float,
        start_angle: float = 0,
        end_angle: float = 360,
        **kwargs
    ):
        """Create an arc positioned by its center."""
        arc = cls(
            position,
            width,
            height,
            start_angle=start_angle,
            end_angle=end_angle,
            **kwargs
        )
        arc.origin = "center"
        return arc


class Line(Shape):
    """Line shape between two positions.

    Args:
        start_position: Start position as `(x, y)`.
        end_position: End position as `(x, y)`.

    Examples:
        ::

            line = Line((200, 100), (400, 100))
            line.border = 2
    """

    def __init__(
        self, start_position: Union[tuple], end_position: Union[tuple], *args, **kwargs
    ):
        try:
            _ensure_point(start_position, "start_position")
        except TypeError:
            raise LineFirstArgumentError(start_position)
        try:
            _ensure_point(end_position, "end_position")
        except TypeError:
            raise LineSecondArgumentError(end_position)
        self._length = 0
        self._start_position = start_position
        self._end_position = end_position
        super().__init__(start_position)
        self.costume = shape_costume.LineCostume(self)
        self._update_size()

    @property
    def start_position(self):
        """tuple[float, float]: Start point as `(x, y)`."""
        return self._start_position

    start = start_position

    @start_position.setter
    def start_position(self, value):
        try:
            _ensure_point(value, "start_position")
        except TypeError:
            raise LineFirstArgumentError(value)
        self._start_position = value
        self._update_size()

    @property
    def end_position(self):
        """tuple[float, float]: End point as `(x, y)`."""
        return self._end_position

    end = end_position

    @end_position.setter
    def end_position(self, value):
        try:
            _ensure_point(value, "end_position")
        except TypeError:
            raise LineSecondArgumentError(value)
        self._end_position = value
        self._update_size()

    @property
    def direction(self):
        return self.position_manager.get_direction()

    @direction.setter
    def direction(self, value):
        self.position_manager.set_direction(value)
        vec_center = world_vector.Vector.from_position(self.center)
        direction_vector = world_vector.Vector.from_direction(self.direction)
        direction_vector = direction_vector.normalize() * self._length * 0.5
        self._start_position = (vec_center + direction_vector).to_position()
        self._end_position = (vec_center - direction_vector).to_position()

    def _set_physics(self):
        self.physics.shape_type = "line"
        self.physics.simulation = "manual"

    def get_bounding_box(self):
        """Return the rectangular bounding box that contains the line.

        Returns:
            Bounding rectangle including line thickness.
        """
        width = abs(self.start_position[0] - self.end_position[0]) + self.thickness
        height = abs(self.start_position[1] - self.end_position[1]) + self.thickness
        box = pygame.Rect(
            min(self.start_position[0], self.end_position[0])
            - int(0.5 * self.thickness),
            min(self.start_position[1], self.end_position[1])
            - int(0.5 * self.thickness),
            width,
            height,
        )
        return box

    def _update_size(self):
        self._length = self.world.distance_to(self.start_position, self._end_position)
        self.position_manager.set_size(
            (self.thickness, self._length + 2 * self.thickness), scale=False
        )
        self.position_manager.set_direction(
            self.world.direction_to(self.start_position, self._end_position)
        )
        vec_to_center = (
            world_vector.Vector.from_positions(self.start_position, self.end_position)
            * 0.5
        )
        self.center = (
            self.start_position[0] + vec_to_center.x,
            self.start_position[1] + vec_to_center.y,
        )
        self.costume.set_dirty("all", 1)

    @property
    def length(self):
        """float: Current line length in pixels."""
        return self._length

    @property
    def thickness(self):
        """float: Line thickness in pixels."""
        return self.costume.border

    @thickness.setter
    def thickness(self, value):
        _ensure_non_negative_real(value, "thickness")
        self.costume.border = value
        self._update_size()

    @property
    def border(self):
        """float: Line thickness in pixels."""
        return self.costume.border

    @border.setter
    def border(self, value):
        _ensure_non_negative_real(value, "border")
        self.costume.border = value
        self._update_size()

    line_width = thickness

    def new_costume(self):
        return shape_costume.LineCostume(self)

    def get_costume_class(self) -> type["costume_mod.Costume"]:
        return shape_costume.LineCostume

class Rectangle(Shape):
    """Rectangular shape.

    Args:
        position: Top-left position as `(x, y)`.
        width: Rectangle width in pixels.
        height: Rectangle height in pixels.

    Examples:
        ::

            rectangle = Rectangle((200, 100), 20, 10)
    """

    def __init__(
        self, position=(0, 0), width: float = 10, height: float = 10, *args, **kwargs
    ):
        args = (width, height, *args)
        super().__init__(position, *args, **kwargs)
        self.costume = shape_costume.RectangleCostume(self)
        self.size = (width, height)

    def _validate_arguments(self, position, *args, **kwargs):
        super()._validate_arguments(position, *args, **kwargs)
        width = args[0]
        height = args[1]
        _ensure_non_negative_real(width, "width")
        _ensure_non_negative_real(height, "height")

    def _set_physics(self):
        self.physics.shape_type = "rect"
        self.physics.stable = False
        self.physics.correct_angle = 90

    @classmethod
    def from_topleft(cls, position: tuple, width: float, height: float):
        """Create a rectangle positioned by its top-left corner."""
        rectangle = cls(position, width, height)
        rectangle.topleft = position
        return rectangle

    @classmethod
    def from_center(cls, position: tuple, width: float, height: float):
        """Create a rectangle positioned by its center."""
        rectangle = cls(position, width, height)
        rectangle.center = rectangle.position
        return rectangle


    def new_costume(self):
        return shape_costume.RectangleCostume(self)

    def get_costume_class(self) -> type["costume_mod.Costume"]:
        return shape_costume.RectangleCostume


class Polygon(Shape):
    """Polygon shape.

    Args:
        pointlist: List of corner points.

    Examples:
        ::

            polygon = Polygon([(200, 100), (400, 100), (0, 0)])
            polygon.fill_color = (255, 0, 0)
    """

    def __init__(self, pointlist, *args, **kwargs):
        _ensure_pointlist(pointlist)
        super().__init__((0, 0))
        self._pointlist = list(pointlist)
        self.costume = shape_costume.PolygonCostume(self, self._pointlist)

    @property
    def pointlist(self):
        """list[tuple[float, float]]: Polygon corner points."""
        return self._pointlist

    @pointlist.setter
    def pointlist(self, value):
        _ensure_pointlist(value)
        self._pointlist = list(value)
        self.costume._update_draw_shape()
        self.costume.set_dirty("draw_shapes", self.costume.RELOAD_ACTUAL_IMAGE)


class Triangle(Polygon):
    """A triangle shape defined by three corner points.

    Args:
        p1: First corner as `(x, y)`.
        p2: Second corner as `(x, y)`.
        p3: Third corner as `(x, y)`.

    Examples:
        ::

            triangle = Triangle((100, 50), (50, 150), (150, 150))
            triangle.fill_color = (255, 165, 0)
    """

    def __init__(self, p1: Tuple, p2: Tuple, p3: Tuple, *args, **kwargs):
        _ensure_point(p1, "p1")
        _ensure_point(p2, "p2")
        _ensure_point(p3, "p3")
        pointlist = [p1, p2, p3]
        super().__init__(pointlist)
