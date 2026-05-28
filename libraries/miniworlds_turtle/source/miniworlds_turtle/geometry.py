from __future__ import annotations

import math


class Vec2D(tuple):
    def __new__(cls, x, y):
        return tuple.__new__(cls, (float(x), float(y)))

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    def __add__(self, other):
        return Vec2D(self.x + other[0], self.y + other[1])

    def __sub__(self, other):
        return Vec2D(self.x - other[0], self.y - other[1])

    def __mul__(self, factor):
        return Vec2D(self.x * factor, self.y * factor)

    __rmul__ = __mul__

    def rotate(self, angle):
        radians = math.radians(angle)
        cos_a = math.cos(radians)
        sin_a = math.sin(radians)
        return Vec2D(self.x * cos_a - self.y * sin_a, self.x * sin_a + self.y * cos_a)

    def __abs__(self):
        return math.hypot(self.x, self.y)


def as_xy(x, y=None):
    if y is None:
        if isinstance(x, Vec2D):
            return x.x, x.y
        if isinstance(x, tuple) and len(x) == 2:
            return float(x[0]), float(x[1])
        obj_x = getattr(x, "x", None)
        obj_y = getattr(x, "y", None)
        if obj_x is not None and obj_y is not None:
            return float(obj_x), float(obj_y)
        raise TypeError("expected x/y or a two-component position")
    return float(x), float(y)
