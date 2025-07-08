# Concept: Imports

With `import`, you can include libraries and use the classes and functions they provide.
There are different ways to import libraries in Python.

---

## Different Types of Imports

In Python, you can import libraries in several ways.
All of the following lines are valid:

```python
import miniworlds
from miniworlds import *
import miniworlds
```

In the first form `import miniworlds`, you need to prefix everything with `miniworlds.` — e.g., `miniworlds.World()`.

Alternatively, you can write `from miniworlds import *`, which allows you to omit the `miniworlds.` prefix and write `World()` directly.

Here’s how a simple program would look using `import miniworlds`:

```python
import miniworlds

world = miniworlds.TiledWorld()
world.add_background("images/soccer_green.jpg")
world.columns = 20
world.rows = 8
world.tile_size = 40

world.run()
```

---

## Explicit vs. Implicit Imports

Using `miniworlds.object` may seem more verbose, but it is the **preferred** method in Python.

Why? Because it makes your code **more readable** — it’s immediately clear which library a function or class comes from.

For example, if you define your own class named `TiledWorld`, it would clash with the imported name.
By using the prefix (`miniworlds.TiledWorld`), you avoid confusion.

This follows the Python Zen principle:

> **Explicit is better than implicit.**

---

## Aliases

The third option is a **compromise** between the two styles.

If you find `miniworlds` too long, you can use an alias — for example, `mwm`:

```python
import miniworlds as mwm

world = mwm.TiledWorld()
world.add_background("images/soccer_green.jpg")
world.columns = 20
world.rows = 8
world.tile_size = 40

world.run()
```

---

## Notes for Teachers

Both styles of import are used throughout these tutorials.
As a teacher, you may wish to **standardize** one approach for beginners.

For students who are new to Python, it might be easier to **avoid advanced import styles** (like `from ... import *`) at first.
