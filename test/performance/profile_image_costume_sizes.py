from __future__ import annotations

from collections import Counter
from pathlib import Path
import tempfile

import pygame

from miniworlds import Actor, World

from logic_benchmark_utils import configure_world, print_summary, record_frame_time


FRAME_LIMIT = 120
ACTORS_PER_VARIANT = 10
ROW_SPACING = 40
COLUMN_SPACING = 52
START_X = 42
START_Y = 42
WORLD_WIDTH = 720
WORLD_HEIGHT = 320

IMAGE_VARIANTS = [
    ((17, 23), (42, 56)),
    ((63, 95), (60, 90)),
    ((129, 97), (84, 62)),
    ((511, 287), (120, 68)),
]

TEMP_IMAGE_DIR = tempfile.TemporaryDirectory(prefix="miniworlds-image-costumes-")


def create_image(path: Path, size: tuple[int, int], color: tuple[int, int, int, int]) -> None:
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill(color)
    pygame.draw.rect(surface, (255, 255, 255, 255), surface.get_rect(), 3)
    pygame.draw.line(surface, (0, 0, 0, 255), (0, 0), (size[0] - 1, size[1] - 1), 2)
    pygame.draw.line(surface, (0, 0, 0, 255), (size[0] - 1, 0), (0, size[1] - 1), 2)
    pygame.image.save(surface, path)


IMAGE_PATHS: list[str] = []
for index, (source_size, _) in enumerate(IMAGE_VARIANTS):
    color = (
        60 + index * 40,
        120 + index * 20,
        max(40, 220 - index * 30),
        255,
    )
    image_path = Path(TEMP_IMAGE_DIR.name) / f"variant_{index}.png"
    create_image(image_path, source_size, color)
    IMAGE_PATHS.append(str(image_path))


class ImageCostumeActor(Actor):
    def __init__(
        self,
        position=(0, 0),
        image_path: str = "",
        target_size: tuple[int, int] = (40, 40),
        lane: int = 0,
        *args,
        **kwargs,
    ) -> None:
        self.image_path = image_path
        self.target_size = target_size
        self.lane = lane
        self._expanded = False
        super().__init__(position, *args, **kwargs)
        self.speed = 1
        self.direction = 90 if lane % 2 == 0 else -90
        self.collision_type = "rect"

    def on_setup(self) -> None:
        self.add_costume(self.image_path)
        self.size = self.target_size

    def act(self) -> None:
        if self.world.frame % 4 == 0:
            self.direction = self.direction + (8 if self.lane % 2 == 0 else -8)
            self.world.logic_metrics["rotations"] += 1

        if self.world.frame % 15 == 0:
            width, height = self.target_size
            if self._expanded:
                self.size = (width, height)
            else:
                self.size = (width + 6, height + 4)
            self._expanded = not self._expanded
            self.world.logic_metrics["resizes"] += 1

        self.move(self.speed)

    def on_detecting_borders(self, borders: list[str]) -> None:
        self.world.logic_metrics["border_hits"] += len(borders)
        self.direction = self.direction + 180


world = World(WORLD_WIDTH, WORLD_HEIGHT)
configure_world(world)


@world.register
def on_setup(self) -> None:
    self.logic_metrics = Counter()
    self.frame_times_ms = []
    self._benchmark_frame_started_at = None

    for lane, image_path in enumerate(IMAGE_PATHS):
        _, target_size = IMAGE_VARIANTS[lane]
        y = START_Y + lane * ROW_SPACING
        for index in range(ACTORS_PER_VARIANT):
            x = START_X + index * COLUMN_SPACING
            ImageCostumeActor(
                (x, y),
                image_path=image_path,
                target_size=target_size,
                lane=lane,
                world=self,
            )


@world.register
def act(self) -> None:
    record_frame_time(self)
    if self.frame >= FRAME_LIMIT:
        print_summary("image costume sizes", self.frame_times_ms, self.logic_metrics)
        self.stop()
        self.quit()


world.run()