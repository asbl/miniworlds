# Screen

`Screen` (also `TurtleScreen`) manages the window and canvas for turtle graphics.
Access the global screen via `getscreen()` or use module-level screen functions.

## Setup

| Method / Alias | Description |
|---|---|
| `setup(width, height, startx, starty)` | Configure the window size and position. |
| `screensize(canvwidth, canvheight, bg)` | Set the scroll canvas size. |
| `setworldcoordinates(llx, lly, urx, ury)` | Set user-defined coordinate system. |
| `title(titlestring)` | Set the window title. |
| `mode(mode)` | Set turtle mode: `"standard"`, `"logo"`, or `"world"`. |

## Background

| Method | Description |
|---|---|
| `bgcolor(*args)` | Get or set the background color. |
| `bgpic(picname)` | Set a background image. |
| `clearscreen()` | Reset the screen to its initial state. |
| `resetscreen()` | Alias for `clearscreen()`. |

## Color and drawing

| Method | Description |
|---|---|
| `colormode(cmode)` | Set color mode to `1.0` (float 0-1) or `255` (int 0-255). |
| `tracer(n, delay)` | Control animation updates. `0` = disable animation (draw instantly). |
| `update()` | Perform a pending screen update (use after `tracer(0)`). |
| `delay(delay)` | Set drawing delay in milliseconds. |

## Event loop

| Method | Description |
|---|---|
| `done()` / `mainloop` | Start the event loop. |
| `exitonclick()` | Exit when the user clicks. |
| `bye()` | Close the window. |

## Input dialogs

| Method | Description |
|---|---|
| `numinput(title, prompt, default, minval, maxval)` | Show a numeric input dialog. |
| `textinput(title, prompt)` | Show a text input dialog. |

## Events

| Method | Description |
|---|---|
| `onscreenclick(fun, btn, add)` | Bind a function to clicking on the canvas. |
| `onkey(fun, key)` | Bind a function to a key press (key-release event). |
| `onkeypress(fun, key)` | Bind a function to a key-down event. |
| `onkeyrelease(fun, key)` | Bind a function to a key-up event. |
| `listen()` | Set focus to the canvas for key event reception. |
| `ontimer(fun, t)` | Call `fun` after `t` milliseconds. |

## Shapes and turtles

| Method | Description |
|---|---|
| `register_shape(name, shape)` / `addshape` | Add a custom shape to the shape registry. |
| `getshapes()` | Return a list of all registered shape names. |
| `turtles()` | Return a list of all turtles on the screen. |
| `getcanvas()` | Return the underlying canvas object. |

## Context manager: no_animation

```python
from miniworlds_turtle import no_animation

with no_animation():
    turtle.forward(100)
    turtle.circle(50)
# screen updates here
```

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_turtle.screen.Screen
   :members:
   :no-private-members:

.. autoclass:: miniworlds_turtle.screen.TurtleScreen
   :members:
   :no-private-members:
```
