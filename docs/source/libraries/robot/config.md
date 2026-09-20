# Configuration Dataclasses

All robot worlds and robots are configured through immutable dataclasses.
You can either use the built-in named configs or build your own by constructing
these dataclasses directly.

## RobotConfig

Controls the robot's appearance and starting direction.

| Field | Default | Description |
|---|---|---|
| `name` | none | Identifier string |
| `costume` | `(214, 37, 37, 255)` | RGBA color of the robot body |
| `direction` | `90` | Initial heading in degrees (90 = right) |

**Built-in configs:** `"standard"` (red), `"blue"` (blue).

## WorldConfig

Controls the world layout, objects, allowed abilities, and win condition.

| Field | Default | Description |
|---|---|---|
| `name` | none | Identifier string |
| `columns` | `10` | Grid width |
| `rows` | `10` | Grid height |
| `tile_size` | `40` | Pixel size of each tile |
| `background` | light green | Background fill color |
| `objects` | `()` | Tuple of `ObjectConfig` for pre-placed actors |
| `target` | empty | `TargetConfig` win condition |
| `robot_abilities` | `{"step", "turn_left", "turn_right"}` | Abilities the robot exposes |
| `start_position` | `None` | Default robot start tile, used by `load()` when no explicit `position` is given |

## ObjectConfig

Describes a single pre-placed object.

| Field | Description |
|---|---|
| `kind` | `"leaf"`, `"tree"`, or `"mushroom"` |
| `position` | `(column, row)` tile coordinate |

## TargetConfig

Describes the win condition checked by `RobotWorld.is_solved()`.
All fields are optional; only non-`None` fields are checked.

| Field | Description |
|---|---|
| `robot_position` | Required final tile position |
| `robot_direction` | Required final heading |
| `robot_steps` | Exact number of steps the robot must have taken |
| `objects` | Required set of remaining `ObjectConfig` entries |

## Custom world example

```python
from miniworlds_robot import RobotWorld, load_robot
from miniworlds_robot.config import WorldConfig, ObjectConfig, TargetConfig

config = WorldConfig(
    name="my_task",
    columns=5,
    rows=5,
    start_position=(0, 2),
    objects=(ObjectConfig("leaf", (3, 2)),),
    target=TargetConfig(robot_position=(4, 2), objects=()),
    robot_abilities=frozenset({"step", "on_leaf", "remove_leaf"}),
)
world = RobotWorld(config)
robot = load_robot(world=world)
```

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_robot.config.RobotConfig
   :members:

.. autoclass:: miniworlds_robot.config.WorldConfig
   :members:

.. autoclass:: miniworlds_robot.config.ObjectConfig
   :members:

.. autoclass:: miniworlds_robot.config.TargetConfig
   :members:
```
