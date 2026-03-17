from __future__ import annotations

from collections import Counter

from miniworlds import Actor, World

from logic_benchmark_utils import configure_world, print_summary, record_frame_time


FRAME_LIMIT = 120
GRID_COLUMNS = 56
GRID_ROWS = 40
SPACING_X = 56
SPACING_Y = 56
START_X = 24
START_Y = 24
CAMERA_STEP_X = 28
CAMERA_STEP_Y = 20


class SceneryActor(Actor):
    def on_setup(self) -> None:
        self.add_costume("images/ship.png")
        self.size = (22, 22)
        self.static = True
        self.collision_type = "rect"


world = World(320, 220)
configure_world(world)
world.world_size_x = 3400
world.world_size_y = 2500


@world.register
def on_setup(self) -> None:
    self.logic_metrics = Counter()
    self.frame_times_ms = []
    self._benchmark_frame_started_at = None

    for row in range(GRID_ROWS):
        y = START_Y + row * SPACING_Y
        for column in range(GRID_COLUMNS):
            x = START_X + column * SPACING_X
            SceneryActor((x, y), world=self)


@world.register
def act(self) -> None:
    record_frame_time(self)

    max_x = max(0, self.world_size_x - self.camera.width)
    max_y = max(0, self.world_size_y - self.camera.height)
    next_x = (self.frame * CAMERA_STEP_X) % (max_x + 1)
    next_y = ((self.frame // 2) * CAMERA_STEP_Y) % (max_y + 1)
    self.camera.topleft = (next_x, next_y)

    visible_actors = self.camera.get_actors_in_view()
    self.logic_metrics["visible_actor_samples"] += len(visible_actors)

    if self.frame >= FRAME_LIMIT:
        print_summary("camera culling", self.frame_times_ms, self.logic_metrics)
        self.stop()
        self.quit()


world.run()