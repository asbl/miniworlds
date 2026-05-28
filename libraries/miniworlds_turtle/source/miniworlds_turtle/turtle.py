from __future__ import annotations

import math
from copy import deepcopy

from miniworlds import Actor

from .colors import color_from_args, normalize_color
from .geometry import Vec2D, as_xy
from .screen import Screen


class TNavigator:
    pass


class TPen:
    pass


class Tbuffer(list):
    pass


class RawTurtle(TNavigator, TPen):
    _counter = 0

    def __init__(self, canvas: Screen | None = None, shape="classic", undobuffersize=1000, visible=True):
        RawTurtle._counter += 1
        self._owner = f"turtle-{RawTurtle._counter}"
        self.screen = canvas or Screen()
        self.screen._register_turtle(self)
        self._position = Vec2D(0, 0)
        self._heading = 0.0
        self._degrees = 360.0
        self._pendown = True
        self._pensize = 1
        self._pencolor = (0, 0, 0, 255)
        self._fillcolor = (0, 0, 0, 255)
        self._is_filling = False
        self._fill_points = []
        self._poly_points = None
        self._visible = visible
        self._shape = shape
        self._speed = 3
        self._stamps = {}
        self._stamp_counter = 0
        self._undo = []
        self._undobuffersize = undobuffersize
        self._actor = Actor(self.screen._to_world(0, 0), world=self.screen.world)
        self._actor.size = (12, 12)
        self._actor.add_costume((40, 120, 200, 255))
        self._sync_actor()

    def _snapshot(self):
        if self._undobuffersize == 0:
            return
        self._undo.append((self._position, self._heading, deepcopy(self.screen.world.background.drawing_commands)))
        if self._undobuffersize is not None and len(self._undo) > self._undobuffersize:
            self._undo.pop(0)

    def _sync_actor(self):
        self._actor.position = self.screen._to_world(self._position.x, self._position.y)
        self._actor.direction = self._heading

    def _line_to(self, new_position):
        old_world = self.screen._to_world(self._position.x, self._position.y)
        new_world = self.screen._to_world(new_position.x, new_position.y)
        if self._pendown:
            self.screen.world.background.draw_line(old_world, new_world, self._pencolor, self._pensize, owner=self._owner)
        if self._is_filling:
            self._fill_points.append(new_world)
        if self._poly_points is not None:
            self._poly_points.append(new_world)
        self._position = new_position
        self._sync_actor()

    def forward(self, distance):
        self._snapshot()
        radians = math.radians(self._heading)
        new_position = Vec2D(
            self._position.x + math.cos(radians) * distance,
            self._position.y + math.sin(radians) * distance,
        )
        self._line_to(new_position)

    fd = forward

    def back(self, distance):
        return self.forward(-distance)

    backward = back
    bk = back

    def right(self, angle):
        self._snapshot()
        self._heading -= angle
        self._sync_actor()

    rt = right

    def left(self, angle):
        self._snapshot()
        self._heading += angle
        self._sync_actor()

    lt = left

    def goto(self, x, y=None):
        self._snapshot()
        self._line_to(Vec2D(*as_xy(x, y)))

    setpos = goto
    setposition = goto

    def setx(self, x):
        self.goto(x, self._position.y)

    def sety(self, y):
        self.goto(self._position.x, y)

    def home(self):
        self.goto(0, 0)
        self.setheading(0)

    def setheading(self, to_angle):
        self._snapshot()
        self._heading = float(to_angle)
        self._sync_actor()

    seth = setheading

    def position(self):
        return Vec2D(self._position.x, self._position.y)

    pos = position

    def xcor(self):
        return self._position.x

    def ycor(self):
        return self._position.y

    def heading(self):
        return self._heading % self._degrees

    def towards(self, x, y=None):
        tx, ty = as_xy(x, y)
        return math.degrees(math.atan2(ty - self._position.y, tx - self._position.x)) % 360

    def distance(self, x, y=None):
        tx, ty = as_xy(x, y)
        return math.hypot(tx - self._position.x, ty - self._position.y)

    def penup(self):
        self._pendown = False

    pu = up = penup

    def pendown(self):
        self._pendown = True

    pd = down = pendown

    def isdown(self):
        return self._pendown

    def pensize(self, width=None):
        if width is None:
            return self._pensize
        self._pensize = int(width)

    width = pensize

    def pencolor(self, *args):
        if not args:
            return self._pencolor
        self._pencolor = color_from_args(args, self._pencolor, self.screen.colormode())

    def fillcolor(self, *args):
        if not args:
            return self._fillcolor
        self._fillcolor = color_from_args(args, self._fillcolor, self.screen.colormode())

    def color(self, *args):
        if not args:
            return self._pencolor, self._fillcolor
        if len(args) == 1:
            color = normalize_color(args[0], self.screen.colormode())
            self._pencolor = color
            self._fillcolor = color
        elif len(args) == 2:
            self._pencolor = normalize_color(args[0], self.screen.colormode())
            self._fillcolor = normalize_color(args[1], self.screen.colormode())
        else:
            color = normalize_color(tuple(args), self.screen.colormode())
            self._pencolor = color
            self._fillcolor = color

    def pen(self, pen=None, **pendict):
        if pen is None and not pendict:
            return {
                "shown": self._visible,
                "pendown": self._pendown,
                "pencolor": self._pencolor,
                "fillcolor": self._fillcolor,
                "pensize": self._pensize,
                "speed": self._speed,
            }
        values = {}
        if pen:
            values.update(pen)
        values.update(pendict)
        if "pendown" in values:
            self._pendown = bool(values["pendown"])
        if "pencolor" in values:
            self.pencolor(values["pencolor"])
        if "fillcolor" in values:
            self.fillcolor(values["fillcolor"])
        if "pensize" in values:
            self.pensize(values["pensize"])
        if "speed" in values:
            self.speed(values["speed"])

    def begin_fill(self):
        self._is_filling = True
        self._fill_points = [self.screen._to_world(self._position.x, self._position.y)]

    def end_fill(self):
        if self._is_filling and len(self._fill_points) >= 3:
            self._snapshot()
            self.screen.world.background.draw_polygon(
                self._fill_points, outline=self._pencolor, fill=self._fillcolor, width=self._pensize, owner=self._owner
            )
        self._is_filling = False
        self._fill_points = []

    def filling(self):
        return self._is_filling

    def begin_poly(self):
        self._poly_points = [self.screen._to_world(self._position.x, self._position.y)]

    def end_poly(self):
        if self._poly_points is None:
            self._poly_points = []

    def get_poly(self):
        return tuple(self._poly_points or [])

    def circle(self, radius, extent=None, steps=None):
        extent = 360 if extent is None else extent
        steps = steps or max(12, int(abs(extent) / 6))
        start_heading = self._heading
        step_length = 2 * math.pi * abs(radius) * abs(extent) / 360 / steps
        step_angle = extent / steps
        for _ in range(steps):
            self.forward(step_length)
            self.left(step_angle if radius >= 0 else -step_angle)
        self._heading = start_heading + extent
        self._sync_actor()

    def dot(self, size=None, *color):
        size = self._pensize + 4 if size is None else size
        dot_color = self._pencolor if not color else color_from_args(color, self._pencolor, self.screen.colormode())
        self._snapshot()
        self.screen.world.background.draw_dot(self.screen._to_world(self._position.x, self._position.y), size, dot_color, owner=self._owner)

    def write(self, arg, move=False, align="left", font=("Arial", 8, "normal")):
        self._snapshot()
        self.screen.world.background.draw_text(
            self.screen._to_world(self._position.x, self._position.y), str(arg), self._pencolor, font, align, owner=self._owner
        )
        if move:
            self.forward(len(str(arg)) * font[1] * 0.6)

    def clear(self):
        self.screen.world.background.clear_drawing_layer(owner=self._owner)
        for stamp in list(self._stamps.values()):
            stamp.remove()
        self._stamps = {}

    def reset(self):
        self.clear()
        self._position = Vec2D(0, 0)
        self._heading = 0
        self._pendown = True
        self._sync_actor()

    def stamp(self):
        self._stamp_counter += 1
        stamp_actor = Actor(self.screen._to_world(self._position.x, self._position.y), world=self.screen.world)
        stamp_actor.size = self._actor.size
        stamp_actor.add_costume(self._pencolor)
        self._stamps[self._stamp_counter] = stamp_actor
        return self._stamp_counter

    def clearstamp(self, stampid):
        stamp = self._stamps.pop(stampid, None)
        if stamp:
            stamp.remove()

    def clearstamps(self, n=None):
        ids = list(self._stamps.keys())
        if n is not None:
            ids = ids[:n] if n >= 0 else ids[n:]
        for stampid in ids:
            self.clearstamp(stampid)

    def undo(self):
        if not self._undo:
            return
        self._position, self._heading, commands = self._undo.pop()
        self.screen.world.background.set_drawing_commands(commands)
        self._sync_actor()

    def setundobuffer(self, size):
        self._undobuffersize = size
        self._undo = []

    def undobufferentries(self):
        return len(self._undo)

    def speed(self, speed=None):
        if speed is None:
            return self._speed
        self._speed = speed

    def hideturtle(self):
        self._visible = False
        self._actor.is_visible = False

    ht = hideturtle

    def showturtle(self):
        self._visible = True
        self._actor.is_visible = True

    st = showturtle

    def isvisible(self):
        return self._visible

    def shape(self, name=None):
        if name is None:
            return self._shape
        self._shape = name

    def shapesize(self, stretch_wid=None, stretch_len=None, outline=None):
        del outline
        if stretch_wid is None and stretch_len is None:
            return (1, 1, 1)
        self._actor.size = (12 * (stretch_len or 1), 12 * (stretch_wid or 1))

    turtlesize = shapesize

    def resizemode(self, rmode=None):
        if rmode is None:
            return "auto"

    def tilt(self, angle):
        self._heading += angle

    def tiltangle(self, angle=None):
        if angle is None:
            return self._heading
        self._heading = angle

    def shapetransform(self, t11=None, t12=None, t21=None, t22=None):
        if t11 is None:
            return (1.0, 0.0, 0.0, 1.0)
        del t11, t12, t21, t22

    def shearfactor(self, shear=None):
        return 0.0 if shear is None else None

    def clone(self):
        clone = type(self)(self.screen, self._shape, self._undobuffersize, self._visible)
        clone._position = Vec2D(self._position.x, self._position.y)
        clone._heading = self._heading
        clone._pencolor = self._pencolor
        clone._fillcolor = self._fillcolor
        clone._pensize = self._pensize
        clone._sync_actor()
        return clone

    def getturtle(self):
        return self

    getpen = getturtle

    def getscreen(self):
        return self.screen

    def onclick(self, fun, btn=1, add=None):
        del fun, btn, add

    def ondrag(self, fun, btn=1, add=None):
        del fun, btn, add

    def onrelease(self, fun, btn=1, add=None):
        del fun, btn, add

    def teleport(self, x=None, y=None, *, fill_gap=False):
        del fill_gap
        if x is None:
            x = self._position.x
        if y is None:
            y = self._position.y
        was_down = self._pendown
        self._pendown = False
        self.goto(x, y)
        self._pendown = was_down

    def degrees(self, fullcircle=360.0):
        self._degrees = float(fullcircle)

    def radians(self):
        self._degrees = 2 * math.pi

    def fill(self):
        self.begin_fill()

    def poly(self):
        self.begin_poly()

    def get_shapepoly(self):
        return ()


class Turtle(RawTurtle):
    pass


class RawPen(RawTurtle):
    pass


class Pen(Turtle):
    pass
