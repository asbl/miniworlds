# Dense scenes and survivors-style games

Pixel worlds provide optional simulation controls for games with many enemies,
projectiles and pickups. Existing `act()`, `detect()` and `detect_all()` calls
keep their default behavior. Spatial simulation queries and actor pooling
currently require a pixel `World`; pooling uses its standard world connector.

## Collision groups and offscreen simulation

Assign groups explicitly and select which groups a projectile can hit:

```python
from miniworlds import Actor, World

world = World(400, 400)
enemy = Actor((900, 900), world=world)
enemy.collision_group = "enemy"
shot = Actor((900, 900), world=world)
shot.collision_targets = {"enemy"}
shot.collision_type = "rect"
shot.collision_worldwide = True
assert shot.detect_all() == [enemy]
```

`collision_targets` is directional: it restricts what the querying actor detects.
`None` allows every group and an empty set detects none. Sprite `layer` still
only controls drawing order. A group's typed spatial index is built on its first
query, then updated when actors move, change group, deactivate or leave the world.

Ordinary actor collision queries remain camera-filtered unless
`collision_worldwide` is enabled. `actor.detect_collisions(Enemy)` explicitly
checks overlaps independently of the camera and uses the actor's hitbox mode.
Use rectangles or circles when pixel-perfect mask collisions are unnecessary.

## Neighbors and nearest targets

`world.query_rect(rect, Enemy)` finds overlapping hitboxes.
`world.query_radius(position, radius, Enemy)` finds actor **centers** in a circle.
`world.find_nearest(position, Enemy, radius=300)` finds a center within that radius,
or returns `None`. Omitting the radius searches the entire world with expanding
spatial queries. These APIs use world pixel coordinates, include offscreen actors
and accept `collision_group="enemy"` and `exclude=player`. The position may also
be an Actor, in which case its center is used. Equal-distance nearest targets
are resolved by `actor_id`. Query result lists otherwise have no ordering contract.

Keep a target between updates while it remains active and in range, rather than
reacquiring it for every projectile and every frame.

## Pooling projectiles

```python
from miniworlds import Actor, ActorPool, World

world = World(400, 400)

class Projectile(Actor):
    def on_setup(self):
        self.size = (6, 6)
        self.collision_type = "rect"
        self.collision_targets = {"enemy"}
        self.collision_worldwide = True

    def act(self):
        self.move_towards_fast(self.target, 4)

def reset_projectile(actor, target):
    actor.target = target
    actor.damage = 10

pool = ActorPool(lambda: Projectile(world=world), initial_size=32,
                 max_size=256, reset=reset_projectile)
shot = pool.acquire((100, 100), target=(200, 200))
if shot is not None:
    pool.release(shot)
pool.clear()
```

`acquire()` returns `None` when the configured capacity is exhausted. Call
`release()` instead of `remove()` to reuse an actor. The reset callback runs
before activation and must reset game state such as health, damage, lifetime
and hit history. Construction and `on_setup()` run once per pooled actor.
Position, sensor and costume managers are retained across releases.

Inactive actors leave drawing groups, spatial indices, blocking and event
dispatch. `actor.active = False` pauses timers bound directly to that actor;
reactivation restores its subscriptions. Pool release instead cancels such
timers to prevent them from firing during the next lifetime. Timers or closures
owned by other objects must be managed by the game. `clear()` permanently
removes all pool-owned actors. Do not transfer pooled actors between worlds.

## Movement, thinking and animation

`actor.move_towards_fast(target, distance)` moves without changing its facing
direction. It clamps the step at the target and respects destination blocking.
It has the same discrete destination-blocking limitation as normal movement;
fast projectiles may require a swept collision test in the game.

`move_towards()` continues to update direction; its scalar movement and the
scalar `get_distance_to()` implementation avoid creating small NumPy arrays.

Use `on_think()` for expensive decisions and `act()` for continuous movement:

```python
from miniworlds import Actor

class Enemy(Actor):
    def on_setup(self):
        self.think_interval = 6
        self.offscreen_act_interval = 4
        self.animation_interval = 8

    def on_think(self):
        self.target = self.world.find_nearest(self, collision_group="player")

    def act(self):
        if getattr(self, "target", None) is not None and self.target.active:
            self.move_towards_fast(self.target, 1.5)
```

Thinking runs before movement. `act_interval` and `think_interval` count world
logic ticks, so they combine with `world.tick_rate` without starving actors.
`offscreen_act_interval` sets a minimum interval for both hooks outside the
camera. Intervals are staggered by actor ID. Slower movement updates reduce
travel speed unless the game compensates for elapsed ticks.

`collision_interval` optionally reduces automatic collision-event checks, in
rendered frames; direct collision queries remain immediate. This also reduces
temporal collision precision. `animation_interval > 1` overrides the costume's
animation frame interval and staggers actors. The default value `1` preserves
the existing `costume.animation_speed` behavior. Dirty costume changes still
render immediately.

## Sharing transform work and bounding memory

Set `actor.costume.shared_transform_cache = True` for repeated scale/rotation
work across identical sprite frames. This is opt-in because hashing source
pixels can outweigh cheap transforms. Content keys detect source pixel changes;
returned surfaces remain independently mutable. The process-wide cache defaults
to **32 MiB** and evicts least recently used results:

```python
from miniworlds import Appearance

Appearance.set_shared_cache_budget(16 * 1024 * 1024)
Appearance.clear_shared_cache()
```

Per-appearance pipeline caches discard previous dirty revisions immediately.
Keep decorative enemies non-rotatable unless their artwork needs rotation;
the default is already `is_rotatable = False`.

Run `invoke benchmarks.pyodide` to measure targeting, grouped collision events,
pooled projectiles and a rendered swarm. Timings depend on scene density,
browser and machine; use the same environment for comparisons.
