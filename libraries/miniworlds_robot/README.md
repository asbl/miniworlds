# miniworlds-robot

`miniworlds-robot` is a small extension library for miniworlds. It provides
robot worlds with a restricted, configuration-driven API for learners.

The library builds everything from miniworlds worlds and actors. It does not
load pygame sprites or expose pygame primitives.

The package is intentionally kept separate from the miniworlds core package so
it can later live in its own repository and be published on PyPI.

## Example

```python
from miniworlds_robot import Loader

world = Loader.load_world("basic")
robot = Loader.load_robot("standard", world, position=(1, 1))

robot.step()
robot.turn_left()

world.run()
```
