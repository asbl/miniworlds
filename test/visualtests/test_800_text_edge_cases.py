"""Visual tests for text edge cases.

Tests cover:
- Text with various fonts and sizes
- Multi-line text
- Special characters (umlauts, symbols)
- Text rotation
- Empty text
- Text with transparency

Uses common helper functions from visual_test_helpers.
"""

import unittest

import miniworlds
from miniworlds import App

from .screenshot_tester import ScreenshotTester
from .visual_test_helpers import (
    BLACK,
    BLUE,
    GREEN,
    RED,
    TEST_FRAMES,
    TEST_WORLD_HEIGHT,
    TEST_WORLD_WIDTH,
    create_test_world,
    create_text_at,
    setup_screenshot_tester,
)


class Test800TextEdgeCases(unittest.TestCase):
    """Visual test for text edge cases."""

    def setUp(self):
        def test_code():
            world = create_test_world(TEST_WORLD_WIDTH, TEST_WORLD_HEIGHT)

            # Test normal text
            create_text_at((50, 50), text="Hello World", font_size=24, color=BLACK)

            # Test text with different font sizes
            create_text_at(
                (50, 100), text="Small Text", font_size=10, color=(100, 100, 100)
            )
            create_text_at(
                (50, 130), text="Large Text", font_size=48, color=(50, 50, 50)
            )
            create_text_at(
                (50, 180), text="Huge Text", font_size=72, color=(25, 25, 25)
            )

            # Test multi-line text
            create_text_at(
                (50, 280),
                text="Line 1\nLine 2\nLine 3\nLine 4",
                font_size=20,
                color=BLACK,
            )

            # Test special characters (umlauts)
            create_text_at((300, 50), text="Ä Ö Ü ä ö ü ß", font_size=24, color=RED)

            # Test special symbols
            create_text_at(
                (300, 100), text="!@#$%^&*()_+-={}[]", font_size=18, color=(0, 150, 0)
            )

            # Test long text with wrapping
            long_text = "This is a very long text that should wrap"
            create_text_at(
                (50, 350), text=long_text, font_size=16, color=(100, 50, 0), width=250
            )

            # Test empty text
            create_text_at((50, 450), text="", font_size=20, color=(200, 200, 200))

            # Test text with single character
            create_text_at((50, 480), text="X", font_size=36, color=RED)

            # Test text with whitespace
            create_text_at(
                (350, 450), text="   Spaces   ", font_size=20, color=(0, 100, 100)
            )

            # Test text with different colors
            create_text_at((50, 550), text="Red Text", font_size=20, color=RED)
            create_text_at((200, 550), text="Green Text", font_size=20, color=GREEN)
            create_text_at((350, 550), text="Blue Text", font_size=20, color=BLUE)

            # Test text with transparency
            create_text_at(
                (50, 580), text="Semi-Transparent", font_size=20, color=(255, 0, 0, 128)
            )

            # Test text rotation
            text_rotated = miniworlds.Text(
                (600, 100), text="Rotated 45", font_size=24, color=BLACK
            )
            text_rotated.direction = 45

            text_rotated_90 = miniworlds.Text(
                (600, 200), text="Rotated 90", font_size=24, color=BLACK
            )
            text_rotated_90.direction = 90

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()

        # Setup screenshot tester with common helpers
        setup_screenshot_tester(self, world)

    def test_screenshot_test_800_text_edge_cases(self):
        """Test that all text edge cases render correctly."""
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
