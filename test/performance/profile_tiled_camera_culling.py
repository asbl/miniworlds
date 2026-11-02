"""
Survivors-like benchmark: large TiledWorld with a moving camera.

Simulates a typical Survivors-like scene on a big tile map:
many dynamic actors move every frame and query the world around them,
while the camera follows the player across a large world.

This exercises the camera view cache (get_actors_in_view) and the
per-move camera cache invalidation on every actor position change.

Run with: python -m test.performance.profile_tiled_camera_culling
"""

from __future__ import annotations

import random
from collections import Counter

from miniworlds import Actor, TiledWorld

from logic_benchmark_utils import configure_world, print_summary, record_frame_time


FRAME_LIMIT = 120
GRID_COLUMNS = 100
GRID_ROWS = 75
TILE_SIZE = 32
ENEMY_COUNT = 120
SEED = 42


class Enemy(Actor):
    """Wandering enemy: moves one tile per frame and queries the world."""

    def act(self) -> None:
        world = self.world
        x, y = self.position
        step = 1 if (world.frame // 40 + int(x)) % 2 == 0 else -1
        new_x = min(max(x + step, 0), world.world_size_x - 1)
        self.position = (new_x, y)
        # Survivors-like per-enemy queries around its own position
        world.actors_at((new_x, y))
        world.camera.get_actors_in_view()


class Player(Actor):
    pass


world = TiledWorld(GRID_COLUMNS, GRID_ROWS, tile_size=TILE_SIZE)
configure_world(world)
world.tick_rate = 1

rng = random.Random(SEED)


@world.register
def on_setup(self) -> None:
    self.logic_metrics = Counter()
    self.frame_times_ms = []
    self._benchmark_frame_started_at = None

    self.player = Player((GRID_COLUMNS // 2, GRID_ROWS // 2), world=self)
    self.player.static = False

    for _ in range(ENEMY_COUNT):
        enemy = Enemy(
            (rng.randrange(GRID_COLUMNS), rng.randrange(GRID_ROWS)), world=self
        )
        enemy.static = False


@world.register
def act(self) -> None:
    record_frame_time(self)

    player = self.player
    px, py = player.position
    step = 1 if self.frame % 80 < 40 else -1
    new_x = min(max(px + step, 0), self.world_size_x - 1)
    player.position = (new_x, py)

    self.camera.from_actor(player)

    visible_actors = self.camera.get_actors_in_view()
    self.logic_metrics["visible_actor_samples"] += len(visible_actors)

    if self.frame >= FRAME_LIMIT:
        print_summary("tiled camera culling", self.frame_times_ms, self.logic_metrics)
        self.stop()
        self.quit()


world.run()
