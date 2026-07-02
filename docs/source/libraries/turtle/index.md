# miniworlds-turtle

**miniworlds-turtle** is a miniworlds-based reimplementation of Python's standard
[`turtle`](https://docs.python.org/3/library/turtle.html) module with a compatible API.

It renders turtle graphics inside a miniworlds `World` instead of Tkinter,
making it easy to combine turtle-style drawing with other miniworlds features.

## Installation

```bash
pip install miniworlds-turtle
```

## Quick start

```python
import miniworlds_turtle as turtle

turtle.forward(100)
turtle.right(90)
turtle.forward(100)
turtle.right(90)
turtle.forward(100)
turtle.right(90)
turtle.forward(100)
turtle.done()
```

Object-oriented usage:

```python
from miniworlds_turtle import Turtle, Screen

screen = Screen()
screen.setup(width=600, height=400)
t = Turtle(screen)
t.speed(3)
t.color("blue")
t.begin_fill()
for _ in range(4):
    t.forward(100)
    t.right(90)
t.end_fill()
screen.done()
```

## API Reference

```{toctree}
---
maxdepth: 1
---
turtle
screen
geometry
```
