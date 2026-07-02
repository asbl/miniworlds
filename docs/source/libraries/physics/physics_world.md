# PhysicsWorld

`PhysicsWorld` is a `World` subclass backed by a [pymunk](http://www.pymunk.org/) space.
Every actor placed in this world automatically gets an `actor.physics` object
(see [ActorPhysics](actor_physics)).

## World-level properties

| Property | Default | Description |
|---|---|---|
| `gravity` | `(0, 900)` | Global gravity as `(x, y)` acceleration tuple. |
| `damping` | `0.9` | Velocity decay factor applied each second. `0.9` = lose 10 % per second. |
| `accuracy` | `1` | Number of physics sub-steps per frame. Higher values improve simulation accuracy at the cost of performance. |
| `debug` | `False` | When `True`, pymunk debug shapes are drawn on top of the world. |

## Methods

| Method | Description |
|---|---|
| `connect(actor1, actor2)` | Draw a dynamic line between two actors that updates its endpoints every frame. Returns the `Line` actor. |
| `on_new_actor(actor)` | Called automatically when an actor is added; removes non-simulated actors from the physics space. |
| `get_physics_collision_type(actor_class)` | Return a stable pymunk collision-type integer for an actor class. Used internally for collision dispatch. |

## Collision callbacks

Define methods on any actor to react to physics collisions.
The method name determines which actor class triggers it:

```python
@my_actor.register
def on_touching_Circle(self, other, collision):
    """Called when my_actor touches any Circle."""
    other.remove()

@my_actor.register
def on_separation_from_Circle(self, other, collision):
    """Called when my_actor separates from a Circle."""
    pass
```

The `other` parameter is the colliding actor; `collision` is a dict with collision metadata.

## Example: Ball with gravity

```python
from miniworlds import Circle, Rectangle, Line
from miniworlds_physics import PhysicsWorld

world = PhysicsWorld(400, 400)
world.gravity = (0, 900)
world.damping = 0.99

floor = Rectangle((0, 370), 400, 30)
floor.physics.simulation = "static"
floor.physics.friction = 1.0

ball = Circle((200, 50), 25)
ball.physics.simulation = "simulated"
ball.physics.elasticity = 0.6

@ball.register
def on_key_down(self, keys):
    if " " in keys:
        self.physics.velocity_y = -400

world.run()
```

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_physics.physics_world.PhysicsWorld
   :members:
   :no-private-members:
   :no-index:
```
