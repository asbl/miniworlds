# ActorPhysics (actor.physics)

Every actor in a `PhysicsWorld` gains an `actor.physics` attribute
of type `ActorPhysics`. Use it to control how the physics engine treats that actor.

Access it as:

```python
my_actor.physics.simulation = "simulated"
my_actor.physics.elasticity = 0.8
my_actor.physics.velocity_x = 200
```

## Simulation mode

The `simulation` property is the primary switch. It must be set **before** the world starts running, or after a geometry change.

| Value | Description |
|---|---|
| `"simulated"` | Fully simulated: affected by gravity, collisions, impulses. |
| `"manual"` | Kinematic: not affected by gravity, but can be moved manually and collides with others. |
| `"static"` | Not moved by the engine; other actors can collide with it (e.g. floors, walls). |
| `None` | Completely removed from the physics space; no collisions possible. |

## Physical properties

| Property | Default | Description |
|---|---|---|
| `density` | `10` | Mass density. Higher value = heavier object. Re-adds actor to physics space when changed. |
| `friction` | `0.5` | Surface friction (0 = frictionless, 1 = very rough). Re-adds actor to physics space. |
| `elasticity` | `0.5` | Bounciness (0 = no bounce, 1 = perfect bounce). Re-adds actor to physics space. |
| `shape_type` | `"rect"` | Collision shape: `"rect"` or `"circle"`. Re-adds actor to physics space. |
| `size` | `(1, 1)` | Scale factor for the physics collision box relative to the actor's visual size. |
| `is_rotatable` | depends on mode | Whether the physics engine may rotate the actor. |
| `damping` | `1` | Per-actor damping multiplied with the world's damping. |
| `max_velocity_x` | `inf` | Clamp the horizontal velocity to this maximum. |

## Velocity control (manual / simulated)

| Property | Description |
|---|---|
| `velocity_x` | Horizontal velocity in pixels per second. Positive = right. |
| `velocity_y` | Vertical velocity in pixels per second. Positive = down. |

## Impulses and forces

| Method | Description |
|---|---|
| `impulse_in_direction(direction, power)` | Apply an instantaneous impulse in the given direction. |
| `force_in_direction(direction, power)` | Apply a continuous force in the given direction. |

## Joints

| Method | Description |
|---|---|
| `join(other, type="pin")` | Create a pin joint between this actor and `other`, connecting their centers. |
| `remove_join(other)` | Remove the joint to `other`. |

## Example: Platformer character

```python
from miniworlds import Rectangle
from miniworlds_physics import PhysicsWorld

world = PhysicsWorld(400, 300)

floor = Rectangle((0, 270), 400, 30)
floor.physics.simulation = "static"
floor.physics.friction = 0.8

player = Rectangle((50, 200), 30, 50)
player.physics.simulation = "manual"
player.physics.shape_type = "rect"

@player.register
def on_key_pressed(self, keys):
    if "a" in keys:
        self.physics.velocity_x = -150
    elif "d" in keys:
        self.physics.velocity_x = 150
    else:
        self.physics.velocity_x = 0

@player.register
def on_key_down(self, keys):
    if " " in keys:
        self.physics.velocity_y = -400

world.run()
```

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_physics.actor_physics.ActorPhysics
   :members:
   :no-private-members:
```
