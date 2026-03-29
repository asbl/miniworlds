from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pygame

from miniworlds import Actor, App, Costume, World


class TestCostumeAttachment(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(160, 120)
        self.world.backgrounds._init_display()
        self.tempdir = tempfile.TemporaryDirectory()
        self.image_paths = {
            "walk1": self._create_image("walk1.png", (18, 22), (255, 80, 80, 255)),
            "walk2": self._create_image("walk2.png", (18, 22), (80, 255, 120, 255)),
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
        pygame.draw.rect(surface, (255, 255, 255, 255), surface.get_rect(), 2)
        pygame.image.save(surface, path)
        return path

    def test_costume_constructor_with_actor_auto_attaches_to_actor(self):
        actor = Actor((20, 20), world=self.world)

        costume = Costume(actor)
        costume.add_image(str(self.image_paths["walk1"]))
        costume.add_image(str(self.image_paths["walk2"]))

        self.assertTrue(actor.has_costume())
        self.assertIs(actor.costume, costume)
        self.assertEqual(actor.costume_count, 1)
        self.assertEqual(len(costume.images), 2)
        self.assertIs(costume.parent, actor)
        self.assertIn(costume, actor.costumes.appearances_list)

    def test_detached_costume_can_be_added_later(self):
        actor = Actor((60, 20), world=self.world)
        costume = Costume()
        costume.add_image(str(self.image_paths["walk1"]))
        costume.add_image(str(self.image_paths["walk2"]))

        added_costume = actor.add_costume(costume)

        self.assertIs(added_costume, costume)
        self.assertTrue(actor.has_costume())
        self.assertIs(actor.costume, costume)
        self.assertEqual(actor.costume_count, 1)
        self.assertEqual(len(costume.images), 2)
        self.assertIs(costume.parent, actor)
        self.assertIn(costume, actor.costumes.appearances_list)


if __name__ == "__main__":
    unittest.main()