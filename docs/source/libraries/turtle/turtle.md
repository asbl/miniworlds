# Turtle

`Turtle` (also `RawTurtle`, `Pen`, `RawPen`) is the main drawing actor.
All turtle-module functions delegate to the global default `Turtle` instance.

## Movement

| Method / Alias | Description |
|---|---|
| `forward(distance)` / `fd` | Move forward by `distance` pixels. |
| `back(distance)` / `backward` / `bk` | Move backward by `distance` pixels. |
| `right(angle)` / `rt` | Turn right by `angle` degrees. |
| `left(angle)` / `lt` | Turn left by `angle` degrees. |
| `goto(x, y)` / `setpos` / `setposition` | Move to absolute position `(x, y)`. |
| `setx(x)` | Set the x coordinate; y stays unchanged. |
| `sety(y)` | Set the y coordinate; x stays unchanged. |
| `setheading(angle)` / `seth` | Set the heading to `angle` degrees. |
| `home()` | Move to origin `(0, 0)` and set heading to 0 degrees. |
| `circle(radius, extent, steps)` | Draw a circle of given radius. |
| `dot(size, color)` | Draw a dot at the current position. |
| `teleport(x, y)` | Move to `(x, y)` without drawing. |

## Pen control

| Method / Alias | Description |
|---|---|
| `penup()` / `pu` / `up` | Lift the pen; movement does not draw. |
| `pendown()` / `pd` / `down` | Lower the pen; movement draws. |
| `isdown()` | Return `True` when the pen is down. |
| `pensize(width)` / `width` | Set line width. |
| `pencolor(*args)` | Set pen color. |
| `fillcolor(*args)` | Set fill color. |
| `color(*args)` | Set pen and fill color at once. |
| `pen(**kwargs)` | Get or set multiple pen attributes at once. |

## Fill

| Method | Description |
|---|---|
| `begin_fill()` | Mark the start of a region to fill. |
| `end_fill()` | Close and fill the region. |
| `filling()` | Return `True` when inside a `begin_fill` / `end_fill` block. |

## State queries

| Method | Description |
|---|---|
| `position()` / `pos` | Return current `Vec2D` position. |
| `xcor()` | Return x coordinate. |
| `ycor()` | Return y coordinate. |
| `heading()` | Return current heading in degrees. |
| `towards(x, y)` | Return angle towards point `(x, y)`. |
| `distance(x, y)` | Return distance to point `(x, y)`. |
| `isvisible()` | Return `True` when the turtle is visible. |

## Appearance

| Method | Description |
|---|---|
| `shape(name)` | Set the turtle shape. |
| `shapesize(stretch_wid, stretch_len, outline)` / `turtlesize` | Scale the turtle shape. |
| `hideturtle()` / `ht` | Hide the turtle icon. |
| `showturtle()` / `st` | Show the turtle icon. |
| `tilt(angle)` | Rotate the turtle shape by `angle` without changing the heading. |
| `tiltangle(angle)` | Set the tilt angle of the turtle shape. |
| `speed(speed)` | Set drawing speed (0-10, or named string). |

## Stamps and undo

| Method | Description |
|---|---|
| `stamp()` | Stamp the turtle shape on the canvas; return stamp id. |
| `clearstamp(stampid)` | Remove a specific stamp. |
| `clearstamps(n)` | Remove first `n` stamps (negative = last `n`). |
| `undo()` | Undo the last action. |
| `setundobuffer(size)` | Set the undo buffer size. |
| `undobufferentries()` | Return the number of actions in the undo buffer. |

## Mouse and click events

| Method | Description |
|---|---|
| `onclick(fun, btn, add)` | Bind a function to a mouse-click on the turtle. |
| `ondrag(fun, btn, add)` | Bind a function to dragging the turtle. |
| `onrelease(fun, btn, add)` | Bind a function to releasing the mouse button on the turtle. |

## Polygon

| Method | Description |
|---|---|
| `begin_poly()` | Start recording polygon vertices. |
| `end_poly()` | Stop recording. |
| `get_poly()` | Return the recorded polygon. |

## Module-level functions

All `Turtle` methods are also available as module-level functions that
delegate to the global default turtle:

```python
import miniworlds_turtle as turtle

turtle.forward(100)
turtle.pencolor("red")
turtle.circle(50)
```

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_turtle.turtle.Turtle
   :members:
   :no-private-members:
```
