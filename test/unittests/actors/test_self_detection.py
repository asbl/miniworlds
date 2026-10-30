import math
import unittest

from miniworlds import Actor, World
from miniworlds.base.app import App


class TestSelfDetection(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(200, 200)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_detect_excludes_self_for_each_collision_type(self):
        actor = Actor((80, 80), world=self.world)
        actor.size = (40, 40)
        actor.add_costume((255, 0, 0))

        for collision_type in ('rect', 'static-rect', 'circle', 'mask'):
            with self.subTest(collision_type=collision_type):
                actor.collision_type = collision_type
                self.assertIsNone(actor.detect(actor))
                self.assertIsNone(actor.detect(filter=actor))
                self.assertIsNone(actor.detect(actor, 0))
                self.assertEqual(actor.detect_all(actor), [])

    def test_detect_preserves_collisions_with_other_actors(self):
        actor = Actor((80, 80), world=self.world)
        other = Actor((85, 80), world=self.world)
        actor.size = (40, 40)
        other.size = (40, 40)
        actor.add_costume((255, 0, 0))
        other.add_costume((0, 255, 0))

        for collision_type in ('rect', 'static-rect', 'circle', 'mask'):
            with self.subTest(collision_type=collision_type):
                actor.collision_type = collision_type
                other.collision_type = collision_type
                self.assertIs(actor.detect(other), other)

    def test_moose_group_avoidance_does_not_move_isolated_enemies(self):
        enemies = [Actor(position, world=self.world) for position in ((40, 40), (150, 40), (40, 150))]
        for enemy in enemies:
            enemy.size = (24, 24)
            enemy.collision_type = 'rect'
        initial = [enemy.position for enemy in enemies]
        avoidance_count = 0

        for enemy in enemies:
            enemy.move_towards((180, 180), 11)
            for first in enemies:
                for second in enemies:
                    if first.detect(second):
                        avoidance_count += 1
                        first.x += 123.05
                        first.y += 123.05

        self.assertEqual(avoidance_count, 0)
        for position, enemy in zip(initial, enemies):
            self.assertAlmostEqual(math.dist(position, enemy.position), 11)
