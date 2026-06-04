from __future__ import annotations

import time

from miniworlds import Actor, World

from logic_benchmark_utils import configure_world, record_measurement_summary


GRID_COLUMNS = 24
GRID_ROWS = 16
SPACING = 24
ITERATIONS = 20000


world = World(640, 440)
configure_world(world)

for row in range(GRID_ROWS):
    for column in range(GRID_COLUMNS):
        actor = Actor((20 + column * SPACING, 20 + row * SPACING), world=world)
        actor.size = (18, 18)
        actor.static = True

world.camera.get_actors_in_view()
positions = [
    (20 + (index % GRID_COLUMNS) * SPACING, 20 + (index % GRID_ROWS) * SPACING)
    for index in range(ITERATIONS)
]

start = time.perf_counter()
world_hits = sum(len(world.detect_actors(position)) for position in positions)
world_elapsed = time.perf_counter() - start

start = time.perf_counter()
pixel_hits = sum(len(world.get_actors_from_pixel(position)) for position in positions)
pixel_elapsed = time.perf_counter() - start

print(
    f"world queries: {ITERATIONS} world queries in {world_elapsed * 1000:.2f} ms, "
    f"{ITERATIONS} pixel queries in {pixel_elapsed * 1000:.2f} ms"
)
record_measurement_summary(
    "world queries",
    {
        "actors": len(world.actors),
        "iterations": ITERATIONS,
        "world_hits": world_hits,
        "world_queries_ms": round(world_elapsed * 1000, 4),
        "world_queries_per_s": round(ITERATIONS / world_elapsed, 4),
        "pixel_hits": pixel_hits,
        "pixel_queries_ms": round(pixel_elapsed * 1000, 4),
        "pixel_queries_per_s": round(ITERATIONS / pixel_elapsed, 4),
    },
)
