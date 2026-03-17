from __future__ import annotations

from collections import Counter

from miniworlds import Actor, World

from logic_benchmark_utils import configure_world, print_summary, record_frame_time


FRAME_LIMIT = 120
ROW_COUNT = 10
COLUMN_COUNT = 18
SPACING_X = 18
SPACING_Y = 18
START_X = 24
START_Y = 28


class CollisionActor(Actor):
    def __init__(self, position=(0, 0), lane: int = 0, *args, **kwargs) -> None:
        self.lane = lane
        super().__init__(position, *args, **kwargs)
        self.speed = 1 + (lane % 2)
        self.direction = 90 if lane % 2 == 0 else -90

    def on_setup(self) -> None:
        self.add_costume("images/ship.png")
        self.size = (20, 20)

    def act(self) -> None:
        if self.world.frame % 6 == 0:
            self.direction = self.direction + (8 if self.lane % 3 == 0 else -8)
        self.move(self.speed)

    def on_detecting_actor(self, other: Actor) -> None:
        self.world.logic_metrics["actor_collisions"] += 1
        self.direction = self.direction + 180

    def on_detecting_borders(self, borders: list[str]) -> None:
        self.world.logic_metrics["border_hits"] += len(borders)
        if "left" in borders or "right" in borders:
            self.direction = -self.direction
        if "top" in borders or "bottom" in borders:
            self.direction = 180 - self.direction


world = World(420, 260)
configure_world(world)


@world.register
def on_setup(self) -> None:
    self.logic_metrics = Counter()
    self.frame_times_ms = []
    self._benchmark_frame_started_at = None

    for row in range(ROW_COUNT):
        y = START_Y + row * SPACING_Y
        x_offset = 6 if row % 2 else 0
        for column in range(COLUMN_COUNT):
            x = START_X + column * SPACING_X + x_offset
            CollisionActor((x, y), lane=row, world=self)


@world.register
def act(self) -> None:
    record_frame_time(self)
    if self.frame >= FRAME_LIMIT:
        print_summary("actor logic collisions", self.frame_times_ms, self.logic_metrics)
        self.stop()
        self.quit()


world.run()