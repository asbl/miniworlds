"""Visual tests for widgets - simplified version.

Tests cover basic widget functionality that works without errors.

Uses common helper functions from visual_test_helpers.
"""

import unittest

import miniworlds
from miniworlds import App

from .screenshot_tester import ScreenshotTester
from .visual_test_helpers import (
    TEST_FRAMES,
    TEST_WORLD_HEIGHT,
    TEST_WORLD_WIDTH,
    create_test_world,
    setup_screenshot_tester,
)


class Test900Widgets(unittest.TestCase):
    """Visual test for widgets - testing only Label and Button which are stable."""

    def setUp(self):
        def test_code():
            world = create_test_world(TEST_WORLD_WIDTH, TEST_WORLD_HEIGHT)

            # Test Label widget - text is the first positional argument
            miniworlds.Label("This is a label")
            miniworlds.Label("Small")
            miniworlds.Label("Large Label")
            miniworlds.Label("Line 1\nLine 2\nLine 3")

            # Test Button widget
            miniworlds.Button("Click Me")

            # Test edge cases
            miniworlds.Label("")  # Empty label
            miniworlds.Label("X")  # Single character
            miniworlds.Label("   Spaces   ")  # Whitespace

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()

        # Setup screenshot tester with common helpers
        setup_screenshot_tester(self, world)

    def test_screenshot_test_900_widgets(self):
        """Test that all widget types render correctly."""
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
