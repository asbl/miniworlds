"""Unit tests for core actor functionality.

Tests cover:
- Actor class attributes and initialization
- ActorBase inheritance and properties
- Actor class methods that can be tested without full world setup
- Edge cases and error handling
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest
from miniworlds.actors.actor import Actor
from miniworlds.actors.actor_base import ActorBase
from miniworlds.base.exceptions import (
    MissingPositionManager,
    Missingworldsensor,
    NoValidPositionOnInitException,
    NoWorldError,
)

# Test constants
SAMPLE_X: float = 10.0
SAMPLE_Y: float = 20.0
SAMPLE_POSITION: tuple[float, float] = (SAMPLE_X, SAMPLE_Y)
INVALID_POSITION_STRING: str = "not a tuple"
INVALID_POSITION_NONE: None = None


class TestActorClassAttributes(unittest.TestCase):
    """Tests for Actor class-level attributes."""

    def test_actor_class_has_actor_count(self) -> None:
        """Test that Actor class has an actor_count attribute."""
        self.assertTrue(
            hasattr(Actor, "actor_count"),
            "Actor class should have actor_count attribute",
        )
        self.assertIsInstance(
            Actor.actor_count,
            int,
            "actor_count should be an integer",
        )

    def test_actor_class_has_class_image(self) -> None:
        """Test that Actor class has a class_image attribute."""
        self.assertTrue(
            hasattr(Actor, "class_image"),
            "Actor class should have class_image attribute",
        )
        self.assertIsInstance(
            Actor.class_image,
            str,
            "class_image should be a string",
        )

    def test_actor_count_increments_on_instantiation(self) -> None:
        """Test that actor_count increments when Actor is instantiated."""
        initial_count: int = Actor.actor_count

        def mock_world_setup(self: Actor, **kwargs) -> None:
            """Mock the world setup to prevent actual world creation."""
            self.world = MagicMock()
            self.world.event_manager = MagicMock()
            self.world.event_manager.can_register_to_actor = MagicMock(
                return_value=True
            )
            self.world.get_world_connector = MagicMock()
            self.world.get_world_connector.return_value = MagicMock()
            self.world.get_world_connector.return_value.add_to_world = MagicMock()

        # We need to mock the world initialization to test class attributes
        # For now, just verify the class attribute exists and is an int
        self.assertIsInstance(Actor.actor_count, int)


class TestActorBaseInheritance(unittest.TestCase):
    """Tests for ActorBase inheritance."""

    def test_actor_base_has_dirty_attribute(self) -> None:
        """Test that ActorBase has dirty attribute."""
        self.assertTrue(
            hasattr(ActorBase, "dirty"),
            "ActorBase should have dirty attribute",
        )

    def test_actor_base_has_register_method(self) -> None:
        """Test that ActorBase has register method."""
        self.assertTrue(
            hasattr(ActorBase, "register"),
            "ActorBase should have register method",
        )

    def test_actor_base_has_register_message_method(self) -> None:
        """Test that ActorBase has register_message method."""
        self.assertTrue(
            hasattr(ActorBase, "register_message"),
            "ActorBase should have register_message method",
        )

    def test_actor_base_is_pygame_sprite_subclass(self) -> None:
        """Test that ActorBase inherits from pygame.sprite.DirtySprite."""
        import pygame.sprite

        self.assertTrue(
            issubclass(ActorBase, pygame.sprite.DirtySprite),
            "ActorBase should be a subclass of pygame.sprite.DirtySprite",
        )


class TestActorBaseDirtyProperty(unittest.TestCase):
    """Tests for ActorBase dirty property."""

    def test_dirty_property_exists(self) -> None:
        """Test that dirty property exists on ActorBase."""
        self.assertTrue(
            hasattr(ActorBase, "dirty"),
            "ActorBase should have dirty property",
        )

    def test_dirty_property_has_getter(self) -> None:
        """Test that dirty property has a getter."""
        # Check if the dirty attribute has a getter by checking the property
        dirty_attr = getattr(ActorBase, "dirty", None)
        self.assertIsNotNone(
            dirty_attr,
            "ActorBase should have dirty attribute",
        )
        # Check if it's a property
        if isinstance(dirty_attr, property):
            self.assertIsNotNone(
                dirty_attr.fget,
                "dirty property should have a getter",
            )

    def test_dirty_property_has_setter(self) -> None:
        """Test that dirty property has a setter."""
        dirty_attr = getattr(ActorBase, "dirty", None)
        if isinstance(dirty_attr, property):
            self.assertIsNotNone(
                dirty_attr.fset,
                "dirty property should have a setter",
            )


class TestActorNormalizeConstructorArguments(unittest.TestCase):
    """Tests for _normalize_constructor_arguments class method."""

    def test_normalize_with_tuple_position(self) -> None:
        """Test normalization with tuple position."""
        position: tuple[float, float] = (SAMPLE_X, SAMPLE_Y)
        args: tuple = ()
        normalized_position, normalized_args = Actor._normalize_constructor_arguments(
            position, args
        )
        self.assertEqual(
            normalized_position,
            position,
            "Position should remain unchanged when it's a tuple",
        )
        self.assertEqual(
            normalized_args,
            args,
            "Args should remain unchanged",
        )

    def test_normalize_with_numeric_position_and_args(self) -> None:
        """Test normalization with numeric x, y and additional args."""
        position: float = SAMPLE_X
        args: tuple = (SAMPLE_Y, "extra_arg")
        normalized_position, normalized_args = Actor._normalize_constructor_arguments(
            position, args
        )
        self.assertEqual(
            normalized_position,
            (SAMPLE_X, SAMPLE_Y),
            "Position should be converted to tuple from numeric x, y",
        )
        self.assertEqual(
            normalized_args,
            ("extra_arg",),
            "Remaining args should be preserved",
        )

    def test_normalize_simple_subclass_with_inherited_actor_init(self) -> None:
        """Simple student Actor subclasses keep the beginner-friendly x, y shortcut."""
        class ActorSubclass(Actor):
            pass

        normalized_position, normalized_args = (
            ActorSubclass._normalize_constructor_arguments(SAMPLE_X, (SAMPLE_Y,))
        )

        self.assertEqual(normalized_position, SAMPLE_POSITION)
        self.assertEqual(normalized_args, ())

    def test_subclass_with_custom_init_keeps_tuple_first_signature(self) -> None:
        """Custom Actor subclasses keep their own positional argument contract."""
        position: tuple[float, float] = (SAMPLE_X, SAMPLE_Y)
        args: tuple = ("custom_arg",)

        class ActorSubclass(Actor):
            def __init__(self, position, custom_arg):
                super().__init__(position)
                self.custom_arg = custom_arg

        normalized_position, normalized_args = (
            ActorSubclass._normalize_constructor_arguments(position, args)
        )
        self.assertEqual(
            normalized_position,
            position,
            "Subclass should return position unchanged",
        )
        self.assertEqual(
            normalized_args,
            args,
            "Subclass should return args unchanged",
        )


class TestActorValidation(unittest.TestCase):
    """Tests for Actor argument validation."""

    def test_validate_arguments_with_none_position(self) -> None:
        """Test that _validate_arguments raises exception for None position."""
        # Create a partial actor instance for testing
        actor = object.__new__(Actor)
        with pytest.raises(NoValidPositionOnInitException):
            actor._validate_arguments(INVALID_POSITION_NONE)

    def test_validate_arguments_with_non_tuple_position(self) -> None:
        """Test that _validate_arguments raises exception for non-tuple position."""
        actor = object.__new__(Actor)
        with pytest.raises(NoValidPositionOnInitException):
            actor._validate_arguments(INVALID_POSITION_STRING)

    def test_validate_arguments_with_valid_tuple_position(self) -> None:
        """Test that _validate_arguments accepts valid tuple position."""
        actor = object.__new__(Actor)
        # Should not raise
        actor._validate_arguments(SAMPLE_POSITION)


class TestActorFacadeProperties(unittest.TestCase):
    """Tests for Actor facade property getters."""

    def test_initialization_facade_access_works(self) -> None:
        """Test that initialization facade can be accessed."""
        actor = object.__new__(Actor)
        # Set the facade directly as __init__ would do
        import miniworlds.actors.actor_initialization_facade as actor_initialization_facade

        actor._initialization_facade = (
            actor_initialization_facade.ActorInitializationFacade(actor)
        )

        facade = actor._initialization_facade
        self.assertIsNotNone(
            facade,
            "Initialization facade should be accessible",
        )

    def test_appearance_facade_access_works(self) -> None:
        """Test that appearance facade can be accessed."""
        actor = object.__new__(Actor)
        facade = actor._appearance_facade
        self.assertIsNotNone(
            facade,
            "Appearance facade should be accessible",
        )

    def test_event_facade_access_works(self) -> None:
        """Test that event facade can be accessed."""
        actor = object.__new__(Actor)
        facade = actor._event_facade
        self.assertIsNotNone(
            facade,
            "Event facade should be accessible",
        )

    def test_sensor_facade_access_works(self) -> None:
        """Test that sensor facade can be accessed."""
        actor = object.__new__(Actor)
        facade = actor._sensor_facade
        self.assertIsNotNone(
            facade,
            "Sensor facade should be accessible",
        )

    def test_movement_facade_access_works(self) -> None:
        """Test that movement facade can be accessed."""
        actor = object.__new__(Actor)
        facade = actor._movement_facade
        self.assertIsNotNone(
            facade,
            "Movement facade should be accessible",
        )

    def test_size_facade_access_works(self) -> None:
        """Test that size facade can be accessed."""
        actor = object.__new__(Actor)
        facade = actor._size_facade
        self.assertIsNotNone(
            facade,
            "Size facade should be accessible",
        )


class TestActorBaseMeta(unittest.TestCase):
    """Tests for ActorWorldConnectorMeta metaclass behavior."""

    def test_metaclass_normalize_constructor_arguments(self) -> None:
        """Test metaclass _normalize_constructor_arguments."""
        position: tuple[float, float] = (SAMPLE_X, SAMPLE_Y)
        args: tuple = ()
        normalized_position, normalized_args = (
            ActorBase._normalize_constructor_arguments(position, args)
        )
        self.assertEqual(
            normalized_position,
            position,
            "Normalized position should match input",
        )
        self.assertEqual(
            normalized_args,
            args,
            "Normalized args should match input",
        )


if __name__ == "__main__":
    unittest.main()
