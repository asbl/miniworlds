"""Unit tests for miniworlds.positions.rect module.

Tests cover:
- Rect creation from various inputs
- Rect class methods
- Edge cases and error handling
- Inheritance from pygame.Rect
- Direct construction scenarios
- Actor-based Rect creation

Test constants for common values used in tests.
"""

import unittest

import pygame
import pytest
from miniworlds.base.exceptions import NoValidWorldRectError
from miniworlds.positions.rect import Rect

# Test constants for position values
SAMPLE_X: int = 10
SAMPLE_Y: int = 20
SAMPLE_WIDTH: int = 30
SAMPLE_HEIGHT: int = 40

# Test constants for edge case values
NEGATIVE_WIDTH: int = -30
NEGATIVE_HEIGHT: int = -40
ZERO: int = 0
LARGE_DIMENSION: int = 1000000
FLOAT_X: float = 10.5
FLOAT_Y: float = 20.3
FLOAT_WIDTH: float = 30.7
FLOAT_HEIGHT: float = 40.2


class TestRectCreation(unittest.TestCase):
    """Tests for Rect.create class method."""

    def test_create_from_2_tuple(self) -> None:
        """Test creating Rect from 2-element tuple (x, y) - creates 1x1 rect."""
        rect: Rect = Rect.create((SAMPLE_X, SAMPLE_Y))
        self.assertEqual(
            rect.x,
            SAMPLE_X,
            "Rect x coordinate should match input x",
        )
        self.assertEqual(
            rect.y,
            SAMPLE_Y,
            "Rect y coordinate should match input y",
        )
        # Rect.create always creates 1x1 rects from tuples
        self.assertEqual(
            rect.width,
            1,
            "Rect.create from tuple should have width of 1",
        )
        self.assertEqual(
            rect.height,
            1,
            "Rect.create from tuple should have height of 1",
        )

    def test_create_from_4_tuple(self) -> None:
        """Test creating Rect from 4-element tuple - still creates 1x1 rect."""
        # Note: Rect.create() always creates 1x1 from tuples, regardless of tuple length
        rect: Rect = Rect.create((SAMPLE_X, SAMPLE_Y, SAMPLE_WIDTH, SAMPLE_HEIGHT))
        self.assertEqual(
            rect.x,
            SAMPLE_X,
            "Rect x coordinate should match first tuple element",
        )
        self.assertEqual(
            rect.y,
            SAMPLE_Y,
            "Rect y coordinate should match second tuple element",
        )
        # Width and height are ignored for tuples - always 1x1
        self.assertEqual(
            rect.width,
            1,
            "Rect.create from 4-tuple should have width of 1",
        )
        self.assertEqual(
            rect.height,
            1,
            "Rect.create from 4-tuple should have height of 1",
        )

    def test_create_from_pygame_rect(self) -> None:
        """Test creating Rect from pygame.Rect - preserves dimensions."""
        pg_rect: pygame.Rect = pygame.Rect(
            SAMPLE_X, SAMPLE_Y, SAMPLE_WIDTH, SAMPLE_HEIGHT
        )
        rect: Rect = Rect.create(pg_rect)
        self.assertEqual(
            rect.x,
            SAMPLE_X,
            "Rect x should match pygame.Rect x",
        )
        self.assertEqual(
            rect.y,
            SAMPLE_Y,
            "Rect y should match pygame.Rect y",
        )
        self.assertEqual(
            rect.width,
            SAMPLE_WIDTH,
            "Rect width should match pygame.Rect width",
        )
        self.assertEqual(
            rect.height,
            SAMPLE_HEIGHT,
            "Rect height should match pygame.Rect height",
        )

    def test_create_invalid_type_string(self) -> None:
        """Test that create raises NoValidWorldRectError for string input."""
        with pytest.raises(NoValidWorldRectError):
            Rect.create("invalid")

    def test_create_invalid_type_list(self) -> None:
        """Test that create raises NoValidWorldRectError for list input."""
        with pytest.raises(NoValidWorldRectError):
            Rect.create(
                [SAMPLE_X, SAMPLE_Y, SAMPLE_WIDTH, SAMPLE_HEIGHT]
            )  # List instead of tuple

    def test_create_invalid_type_none(self) -> None:
        """Test that create raises NoValidWorldRectError for None input."""
        with pytest.raises(NoValidWorldRectError):
            Rect.create(None)


class TestRectInheritance(unittest.TestCase):
    """Tests for Rect inheritance from pygame.Rect."""

    def test_rect_is_pygame_rect_subclass(self) -> None:
        """Test that Rect is a subclass of pygame.Rect."""
        self.assertTrue(
            issubclass(Rect, pygame.Rect),
            "Rect should be a subclass of pygame.Rect",
        )

    def test_rect_has_pygame_rect_attributes(self) -> None:
        """Test that Rect has all pygame.Rect attributes."""
        rect: Rect = Rect.create((SAMPLE_X, SAMPLE_Y))
        # Check standard pygame.Rect attributes
        expected_attributes: list[str] = [
            "x",
            "y",
            "width",
            "height",
            "topleft",
            "bottomright",
            "center",
        ]
        for attr in expected_attributes:
            self.assertTrue(
                hasattr(rect, attr),
                f"Rect should have attribute '{attr}'",
            )

    def test_rect_pygame_rect_methods(self) -> None:
        """Test that Rect supports pygame.Rect methods."""
        # Create rects with actual dimensions using pygame.Rect constructor
        rect1: Rect = Rect(SAMPLE_X, SAMPLE_Y, SAMPLE_WIDTH, SAMPLE_HEIGHT)
        rect2: Rect = Rect(SAMPLE_X + 25, SAMPLE_Y + 25, SAMPLE_WIDTH, SAMPLE_HEIGHT)

        # Test collision detection
        self.assertTrue(
            rect1.colliderect(rect2),
            "Rects should collide when overlapping",
        )

        # Test contains
        self.assertTrue(
            rect1.collidepoint(SAMPLE_X + 10, SAMPLE_Y + 10),
            "Rect should contain interior point",
        )
        self.assertFalse(
            rect1.collidepoint(
                SAMPLE_X + SAMPLE_WIDTH + 100, SAMPLE_Y + SAMPLE_HEIGHT + 100
            ),
            "Rect should not contain exterior point",
        )


class TestRectDirectConstruction(unittest.TestCase):
    """Tests for direct Rect construction (not using create class method)."""

    def test_direct_construction_with_dimensions(self) -> None:
        """Test creating Rect directly with x, y, width, height."""
        rect: Rect = Rect(SAMPLE_X, SAMPLE_Y, SAMPLE_WIDTH, SAMPLE_HEIGHT)
        self.assertEqual(
            rect.x,
            SAMPLE_X,
            "Rect x should match input x",
        )
        self.assertEqual(
            rect.y,
            SAMPLE_Y,
            "Rect y should match input y",
        )
        self.assertEqual(
            rect.width,
            SAMPLE_WIDTH,
            "Rect width should match input width",
        )
        self.assertEqual(
            rect.height,
            SAMPLE_HEIGHT,
            "Rect height should match input height",
        )

    def test_direct_construction_with_negative_dimensions(self) -> None:
        """Test creating Rect directly with negative dimensions."""
        # Note: pygame.Rect can have negative dimensions (they're not normalized to 0)
        rect: Rect = Rect(SAMPLE_X, SAMPLE_Y, NEGATIVE_WIDTH, NEGATIVE_HEIGHT)
        # pygame.Rect preserves negative dimensions
        self.assertEqual(
            rect.width,
            NEGATIVE_WIDTH,
            "Rect width should preserve negative value",
        )
        self.assertEqual(
            rect.height,
            NEGATIVE_HEIGHT,
            "Rect height should preserve negative value",
        )

    def test_direct_construction_with_zero_dimensions(self) -> None:
        """Test creating Rect directly with zero dimensions."""
        rect: Rect = Rect(SAMPLE_X, SAMPLE_Y, ZERO, ZERO)
        self.assertEqual(
            rect.width,
            ZERO,
            "Rect width should be 0",
        )
        self.assertEqual(
            rect.height,
            ZERO,
            "Rect height should be 0",
        )

    def test_direct_construction_with_very_large_dimensions(self) -> None:
        """Test creating Rect directly with very large dimensions."""
        rect: Rect = Rect(ZERO, ZERO, LARGE_DIMENSION, LARGE_DIMENSION)
        self.assertEqual(
            rect.width,
            LARGE_DIMENSION,
            "Rect width should handle large values",
        )
        self.assertEqual(
            rect.height,
            LARGE_DIMENSION,
            "Rect height should handle large values",
        )

    def test_direct_construction_with_float_dimensions(self) -> None:
        """Test creating Rect directly with float dimensions (should be converted to int)."""
        rect: Rect = Rect(FLOAT_X, FLOAT_Y, FLOAT_WIDTH, FLOAT_HEIGHT)
        # pygame.Rect converts floats to ints
        self.assertEqual(
            rect.x,
            int(FLOAT_X),
            "Rect x should convert float to int",
        )
        self.assertEqual(
            rect.y,
            int(FLOAT_Y),
            "Rect y should convert float to int",
        )
        self.assertEqual(
            rect.width,
            int(FLOAT_WIDTH),
            "Rect width should convert float to int",
        )
        self.assertEqual(
            rect.height,
            int(FLOAT_HEIGHT),
            "Rect height should convert float to int",
        )


class TestRectFromActor(unittest.TestCase):
    """Tests for Rect.from_actor class method."""

    def test_from_actor_requires_actor_with_get_global_rect(self) -> None:
        """Test that from_actor requires an actor with get_global_rect method."""

        # Create a mock actor
        class MockActor:
            def get_global_rect(self) -> pygame.Rect:
                """Mock get_global_rect method."""
                return pygame.Rect(SAMPLE_X, SAMPLE_Y, SAMPLE_WIDTH, SAMPLE_HEIGHT)

        mock_actor: MockActor = MockActor()
        rect: Rect = Rect.from_actor(mock_actor)

        self.assertEqual(
            rect.x,
            SAMPLE_X,
            "Rect x should match actor's rect x",
        )
        self.assertEqual(
            rect.y,
            SAMPLE_Y,
            "Rect y should match actor's rect y",
        )
        self.assertEqual(
            rect.width,
            SAMPLE_WIDTH,
            "Rect width should match actor's rect width",
        )
        self.assertEqual(
            rect.height,
            SAMPLE_HEIGHT,
            "Rect height should match actor's rect height",
        )


if __name__ == "__main__":
    unittest.main()
