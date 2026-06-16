from __future__ import annotations

from collections import Counter

from miniworlds import Actor, World

from logic_benchmark_utils import configure_world, print_summary, record_frame_time


FRAME_LIMIT = 120
LANES = 8
NON_BLOCKERS_PER_LANE = 40
BLOCKERS_PER_LANE = 4
MOVERS_PER_LANE = 10
LANE_SPACING = 26
START_X = 30
START_Y = 30
STEP_X = 12


class Decoy(Actor):
    def on_setup(self) -> None:
        self.add_costume("images/enemy.png")
        self.size = (10, 10)
        self.collision_type = "rect"


class Blocker(Actor):
    def on_setup(self) -> None:
        self.add_costume("images/enemy.png")
        self.size = (10, 10)
        self.collision_type = "rect"
        self.is_blocking = True
        self.static = True


class Probe(Actor):
    def __init__(self, position=(0, 0), lane: int = 0, *args, **kwargs) -> None:
        self.lane = lane
        super().__init__(position, *args, **kwargs)
        self.speed = 2
        self.direction = 90 if lane % 2 == 0 else -90
        self.is_blockable = True
        self.collision_type = "rect"

    def on_setup(self) -> None:
        self.add_costume("images/ship.png")
        self.size = (10, 10)

    def act(self) -> None:
        previous_position = self.position
        self.move(self.speed)
        self.world.logic_metrics["blocking_queries"] += 1
        if self.position == previous_position:
            self.world.logic_metrics["blocked_moves"] += 1
            self.direction = self.direction + 180
        else:
            self.world.logic_metrics["successful_moves"] += 1


world = World(620, 260)
configure_world(world)


@world.register
def on_setup(self) -> None:
    self.logic_metrics = Counter()
    self.frame_times_ms = []
    self._benchmark_frame_started_at = None

    for lane in range(LANES):
        y = START_Y + lane * LANE_SPACING
        for index in range(NON_BLOCKERS_PER_LANE):
            Decoy((START_X + index * STEP_X, y), world=self)
        for index in range(BLOCKERS_PER_LANE):
            Blocker((START_X + 160 + index * 72, y), world=self)
        for index in range(MOVERS_PER_LANE):
            Probe((START_X + index * 20, y), lane=lane, world=self)


@world.register
def act(self) -> None:
    record_frame_time(self)
    if self.frame >= FRAME_LIMIT:
        print_summary("blocking index", self.frame_times_ms, self.logic_metrics)
        self.stop()
        self.quit()


world.run()
