from __future__ import annotations

import cProfile
from collections import Counter

from miniworlds import Actor, World

from logic_benchmark_utils import (
    configure_world,
    print_summary,
    record_frame_time,
    write_profile,
)


FRAME_LIMIT = 120
LANES = 10
BLOCKERS_PER_LANE = 18
MOVERS_PER_LANE = 18
LANE_SPACING = 24
STEP_X = 28
START_X = 36
START_Y = 28


class Blocker(Actor):
    def on_setup(self) -> None:
        self.add_costume("images/enemy.png")
        self.size = (18, 18)
        self.is_blocking = True
        self.static = True


class Mover(Actor):
    def __init__(self, position=(0, 0), lane: int = 0, *args, **kwargs) -> None:
        self.lane = lane
        super().__init__(position, *args, **kwargs)
        self.speed = 2
        self.direction = 90 if lane % 2 == 0 else -90
        self.is_blockable = True
        self.collision_type = "rect"

    def on_setup(self) -> None:
        self.add_costume("images/ship.png")
        self.size = (18, 18)

    def act(self) -> None:
        previous_position = self.position
        self.move(self.speed)

        if self.position == previous_position:
            self.world.logic_metrics["blocked_moves"] += 1
            self.direction = self.direction + 180
        else:
            self.world.logic_metrics["successful_moves"] += 1

    def on_detecting_borders(self, borders: list[str]) -> None:
        self.world.logic_metrics["border_hits"] += len(borders)
        self.direction = self.direction + 180


world = World(620, 300)
configure_world(world)


@world.register
def on_setup(self) -> None:
    self.logic_metrics = Counter()
    self.frame_times_ms = []
    self._benchmark_frame_started_at = None
    self.profiler = cProfile.Profile()

    for lane in range(LANES):
        y = START_Y + lane * LANE_SPACING
        for index in range(BLOCKERS_PER_LANE):
            blocker_x = START_X + 96 + index * STEP_X
            Blocker((blocker_x, y), world=self)
        for index in range(MOVERS_PER_LANE):
            mover_x = START_X + index * STEP_X
            Mover((mover_x, y), lane=lane, world=self)

    self.profiler.enable()


@world.register
def act(self) -> None:
    record_frame_time(self)
    if self.frame >= FRAME_LIMIT:
        self.profiler.disable()
        print_summary("blockable movement cprofile", self.frame_times_ms, self.logic_metrics)
        filename = write_profile(self.profiler, "blockable_movement")
        print(f"Profiling-Daten erfolgreich gespeichert in: {filename}")
        self.stop()
        self.quit()


world.run()