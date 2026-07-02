# miniworlds-robot

**miniworlds-robot** provides a grid-based robot world for teaching algorithmic thinking.
Students write code that moves a robot through a `TiledWorld`, collecting leaves and navigating obstacles,
without having access to the full miniworlds API surface.

The library enforces an intentionally limited robot *ability set* that you configure per world,
so each exercise reveals exactly the language features needed for that lesson.

## Installation

```bash
pip install miniworlds-robot
```

## Quick start

```python
from miniworlds_robot import task

world, robot = task("sequence_path")   # built-in task config
robot.step()
robot.step()
robot.turn_right()
robot.step()
world.run()
```

Or build your own world from scratch:

```python
from miniworlds_robot import RobotWorld, load_robot, WorldConfig

world = RobotWorld()       # default 10 x 10 grid
robot = load_robot(world=world, position=(0, 0))
robot.step()
world.run()
```

## Built-in tasks

| Name | Description |
|---|---|
| `"basic"` | Empty 10 x 10 grid |
| `"sequence_path"` | Reach a target position in a straight line |
| `"variables_path"` | Path requiring a direction change (introduces variables) |
| `"function_path"` | Repeated movement (introduces functions) |
| `"loop_square"` | Walk around a square (introduces loops) |
| `"leaf_line"` | Collect leaves in a row (introduces `on_leaf` / `remove_leaf`) |
| `"obstacle_garden"` | Navigate around trees and mushrooms |
| `"with_position"` | Exposes `robot.position` for coordinate-based tasks |

## API Reference

```{toctree}
---
maxdepth: 1
---
robot
robot_world
world_objects
loader
config
```
