from __future__ import annotations

from collections import Counter

from logic_benchmark_utils import configure_world, print_summary, record_frame_time

from miniworlds import Actor, World

FRAME_LIMIT = 180
GRID_COLUMNS = 30
GRID_ROWS = 18
SPACING = 22
START_X = 20
START_Y = 20


class StaticDecoration(Actor):
    def on_setup(self) -> None:
        self.add_costume((40, 110, 190, 255))
        self.size = (14, 14)
        self.static = True


class Player(Actor):
    def on_setup(self) -> None:
        self.add_costume((240, 180, 30, 255))
        self.size = (18, 18)
        self.direction = 90
        self.speed = 2

    def act(self) -> None:
        self.move(self.speed)
        self.world.logic_metrics["player_moves"] += 1

    def on_detecting_borders(self, borders: list[str]) -> None:
        self.direction += 180


world = World(720, 460)
configure_world(world)


@world.register
def on_setup(self) -> None:
    self.logic_metrics = Counter()
    self.frame_times_ms = []
    self._benchmark_frame_started_at = None

    for row in range(GRID_ROWS):
        for column in range(GRID_COLUMNS):
            StaticDecoration(
                (START_X + column * SPACING, START_Y + row * SPACING),
                world=self,
            )
    Player((30, 430), world=self)
    self.logic_metrics["static_actors"] = GRID_COLUMNS * GRID_ROWS


@world.register
def act(self) -> None:
    record_frame_time(self)
    if self.frame >= FRAME_LIMIT:
        print_summary("static scene", self.frame_times_ms, self.logic_metrics)
        self.stop()
        self.quit()


world.run()
