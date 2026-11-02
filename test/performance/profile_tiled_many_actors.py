"""
Benchmark: very many actors around a moving camera (Survivors-like).

Hundreds of dynamic actors move every frame, most of them outside the
scrolling camera view. This exercises the per-move overhead (spatial index
update, dirty gating, view cache) and the camera-scroll paths with a large
actor count.

Run with: invoke benchmarks.run --selection=tiled_many_actors
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
VIEW_COLUMNS = 25
VIEW_ROWS = 20
ENEMY_COUNT = 800
SEED = 7


class Enemy(Actor):
    """Wandering enemy: moves one tile per frame."""

    def act(self) -> None:
        world = self.world
        x, y = self.position
        step = 1 if (world.frame // 40 + int(x)) % 2 == 0 else -1
        self.position = (min(max(x + step, 0), world.world_size_x - 1), y)


class Player(Actor):
    pass


world = TiledWorld(GRID_COLUMNS, GRID_ROWS, tile_size=TILE_SIZE)
configure_world(world)
world.camera.view = (VIEW_COLUMNS, VIEW_ROWS)
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
    player.position = (min(max(px + step, 0), self.world_size_x - 1), py)

    self.camera.from_actor(player)

    if self.frame >= FRAME_LIMIT:
        print_summary("tiled many actors", self.frame_times_ms, self.logic_metrics)
        self.stop()
        self.quit()


world.run()
