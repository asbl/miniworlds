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
LANES = 8
PAIRS_PER_LANE = 10
LANE_SPACING = 24
PAIR_SPACING = 28
START_X = 40
START_Y = 36


class Hunter(Actor):
    def __init__(self, position=(0, 0), lane: int = 0, *args, **kwargs) -> None:
        self.lane = lane
        super().__init__(position, *args, **kwargs)
        self.speed = 2
        self.direction = 90

    def on_setup(self) -> None:
        self.add_costume("images/ship.png")
        self.size = (18, 18)

    def act(self) -> None:
        if self.world.frame % 8 == 0:
            self.direction = self.direction + (6 if self.lane % 2 == 0 else -6)
        self.move(self.speed)

    def on_detecting_runner(self, runner: Actor) -> None:
        self.world.logic_metrics["hunter_hits"] += 1
        self.direction = self.direction + 180

    def on_not_detecting_runner(self) -> None:
        self.world.logic_metrics["hunter_misses"] += 1

    def on_detecting_borders(self, borders: list[str]) -> None:
        self.world.logic_metrics["hunter_border_hits"] += len(borders)
        self.direction = self.direction + 180


class Runner(Actor):
    def __init__(self, position=(0, 0), lane: int = 0, *args, **kwargs) -> None:
        self.lane = lane
        super().__init__(position, *args, **kwargs)
        self.speed = 2
        self.direction = -90

    def on_setup(self) -> None:
        self.add_costume("images/enemy.png")
        self.size = (18, 18)

    def act(self) -> None:
        if self.world.frame % 10 == 0:
            self.direction = self.direction + (4 if self.lane % 2 == 0 else -4)
        self.move(self.speed)

    def on_detecting_hunter(self, hunter: Actor) -> None:
        self.world.logic_metrics["runner_hits"] += 1
        self.direction = self.direction + 180

    def on_not_detecting_hunter(self) -> None:
        self.world.logic_metrics["runner_misses"] += 1

    def on_detecting_borders(self, borders: list[str]) -> None:
        self.world.logic_metrics["runner_border_hits"] += len(borders)
        self.direction = self.direction + 180


world = World(420, 280)
configure_world(world)


@world.register
def on_setup(self) -> None:
    self.logic_metrics = Counter()
    self.frame_times_ms = []
    self._benchmark_frame_started_at = None
    self.profiler = cProfile.Profile()

    for lane in range(LANES):
        y = START_Y + lane * LANE_SPACING
        for pair in range(PAIRS_PER_LANE):
            hunter_x = START_X + pair * PAIR_SPACING
            runner_x = hunter_x + 12
            Hunter((hunter_x, y), lane=lane, world=self)
            Runner((runner_x, y), lane=lane, world=self)

    print("enable cprofile")
    self.profiler.enable()


@world.register
def act(self) -> None:
    record_frame_time(self)
    if self.frame >= FRAME_LIMIT:
        self.profiler.disable()
        print_summary("actor logic filters cprofile", self.frame_times_ms, self.logic_metrics)
        filename = write_profile(self.profiler, "logic_filters")
        print(f"Profiling-Daten erfolgreich gespeichert in: {filename}")
        self.stop()
        self.quit()


world.run()