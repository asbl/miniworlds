# Loader Functions

These factory functions are the primary entry point for creating robot worlds.

## `task(name, robot="standard")`

The simplest way to start a lesson task. Returns `(world, robot)`.

```python
from miniworlds_robot import task

world, robot = task("leaf_line")
robot.step()
robot.step()
robot.on_leaf()      # True
robot.remove_leaf()
world.run()
```

## `load_world(config="basic", **overrides)`

Create a `RobotWorld` from a named built-in config or a `WorldConfig` instance.
Objects listed in the config are placed automatically.

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

`Loader` is a convenience class that bundles both factory functions as static methods.
Useful if you want to pass the factory as an object.

## API Reference

```{eval-rst}
.. autofunction:: miniworlds_robot.tasks.task

.. autofunction:: miniworlds_robot.loader.load_world

.. autofunction:: miniworlds_robot.loader.load_robot

.. autoclass:: miniworlds_robot.loader.Loader
   :members:
   :no-private-members:
```
