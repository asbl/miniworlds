import turtle as std_turtle

import miniworlds_turtle as turtle


def test_common_public_turtle_names_are_exported():
    names = {
        "Turtle",
        "RawTurtle",
        "Pen",
        "RawPen",
        "Screen",
        "TurtleScreen",
        "Vec2D",
        "Shape",
        "TurtleGraphicsError",
        "forward",
        "backward",
        "left",
        "right",
        "goto",
        "circle",
        "dot",
        "write",
        "penup",
        "pendown",
        "pencolor",
        "fillcolor",
        "begin_fill",
        "end_fill",
        "stamp",
        "undo",
        "bgcolor",
        "screensize",
        "setworldcoordinates",
        "onkey",
        "ontimer",
        "done",
    }

    missing = names - set(dir(turtle))

    assert missing == set()


def test_no_missing_callable_names_from_standard_turtle_module():
    ignored = {
        "deepcopy",
        "contextmanager",
    }
    standard_callables = {
        name
        for name in dir(std_turtle)
        if not name.startswith("_") and callable(getattr(std_turtle, name))
    }
    implemented = set(dir(turtle))

    assert standard_callables - ignored - implemented == set()
