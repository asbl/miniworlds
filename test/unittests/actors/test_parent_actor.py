from __future__ import annotations

import unittest

from miniworlds import Actor, App, World
from miniworlds.actors.parent_actor import ParentActor
from miniworlds.base.exceptions import NoValidPositionOnInitException


class TestParentActor(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(120, 120)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_add_child_propagates_parent_and_layer(self):
        parent = ParentActor((40, 40), world=self.world)
        child = Actor((50, 50), world=self.world)

        parent.layer = 3
        parent.add_child(child)

        self.assertIs(child._parent, parent)
        self.assertEqual(child.layer, 4)

        parent.layer = 5

        self.assertEqual(child.layer, 6)

    def test_visible_propagates_to_children(self):
        parent = ParentActor((40, 40), world=self.world)
        child = Actor((50, 50), world=self.world)
        parent.add_child(child)

        parent.visible = False

        self.assertFalse(parent.visible)
        self.assertFalse(child.visible)

        parent.visible = True

        self.assertTrue(child.visible)

    def test_removing_parent_removes_children_from_world(self):
        parent = ParentActor((40, 40), world=self.world)
        child = Actor((50, 50), world=self.world)
        parent.add_child(child)

        self.assertIn(parent, self.world.actors)
        self.assertIn(child, self.world.actors)

        parent.remove()

        self.assertNotIn(parent, self.world.actors)
        self.assertNotIn(child, self.world.actors)

    def test_parent_actor_instances_do_not_share_default_children(self):
        first = ParentActor((20, 20), world=self.world)
        second = ParentActor((30, 30), world=self.world)
        child = Actor((40, 40), world=self.world)

        first.add_child(child)

        self.assertIn(child, first.children)
        self.assertNotIn(child, second.children)

    def test_actor_accepts_two_coordinate_arguments(self):
        actor = Actor(40, 50, world=self.world)

        self.assertEqual(actor.position, (40, 50))
        self.assertIn(actor, self.world.actors)

    def test_actor_accepts_tuple_position_argument(self):
        actor = Actor((40, 50), world=self.world)

        self.assertEqual(actor.position, (40, 50))
        self.assertIn(actor, self.world.actors)

    def test_simple_actor_subclass_accepts_two_coordinate_arguments(self):
        class Player(Actor):
            pass

        actor = Player(40, 50, world=self.world)

        self.assertEqual(actor.position, (40, 50))
        self.assertIn(actor, self.world.actors)

    def test_parent_actor_keeps_tuple_only_position_signature(self):
        with self.assertRaises(NoValidPositionOnInitException):
            ParentActor(40, 50, world=self.world)
