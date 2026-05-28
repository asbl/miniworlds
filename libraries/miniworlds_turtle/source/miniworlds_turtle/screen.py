from __future__ import annotations

from typing import Callable

from miniworlds import World

from .colors import normalize_color


class TurtleGraphicsError(Exception):
    pass


class Shape:
    def __init__(self, type_, data=None):
        self._type = type_
        self._data = data


class TurtleScreenBase:
    pass


class TurtleScreen(TurtleScreenBase):
    def __init__(self, world: World | None = None, width: int = 400, height: int = 400):
        self.world = world or World(width, height)
        self._width = width
        self._height = height
        self._colormode = 255
        self._mode = "standard"
        self._title = ""
        self._tracer = 1
        self._delay = 10
        self._turtles = []
        self._shapes = {"arrow": None, "turtle": None, "circle": None, "square": None, "triangle": None, "classic": None}
        self._world_coordinates = None

    def _to_world(self, x: float, y: float):
        if self._world_coordinates:
            llx, lly, urx, ury = self._world_coordinates
            wx = (x - llx) / (urx - llx) * self.world.width
            wy = self.world.height - ((y - lly) / (ury - lly) * self.world.height)
            return wx, wy
        return self.world.width / 2 + x, self.world.height / 2 - y

    def _from_world(self, x: float, y: float):
        if self._world_coordinates:
            llx, lly, urx, ury = self._world_coordinates
            tx = llx + x / self.world.width * (urx - llx)
            ty = lly + (self.world.height - y) / self.world.height * (ury - lly)
            return tx, ty
        return x - self.world.width / 2, self.world.height / 2 - y

    def _register_turtle(self, turtle):
        if turtle not in self._turtles:
            self._turtles.append(turtle)

    def bgcolor(self, *args):
        if not args:
            return self.world.background.fill_color
        color = normalize_color(args[0] if len(args) == 1 else tuple(args), self._colormode)
        self.world.background.fill(color)

    def bgpic(self, picname=None):
        if picname is None:
            return "nopic"
        self.world.add_background(picname)
        return picname

    def clear(self):
        return self.clearscreen()

    def clearscreen(self):
        self.world.background.clear_drawing_layer()
        for turtle in list(self._turtles):
            turtle.reset()

    def reset(self):
        return self.resetscreen()

    def resetscreen(self):
        self.clearscreen()

    def colormode(self, cmode=None):
        if cmode is None:
            return self._colormode
        if cmode not in (1.0, 255):
            raise TurtleGraphicsError("bad color sequence: colormode must be 1.0 or 255")
        self._colormode = cmode

    def mode(self, mode=None):
        if mode is None:
            return self._mode
        if mode not in ("standard", "logo", "world"):
            raise TurtleGraphicsError(f"No turtle-graphics-mode {mode!r}")
        self._mode = mode

    def setworldcoordinates(self, llx, lly, urx, ury):
        self._world_coordinates = (float(llx), float(lly), float(urx), float(ury))
        self._mode = "world"

    def screensize(self, canvwidth=None, canvheight=None, bg=None):
        if canvwidth is None and canvheight is None and bg is None:
            return self.world.width, self.world.height
        if bg is not None:
            self.bgcolor(bg)
        return self.world.width, self.world.height

    def setup(self, width=None, height=None, startx=None, starty=None):
        del startx, starty
        if width is not None:
            self._width = int(width)
        if height is not None:
            self._height = int(height)

    def window_width(self):
        return self.world.width

    def window_height(self):
        return self.world.height

    def title(self, titlestring=None):
        if titlestring is None:
            return self._title
        self._title = str(titlestring)

    def tracer(self, n=None, delay=None):
        if n is None:
            return self._tracer
        self._tracer = n
        if delay is not None:
            self._delay = delay

    def delay(self, delay=None):
        if delay is None:
            return self._delay
        self._delay = delay

    def update(self):
        self.world.background.set_dirty("all", self.world.background.RELOAD_ACTUAL_IMAGE)

    def mainloop(self):
        return self.world.run()

    def bye(self):
        return None

    def exitonclick(self):
        return self.mainloop()

    def done(self):
        return self.mainloop()

    def listen(self, xdummy=None, ydummy=None):
        del xdummy, ydummy

    def onkey(self, fun: Callable, key):
        return self.onkeypress(fun, key)

    def onkeypress(self, fun: Callable, key=None):
        del fun, key

    def onkeyrelease(self, fun: Callable, key):
        del fun, key

    def onclick(self, fun: Callable, btn=1, add=None):
        del fun, btn, add

    def onscreenclick(self, fun: Callable, btn=1, add=None):
        return self.onclick(fun, btn, add)

    def ontimer(self, fun: Callable, t=0):
        del t
        return fun()

    def textinput(self, title, prompt):
        del title, prompt
        return None

    def numinput(self, title, prompt, default=None, minval=None, maxval=None):
        del title, prompt, minval, maxval
        return default

    def getcanvas(self):
        return self.world

    def turtles(self):
        return list(self._turtles)

    def addshape(self, name, shape=None):
        self._shapes[name] = shape

    register_shape = addshape

    def getshapes(self):
        return list(self._shapes.keys())

    def save(self, filename, *, overwrite=False):
        del filename, overwrite

    def no_animation(self):
        self.tracer(0, 0)


class Screen(TurtleScreen):
    pass


class ScrolledCanvas:
    pass


class Canvas:
    pass
