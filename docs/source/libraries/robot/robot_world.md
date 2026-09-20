# RobotWorld

`RobotWorld` is a `TiledWorld` subclass that hosts the robot simulation.
It reads its dimensions, background color, pre-placed objects, and allowed robot
abilities from a `WorldConfig` dataclass.

Use `load(...)`, `load_world(...)`, or `task(...)` to create a pre-configured
instance rather than constructing `RobotWorld` directly.

## Key methods

| Method | Description |
|---|---|
| `is_blocked(position)` | Return `True` if the tile is outside the grid or occupied by a blocking object. |
| `is_solved()` | Return `True` when the world state matches the task's `TargetConfig`. |
| `add_object(actor_cls, position)` | Place a robot world object (e.g. `Tree`, `Leaf`) on the grid. |
| `robot_abilities` | `frozenset[str]`: abilities the current task permits. |

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_robot.world.RobotWorld
   :members:
   :no-private-members:
```
