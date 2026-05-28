from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy

from .geometry import Vec2D
from .screen import Canvas, Screen, ScrolledCanvas, Shape, TurtleGraphicsError, TurtleScreen, TurtleScreenBase
from .turtle import Pen, RawPen, RawTurtle, TNavigator, TPen, Tbuffer, Turtle

_screen = None
_pen = None


def _get_screen():
    global _screen
    if _screen is None:
        _screen = Screen()
    return _screen


def getturtle():
    global _pen
    if _pen is None:
        _pen = Turtle(_get_screen())
    return _pen


getpen = getturtle


def getscreen():
    return _get_screen()


def _delegate(name):
    def wrapper(*args, **kwargs):
        return getattr(getturtle(), name)(*args, **kwargs)
    wrapper.__name__ = name
    return wrapper


def _screen_delegate(name):
    def wrapper(*args, **kwargs):
        return getattr(_get_screen(), name)(*args, **kwargs)
    wrapper.__name__ = name
    return wrapper


forward = fd = _delegate("forward")
back = backward = bk = _delegate("back")
right = rt = _delegate("right")
left = lt = _delegate("left")
goto = setpos = setposition = _delegate("goto")
setx = _delegate("setx")
sety = _delegate("sety")
setheading = seth = _delegate("setheading")
home = _delegate("home")
circle = _delegate("circle")
dot = _delegate("dot")
write = _delegate("write")
position = pos = _delegate("position")
xcor = _delegate("xcor")
ycor = _delegate("ycor")
heading = _delegate("heading")
towards = _delegate("towards")
distance = _delegate("distance")
penup = pu = up = _delegate("penup")
pendown = pd = down = _delegate("pendown")
isdown = _delegate("isdown")
pensize = width = _delegate("pensize")
pencolor = _delegate("pencolor")
fillcolor = _delegate("fillcolor")
color = _delegate("color")
pen = _delegate("pen")
begin_fill = _delegate("begin_fill")
end_fill = _delegate("end_fill")
filling = _delegate("filling")
begin_poly = _delegate("begin_poly")
end_poly = _delegate("end_poly")
get_poly = _delegate("get_poly")
fill = _delegate("fill")
poly = _delegate("poly")
clear = _delegate("clear")
reset = _delegate("reset")
stamp = _delegate("stamp")
clearstamp = _delegate("clearstamp")
clearstamps = _delegate("clearstamps")
undo = _delegate("undo")
setundobuffer = _delegate("setundobuffer")
undobufferentries = _delegate("undobufferentries")
speed = _delegate("speed")
hideturtle = ht = _delegate("hideturtle")
showturtle = st = _delegate("showturtle")
isvisible = _delegate("isvisible")
shape = _delegate("shape")
shapesize = turtlesize = _delegate("shapesize")
resizemode = _delegate("resizemode")
tilt = _delegate("tilt")
tiltangle = _delegate("tiltangle")
shapetransform = _delegate("shapetransform")
shearfactor = _delegate("shearfactor")
clone = _delegate("clone")
onclick = _delegate("onclick")
ondrag = _delegate("ondrag")
onrelease = _delegate("onrelease")
teleport = _delegate("teleport")
degrees = _delegate("degrees")
radians = _delegate("radians")
get_shapepoly = _delegate("get_shapepoly")

bgcolor = _screen_delegate("bgcolor")
bgpic = _screen_delegate("bgpic")
bye = _screen_delegate("bye")
clearscreen = _screen_delegate("clearscreen")
resetscreen = _screen_delegate("resetscreen")
colormode = _screen_delegate("colormode")
delay = _screen_delegate("delay")
done = _screen_delegate("done")
exitonclick = _screen_delegate("exitonclick")
getcanvas = _screen_delegate("getcanvas")
getshapes = _screen_delegate("getshapes")
listen = _screen_delegate("listen")
mainloop = _screen_delegate("mainloop")
mode = _screen_delegate("mode")
no_animation = _screen_delegate("no_animation")
numinput = _screen_delegate("numinput")
onkey = _screen_delegate("onkey")
onkeypress = _screen_delegate("onkeypress")
onkeyrelease = _screen_delegate("onkeyrelease")
onscreenclick = _screen_delegate("onscreenclick")
ontimer = _screen_delegate("ontimer")
register_shape = addshape = _screen_delegate("addshape")
save = _screen_delegate("save")
screensize = _screen_delegate("screensize")
setup = _screen_delegate("setup")
setworldcoordinates = _screen_delegate("setworldcoordinates")
textinput = _screen_delegate("textinput")
title = _screen_delegate("title")
tracer = _screen_delegate("tracer")
turtles = _screen_delegate("turtles")
update = _screen_delegate("update")
window_height = _screen_delegate("window_height")
window_width = _screen_delegate("window_width")


@contextmanager
def no_animation():
    old = tracer()
    tracer(0, 0)
    try:
        yield
    finally:
        tracer(old)


def isfile(path):
    import os
    return os.path.isfile(path)


def readconfig(cfgdict):
    return cfgdict


def config_dict(filename=None):
    del filename
    return {}


def read_docstrings(lang):
    del lang
    return {}


def write_docstringdict(filename="turtle_docstringdict"):
    del filename


def getmethparlist(ob):
    import inspect
    return inspect.signature(ob)


class Terminator(Exception):
    pass


Path = list
split = str.split
join = "".join

__all__ = [name for name in globals() if not name.startswith("_")]
