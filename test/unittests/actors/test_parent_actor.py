from __future__ import annotations

import unittest

from miniworlds import Actor, App, World
from miniworlds.actors.parent_actor import ParentActor


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
