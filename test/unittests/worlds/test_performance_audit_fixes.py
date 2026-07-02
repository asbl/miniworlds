import unittest
from unittest.mock import patch

import pygame

from miniworlds import Actor, World
from miniworlds.base.app import App
from miniworlds.worlds.manager.mainloop_manager import MainloopManager


# Unique class names so they do not collide with classes of the same name in
# other test modules (e.g. test_sensor_manager.py). The EventDefinition caches
# resolved class names by lowercased class name across App.reset(), so a shared
# name like "Wall"/"Runner" would resolve to the wrong class in the other suite.
class AuditWall(Actor):
    pass


class AuditRunner(Actor):
    pass


class TestDetectActorRectEarlyReturn(unittest.TestCase):
    """Tests for performance audit issue #4: detect_actor must not re-iterate
    all candidates when no rect collision is found. Previously, the rect branch
    fell through to a redundant second colliderect loop over every candidate.
    """

    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(120, 120)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def _create_actor(self, cls, position=(20, 20)):
        actor = cls(position, world=self.world)
        actor.size = (16, 16)
        actor.collision_type = "rect"
        return actor

    def test_detect_actor_returns_none_when_no_rect_collision(self):
        hunter = self._create_actor(Actor, position=(10, 10))
        # Wall far away — no rect collision
        self._create_actor(AuditWall, position=(100, 100))

        result = hunter.sensor_manager.detect_actor(AuditWall)
        self.assertIsNone(result)

    def test_detect_actor_returns_none_when_only_self_in_range(self):
        hunter = self._create_actor(Actor, position=(40, 40))

        result = hunter.sensor_manager.detect_actor(Actor)
        self.assertIsNone(result)

    def test_detect_actor_finds_colliding_rect_actor(self):
        hunter = self._create_actor(Actor, position=(40, 40))
        wall = self._create_actor(AuditWall, position=(48, 40))

        result = hunter.sensor_manager.detect_actor(AuditWall)
        self.assertIs(result, wall)

    def test_detect_actor_rect_branch_does_not_call_collision_type_check(self):
        """Regression: the rect branch must return None directly and not fall
        through into _detect_actor_by_collision_type on the full candidate list.
        """
        hunter = self._create_actor(Actor, position=(10, 10))
        # Several non-colliding candidates in view
        self._create_actor(AuditWall, position=(100, 10))
        self._create_actor(AuditWall, position=(100, 100))
        self._create_actor(AuditWall, position=(10, 100))

        with patch.object(
            hunter.sensor_manager,
            "_detect_actor_by_collision_type",
            wraps=hunter.sensor_manager._detect_actor_by_collision_type,
        ) as collision_check:
            result = hunter.sensor_manager.detect_actor(AuditWall)

        self.assertIsNone(result)
        # The rect branch must return early; _detect_actor_by_collision_type
        # should never be reached when no rect collision is found.
        collision_check.assert_not_called()

    def test_detect_actor_mask_type_does_not_use_rect_early_return(self):
        """For mask/circle collision types, the rect early-return must not
        short-circuit the mask-based detection."""
        hunter = self._create_actor(Actor, position=(40, 40))
        hunter.collision_type = "mask"
        wall = self._create_actor(AuditWall, position=(48, 48))
        wall.collision_type = "mask"

        result = hunter.sensor_manager.detect_actor(AuditWall)
        self.assertIs(result, wall)


class TestUpdateAllCostumesSkipsIdle(unittest.TestCase):
    """Tests for performance audit issue #5: _update_all_costumes must skip
    dynamic actors whose costume is neither animated nor dirty. Previously it
    called costume.update() for every dynamic actor every frame.
    """

    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(120, 120)
        self.manager = MainloopManager(self.world, self.world.app)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def _create_actor(self, position=(20, 20)):
        actor = Actor(position, world=self.world)
        actor.size = (16, 16)
        return actor

    def test_idle_dynamic_actor_costume_not_updated(self):
        actor = self._create_actor()
        # Ensure the actor is dynamic and its costume is settled (not dirty,
        # not animated) by forcing a clean state.
        actor.costume.set_dirty("all", 0)
        actor.costume._dirty = 0
        actor.costume._is_animated = False
        self.assertIn(actor, self.world._dynamic_actors)

        with patch.object(
            actor.costume, "update", wraps=actor.costume.update
        ) as update_mock:
            self.manager._update_all_costumes()

        update_mock.assert_not_called()

    def test_animated_dynamic_actor_costume_is_updated(self):
        actor = self._create_actor()
        actor.costume._is_animated = True
        actor.costume._dirty = 0

        with patch.object(
            actor.costume, "update", wraps=actor.costume.update
        ) as update_mock:
            self.manager._update_all_costumes()

        update_mock.assert_called_once()

    def test_dirty_dynamic_actor_costume_is_updated(self):
        actor = self._create_actor()
        actor.costume._is_animated = False
        actor.costume._dirty = 1

        with patch.object(
            actor.costume, "update", wraps=actor.costume.update
        ) as update_mock:
            self.manager._update_all_costumes()

        update_mock.assert_called_once()

    def test_actor_without_costume_is_skipped(self):
        actor = self._create_actor()
        # Simulate a missing costume without breaking the actor lifecycle.
        actor._costume_manager._costume = None
        actor._costume_manager._appearance = None

        # Must not raise AttributeError.
        self.manager._update_all_costumes()


if __name__ == "__main__":
    unittest.main()
