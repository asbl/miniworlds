from __future__ import annotations

import time

from miniworlds import Actor, World

from logic_benchmark_utils import configure_world, record_measurement_summary


ACTOR_COUNT = 1000

world = World(640, 440)
configure_world(world)

start = time.perf_counter()
actors = [
    Actor(((index * 17) % 620, (index * 29) % 420), world=world)
    for index in range(ACTOR_COUNT)
]
creation_elapsed = time.perf_counter() - start

start = time.perf_counter()
for actor in actors:
    actor.remove()
removal_elapsed = time.perf_counter() - start

assert not world.actors
print(
    f"actor lifecycle: created {ACTOR_COUNT} actors in {creation_elapsed * 1000:.2f} ms, "
    f"removed them in {removal_elapsed * 1000:.2f} ms"
)
record_measurement_summary(
    "actor lifecycle",
    {
        "actors": ACTOR_COUNT,
        "creation_ms": round(creation_elapsed * 1000, 4),
        "creations_per_s": round(ACTOR_COUNT / creation_elapsed, 4),
        "removal_ms": round(removal_elapsed * 1000, 4),
        "removals_per_s": round(ACTOR_COUNT / removal_elapsed, 4),
    },
)
