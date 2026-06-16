from __future__ import annotations

from collections import Counter

from logic_benchmark_utils import configure_world, print_summary, record_frame_time

from miniworlds import Actor, World

FRAME_LIMIT = 120
ROW_COUNT = 8
ACTORS_PER_ROW = 12
SPACING_X = 20
SPACING_Y = 28
START_X = 34
START_Y = 34
MESSAGE_INTERVAL = 5


class CommunicatingActor(Actor):
    def __init__(self, position=(0, 0), lane: int = 0, *args, **kwargs) -> None:
        self.lane = lane
        super().__init__(position, *args, **kwargs)
        self.speed = 1
        self.direction = 90 if lane % 2 == 0 else -90
        self.collision_type = "rect"

    def on_setup(self) -> None:
        self.add_costume((50, 130, 220, 255))
        self.size = (24, 20)

    def act(self) -> None:
        detected = self.detect_all(CommunicatingActor)
        self.world.logic_metrics["collision_queries"] += 1
        self.world.logic_metrics["collision_hits"] += len(detected)

        if detected and self.world.frame % MESSAGE_INTERVAL == 0:
            self.send_message("collision_ping")
            self.world.logic_metrics["messages_queued"] += 1

        self.move(self.speed)

    def on_message(self, message: str) -> None:
        if message == "collision_ping":
            self.world.logic_metrics["message_handler_calls"] += 1

    def on_detecting_borders(self, borders: list[str]) -> None:
        self.direction += 180


world = World(420, 280)
configure_world(world)


@world.register
def on_setup(self) -> None:
    self.logic_metrics = Counter()
    self.frame_times_ms = []
    self._benchmark_frame_started_at = None

    for row in range(ROW_COUNT):
        for column in range(ACTORS_PER_ROW):
            CommunicatingActor(
                (START_X + column * SPACING_X, START_Y + row * SPACING_Y),
                lane=row,
                world=self,
            )
    self.logic_metrics["actors"] = ROW_COUNT * ACTORS_PER_ROW


@world.register
def act(self) -> None:
    record_frame_time(self)
    if self.frame >= FRAME_LIMIT:
        print_summary(
            "collision communication",
            self.frame_times_ms,
            self.logic_metrics,
        )
        self.stop()
        self.quit()


world.run()
