import math

from miniworlds_turtle import Screen, Turtle


def test_turtle_moves_in_centered_coordinate_system():
    screen = Screen(width=200, height=100)
    turtle = Turtle(screen)

    turtle.forward(30)
    turtle.left(90)
    turtle.forward(20)

    assert turtle.position() == (30, 20)
    assert turtle.heading() == 90
    assert len(screen.world.background.drawing_commands) == 2


def test_penup_moves_without_background_command():
    screen = Screen(width=200, height=100)
    turtle = Turtle(screen)

    turtle.penup()
    turtle.forward(40)

    assert turtle.position() == (40, 0)
    assert screen.world.background.drawing_commands == ()


def test_color_fill_and_dot_are_recorded_on_background():
    screen = Screen(width=200, height=100)
    turtle = Turtle(screen)

    turtle.color("red", "blue")
    turtle.begin_fill()
    for _ in range(3):
        turtle.forward(20)
        turtle.left(120)
    turtle.end_fill()
    turtle.dot(8, "green")

    kinds = [command["kind"] for command in screen.world.background.drawing_commands]
    assert "polygon" in kinds
    assert kinds[-1] == "dot"


def test_undo_restores_position_and_background_commands():
    screen = Screen(width=200, height=100)
    turtle = Turtle(screen)

    turtle.forward(10)
    turtle.forward(20)
    assert math.isclose(turtle.xcor(), 30)
    assert len(screen.world.background.drawing_commands) == 2

    turtle.undo()

    assert math.isclose(turtle.xcor(), 10)
    assert len(screen.world.background.drawing_commands) == 1


def test_clear_removes_only_this_turtles_background_commands():
    screen = Screen(width=200, height=100)
    first = Turtle(screen)
    second = Turtle(screen)

    first.forward(10)
    second.forward(20)

    first.clear()

    assert len(screen.world.background.drawing_commands) == 1
    assert screen.world.background.drawing_commands[0]["owner"] == second._owner
