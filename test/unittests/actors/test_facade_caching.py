"""Unit tests for facade caching with @cached_property.

Tests cover:
- Facades are cached and reused (except initialization_facade which is set in __init__)
- Facade instances are created only once
- Multiple accesses return the same instance
- Facade functionality remains unchanged
"""

import unittest

from miniworlds.actors.actor import Actor
from miniworlds.worlds.world import World


class TestActorFacadeCaching(unittest.TestCase):
    """Tests for @cached_property on Actor facades."""

    def setUp(self):
        """Set up test fixtures."""
        self.world = World(100, 100)
        self.actor = Actor((50, 50), world=self.world)

    def test_initialization_facade_is_set_in_init(self):
        """Test that _initialization_facade is set during __init__."""
        # Initialization facade is set directly in __init__, not via cached_property
        facade = self.actor._initialization_facade
        self.assertIsNotNone(
            facade, "Initialization facade should be set during __init__"
        )

    def test_appearance_facade_is_cached(self):
        """Test that _appearance_facade is cached."""
        facade1 = self.actor._appearance_facade
        facade2 = self.actor._appearance_facade

        self.assertIs(facade1, facade2, "Appearance facade should be cached")

    def test_event_facade_is_cached(self):
        """Test that _event_facade is cached."""
        facade1 = self.actor._event_facade
        facade2 = self.actor._event_facade

        self.assertIs(facade1, facade2, "Event facade should be cached")

    def test_sensor_facade_is_cached(self):
        """Test that _sensor_facade is cached."""
        facade1 = self.actor._sensor_facade
        facade2 = self.actor._sensor_facade

        self.assertIs(facade1, facade2, "Sensor facade should be cached")

    def test_movement_facade_is_cached(self):
        """Test that _movement_facade is cached."""
        facade1 = self.actor._movement_facade
        facade2 = self.actor._movement_facade

        self.assertIs(facade1, facade2, "Movement facade should be cached")

    def test_size_facade_is_cached(self):
        """Test that _size_facade is cached."""
        facade1 = self.actor._size_facade
        facade2 = self.actor._size_facade

        self.assertIs(facade1, facade2, "Size facade should be cached")

    def test_all_facades_are_separate_instances(self):
        """Test that different facades are different instances."""
        init_facade = self.actor._initialization_facade
        appearance_facade = self.actor._appearance_facade
        movement_facade = self.actor._movement_facade

        # Each facade type should be a different instance
        self.assertIsNot(init_facade, appearance_facade)
        self.assertIsNot(init_facade, movement_facade)
        self.assertIsNot(appearance_facade, movement_facade)


class TestWorldFacadeCaching(unittest.TestCase):
    """Tests for @cached_property on World facades."""

    def setUp(self):
        """Set up test fixtures."""
        self.world = World(100, 100)

    def test_initialization_facade_is_set_in_init(self):
        """Test that _initialization_facade is set during __init__."""
        # Initialization facade is set directly in __init__, not via cached_property
        facade = self.world._initialization_facade
        self.assertIsNotNone(
            facade, "World initialization facade should be set during __init__"
        )

    def test_background_facade_is_cached(self):
        """Test that _background_facade is cached on World."""
        facade1 = self.world._background_facade
        facade2 = self.world._background_facade

        self.assertIs(facade1, facade2, "World background facade should be cached")

    def test_runtime_facade_is_cached(self):
        """Test that _runtime_facade is cached on World."""
        facade1 = self.world._runtime_facade
        facade2 = self.world._runtime_facade

        self.assertIs(facade1, facade2, "World runtime facade should be cached")


class TestFacadeFunctionalityPreserved(unittest.TestCase):
    """Tests that facade functionality remains unchanged after caching."""

    def setUp(self):
        """Set up test fixtures."""
        self.world = World(100, 100)
        self.actor = Actor((50, 50), world=self.world)

    def test_actor_x_property_works(self):
        """Test that actor.x property works through cached movement facade."""
        self.actor.x = 10
        self.assertEqual(self.actor.x, 10)

        self.actor.x = 20
        self.assertEqual(self.actor.x, 20)

    def test_actor_y_property_works(self):
        """Test that actor.y property works through cached movement facade."""
        self.actor.y = 30
        self.assertEqual(self.actor.y, 30)

    def test_actor_direction_property_works(self):
        """Test that actor.direction property works through cached movement facade."""
        self.actor.direction = 90
        self.assertEqual(self.actor.direction, 90)

        self.actor.direction = "left"
        self.assertEqual(self.actor.direction, -90)

    def test_actor_size_property_works(self):
        """Test that actor.size property works through cached size facade."""
        self.actor.size = (20, 30)
        self.assertEqual(self.actor.size, (20, 30))

    def test_actor_origin_property_works(self):
        """Test that actor.origin property works through cached size facade."""
        self.actor.origin = "center"
        self.assertEqual(self.actor.origin, "center")

    def test_actor_costume_property_works(self):
        """Test that actor.costume property works through cached appearance facade."""
        # Accessing costume should work
        costume = self.actor.costume
        # May be None if no costume is set
        self.assertIsInstance(costume, (type(None), object))

    def test_actor_detect_with_none_works(self):
        """Test that actor.detect() works through cached sensor facade."""
        # This should not raise an error
        result = self.actor.detect(None)
        # Result may be None or an actor, but the method should work
        self.assertIsInstance(result, (type(None), object))


class TestMultipleActorsFacadeIsolation(unittest.TestCase):
    """Tests that each actor has its own cached facade instances."""

    def setUp(self):
        """Set up test fixtures."""
        self.world = World(100, 100)

    def test_each_actor_has_own_movement_facade(self):
        """Test that each actor gets its own movement facade instance."""
        actor1 = Actor((10, 10), world=self.world)
        actor2 = Actor((20, 20), world=self.world)

        facade1 = actor1._movement_facade
        facade2 = actor2._movement_facade

        # Different actors should have different facade instances
        self.assertIsNot(
            facade1, facade2, "Each actor should have its own movement facade"
        )

    def test_each_actor_has_own_appearance_facade(self):
        """Test that each actor gets its own appearance facade instance."""
        actor1 = Actor((10, 10), world=self.world)
        actor2 = Actor((20, 20), world=self.world)

        facade1 = actor1._appearance_facade
        facade2 = actor2._appearance_facade

        self.assertIsNot(
            facade1, facade2, "Each actor should have its own appearance facade"
        )

    def test_each_actor_has_own_event_facade(self):
        """Test that each actor gets its own event facade instance."""
        actor1 = Actor((10, 10), world=self.world)
        actor2 = Actor((20, 20), world=self.world)

        facade1 = actor1._event_facade
        facade2 = actor2._event_facade

        self.assertIsNot(
            facade1, facade2, "Each actor should have its own event facade"
        )

    def test_each_world_has_own_background_facade(self):
        """Test that each world gets its own background facade instance."""
        world1 = World(100, 100)
        world2 = World(200, 200)

        facade1 = world1._background_facade
        facade2 = world2._background_facade

        self.assertIsNot(
            facade1, facade2, "Each world should have its own background facade"
        )


class TestSlotsOptimization(unittest.TestCase):
    """Tests for __slots__ memory optimization."""

    def test_actor_has_slots(self):
        """Test that Actor class has __slots__ defined."""
        self.assertTrue(
            hasattr(Actor, "__slots__"), "Actor should have __slots__ defined"
        )
        self.assertIsInstance(Actor.__slots__, tuple, "__slots__ should be a tuple")

    def test_actor_base_has_slots(self):
        """Test that ActorBase class has __slots__ defined."""
        from miniworlds.actors.actor_base import ActorBase

        self.assertTrue(
            hasattr(ActorBase, "__slots__"), "ActorBase should have __slots__ defined"
        )

    def test_world_base_has_slots(self):
        """Test that WorldBase class has __slots__ defined."""
        from miniworlds.worlds.world_base import WorldBase

        self.assertTrue(
            hasattr(WorldBase, "__slots__"), "WorldBase should have __slots__ defined"
        )

    def test_world_has_slots(self):
        """Test that World class has __slots__ defined."""
        self.assertTrue(
            hasattr(World, "__slots__"), "World should have __slots__ defined"
        )

    def test_appearance_has_slots(self):
        """Test that Appearance class has __slots__ defined."""
        from miniworlds.appearances.appearance import Appearance

        self.assertTrue(
            hasattr(Appearance, "__slots__"), "Appearance should have __slots__ defined"
        )

    def test_actor_allows_dynamic_attributes(self):
        """Test that Actor allows dynamic attributes (via inherited __dict__)."""
        world = World(100, 100)
        actor = Actor((50, 50), world=world)

        # Should be able to add dynamic attributes
        actor.health = 100
        actor.score = 50

        self.assertEqual(actor.health, 100)
        self.assertEqual(actor.score, 50)

    def test_actor_slots_contains_core_attributes(self):
        """Test that Actor __slots__ contains core attributes."""
        expected_slots = {
            "_initialization_facade",
            "_collision_type",
            "_layer",
            "_world",
            "_static",
        }
        actual_slots = set(Actor.__slots__)

        for slot in expected_slots:
            self.assertIn(slot, actual_slots, f"Actor.__slots__ should contain {slot}")

    def test_world_slots_contains_core_attributes(self):
        """Test that World __slots__ contains core attributes."""
        expected_slots = {
            "_initialization_facade",
            "_debug",
            "_learning_mode",
            "_active_dialog",
            "dialog",
        }
        actual_slots = set(World.__slots__)

        for slot in expected_slots:
            self.assertIn(slot, actual_slots, f"World.__slots__ should contain {slot}")


if __name__ == "__main__":
    unittest.main()
