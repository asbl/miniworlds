# miniworlds-physics

**miniworlds-physics** adds rigid-body physics to miniworlds via [pymunk](http://www.pymunk.org/).
Replace `World` with `PhysicsWorld` and every actor gains an `actor.physics` interface
for controlling mass, velocity, elasticity, friction, and collision callbacks.

## Installation

```bash
pip install miniworlds-physics
```

pymunk must also be installed:

```bash
pip install pymunk
```

## Quick start

```python
from miniworlds import Circle, Rectangle
from miniworlds_physics import PhysicsWorld

world = PhysicsWorld(400, 300)
world.gravity = (0, 500)

floor = Rectangle((0, 280), 400, 20)
floor.physics.simulation = "static"

ball = Circle((200, 20), 20)
ball.physics.simulation = "simulated"
ball.physics.elasticity = 0.7

world.run()
```

## API Reference

```{toctree}
---
maxdepth: 1
---
physics_world
actor_physics
```
