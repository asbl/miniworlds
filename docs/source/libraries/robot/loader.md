# Loader Functions

These factory functions are the primary entry point for creating robot worlds.

## `load(config="basic", robot="standard", *, position=None, **overrides)`

The simplest way to create a world and its robot in one call.
Returns `(world, robot)`. The robot is placed at `position` if given, otherwise
at the world's configured `start_position` (falling back to `(0, 0)`).

```python
from miniworlds_robot import load

world, robot = load("leaf_line")
robot.step()
robot.step()
robot.on_leaf()      # True
robot.remove_leaf()
world.run()
```

Worlds can also be loaded from JSON URLs, including GitHub `blob` links:

```python
from miniworlds_robot import load

world, robot = load(
    "https://github.com/asbl/miniworlds-robot-worlds/blob/main/worlds/01-sequences/sequence_01_straight_line.json"
)
```

## `task(name, robot="standard", *, position=None, debug=False)`

Convenience wrapper around `load` for built-in lesson tasks.
Returns `(world, robot)`.

## `load_world(config="basic", **overrides)`

Create a `RobotWorld` from a named built-in config or a `WorldConfig` instance.
Objects listed in the config are placed automatically. No robot is created.

```python
from miniworlds_robot import load_world

world = load_world("obstacle_garden")
world.run()
```

## `load_robot(config="standard", world=None, *, position=(0, 0))`

Create a `Robot` and place it on the given world.
If `world` is `None`, a basic world is created automatically.

```python
from miniworlds_robot import load_world, load_robot

world = load_world("loop_square")
robot = load_robot(world=world, position=(1, 1))
```

## `Loader` class

`Loader` is a convenience class that bundles the factory functions as static methods.
Useful if you want to pass the factory as an object.

## API Reference

```{eval-rst}
.. autofunction:: miniworlds_robot.loader.load

.. autofunction:: miniworlds_robot.tasks.task

.. autofunction:: miniworlds_robot.loader.load_world

.. autofunction:: miniworlds_robot.loader.load_robot

.. autoclass:: miniworlds_robot.loader.Loader
   :members:
   :no-private-members:
```
