# World > PhysicsWorld

`PhysicsWorld` extends the regular world with a `pymunk` space. Use it when actors should fall, collide, bounce, or be connected with joints.

Install `miniworlds_physics` alongside `miniworlds` and import it from the separate package:

```python
from miniworlds import Circle, Rectangle
from miniworlds_physics import PhysicsWorld

world = PhysicsWorld(400, 300)
world.gravity = (0, 500)

floor = Rectangle((0, 260), 400, 40)
floor.physics.simulation = "static"

ball = Circle((80, 40), 20)
ball.physics.elasticity = 0.4
ball.physics.shape_type = "circle"

world.run()
```

## Typical Physics Settings

- `world.gravity` controls global acceleration.
- `world.damping` slows bodies over time.
- `actor.physics.simulation` chooses how an actor participates: `simulated`, `manual`, `static`, or `None`.
- `actor.physics` also exposes `density`, `friction`, `elasticity`, `shape_type`, and velocity helpers.

## Collision Hooks

Physics worlds support dedicated actor callbacks such as `on_touching_circle` and `on_separation_from_circle`. These receive the other actor and contact information from the physics engine.

See also the [Flappy Bird tutorial](../patterns/flappy_physics.md) for a larger example.

```{eval-rst}
.. autoclass:: miniworlds_physics.physics_world.PhysicsWorld
	:members:

	.. autoclasstoc::
```
