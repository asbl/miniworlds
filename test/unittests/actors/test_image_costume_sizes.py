from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pygame

from miniworlds import Actor, App, World


class TestImageCostumeSizes(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(160, 120)
        self.world.backgrounds._init_display()
        self.tempdir = tempfile.TemporaryDirectory()
        self.image_paths = {
            "odd": self._create_image("odd.png", (17, 23), (255, 40, 40, 255)),
            "medium": self._create_image("medium.png", (63, 95), (40, 255, 120, 255)),
            "large": self._create_image("large.png", (257, 173), (40, 120, 255, 255)),
        }

    def tearDown(self):
        self.tempdir.cleanup()
        App.reset(unittest=True, file=__file__)

    def _create_image(
        self, filename: str, size: tuple[int, int], color: tuple[int, int, int, int]
    ) -> Path:
        path = Path(self.tempdir.name) / filename
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill(color)
        pygame.draw.line(surface, (255, 255, 255, 255), (0, 0), (size[0] - 1, size[1] - 1), 2)
        pygame.image.save(surface, path)
        return path

    def test_image_costume_with_odd_source_dimensions_scales_to_actor_size(self):
        actor = Actor((20, 20), world=self.world)

        actor.add_costume(str(self.image_paths["odd"]))
        actor.size = (51, 69)

        self.assertTrue(actor.costume.is_upscaled)
        self.assertEqual(actor.image.get_size(), (51, 69))
        self.assertEqual(actor.position_manager.get_global_rect().size, (51, 69))

    def test_multiple_image_source_sizes_keep_requested_target_sizes(self):
        specs = [
            (self.image_paths["odd"], (33, 45), (20, 20)),
            (self.image_paths["medium"], (72, 108), (70, 20)),
            (self.image_paths["large"], (128, 84), (130, 20)),
        ]

        actors = []
        for image_path, target_size, position in specs:
            actor = Actor(position, world=self.world)
            actor.add_costume(str(image_path))
            actor.size = target_size
            actors.append((actor, target_size))

        for actor, target_size in actors:
            self.assertEqual(actor.image.get_size(), target_size)
            self.assertEqual(actor.position_manager.get_global_rect().size, target_size)

    def test_switching_between_large_image_costumes_preserves_requested_size(self):
        actor = Actor((60, 60), world=self.world)
        actor.add_costume(str(self.image_paths["odd"]))
        actor.add_costume(str(self.image_paths["large"]))
        actor.size = (96, 54)

        actor.switch_costume(1)

        self.assertEqual(actor.image.get_size(), (96, 54))
        self.assertEqual(actor.position_manager.get_global_rect().size, (96, 54))


if __name__ == "__main__":
    unittest.main()