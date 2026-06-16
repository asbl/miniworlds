"""Visual tests for shapes edge cases.

Tests cover:
- All shape types (Circle, Rectangle, Line, Triangle, Ellipse)
- Edge cases: zero size, negative size, very large size
- Position edge cases
- Color edge cases
- Origin switching
- Fill vs outline

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
    MAGENTA,
    RED,
    TEST_FRAMES,
    TEST_WORLD_HEIGHT,
    TEST_WORLD_WIDTH,
    create_circle_at,
    create_line_between,
    create_rectangle_at,
    create_test_world,
    setup_screenshot_tester,
)


class Test750ShapesEdgeCases(unittest.TestCase):
    """Visual test for shapes edge cases."""

    def setUp(self):
        def test_code():
            world = create_test_world(TEST_WORLD_WIDTH, TEST_WORLD_HEIGHT)

            # Test Circle edge cases
            create_circle_at((100, 100), radius=50, color=RED)
            create_circle_at((100, 200), radius=1, color=GREEN)
            create_circle_at((100, 350), radius=80, color=BLUE)
            create_circle_at((100, 450), radius=0, color=MAGENTA)

            # Test Rectangle edge cases
            create_rectangle_at((250, 100), width=100, height=50, color=(255, 165, 0))
            create_rectangle_at((250, 200), width=100, height=1, color=(0, 255, 255))
            create_rectangle_at((250, 250), width=300, height=20, color=(128, 0, 128))
            create_rectangle_at((250, 350), width=50, height=50, color=(255, 192, 203))

            # Test Line edge cases
            create_line_between((450, 100), (550, 150), width=3, color=BLACK)
            create_line_between((450, 200), (650, 200), width=2, color=RED)
            create_line_between((450, 250), (450, 350), width=2, color=GREEN)
            create_line_between((450, 400), (450, 400), width=2, color=BLUE)
            create_line_between((450, 450), (600, 550), width=2, color=(255, 255, 0))

            # Test Triangle edge cases
            create_triangle_at((650, 100), (700, 50), (750, 100), color=(0, 128, 0))
            create_triangle_at((650, 200), (700, 200), (750, 200), color=(128, 128, 0))
            create_triangle_at((650, 250), (660, 250), (655, 260), color=(0, 128, 128))

            # Test Ellipse edge cases
            create_ellipse_at((100, 500), width=50, height=50, color=MAGENTA)
            create_ellipse_at((250, 500), width=100, height=30, color=GREEN)
            create_ellipse_at((400, 500), width=30, height=80, color=BLUE)
            create_ellipse_at((550, 500), width=40, height=2, color=ORANGE)

            # Test origin switching
            circle_center = miniworlds.Circle(
                (300, 400), radius=30, color=(100, 100, 200)
            )
            circle_center.switch_origin("center")
            circle_center.center = (300, 400)

            rect_center = miniworlds.Rectangle(
                (300, 450), width=60, height=40, color=(200, 100, 100)
            )
            rect_center.switch_origin("center")
            rect_center.center = (300, 450)

            # Test transparency
            miniworlds.Circle((500, 400), radius=40, color=(255, 0, 0, 128))

            # Test fill vs outline
            filled_circle = miniworlds.Circle((500, 450), radius=35, color=GREEN)
            filled_circle.fill = True

            outlined_rect = miniworlds.Rectangle(
                (600, 400), width=50, height=50, color=BLUE
            )
            outlined_rect.fill = False

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()

        # Setup screenshot tester with common helpers
        setup_screenshot_tester(self, world)

    def test_screenshot_test_750_shapes_edge_cases(self):
        """Test that all shape edge cases render correctly."""
        with self.assertRaises(SystemExit):
            self.world.run()


# Helper functions defined locally for this module
# (These could be moved to visual_test_helpers if needed elsewhere)
def create_triangle_at(
    pos1: tuple[int, int],
    pos2: tuple[int, int],
    pos3: tuple[int, int],
    color: tuple[int, int, int] = (0, 0, 0),
    **kwargs,
) -> miniworlds.Triangle:
    """Create a triangle actor at the specified positions."""
    return miniworlds.Triangle(pos1, pos2, pos3, color=color, **kwargs)


def create_ellipse_at(
    position: tuple[int, int],
    width: int = 50,
    height: int = 50,
    color: tuple[int, int, int] = (0, 0, 0),
    **kwargs,
) -> miniworlds.Ellipse:
    """Create an ellipse actor at the specified position."""
    return miniworlds.Ellipse(
        position, width=width, height=height, color=color, **kwargs
    )


# Color constants used in this test
ORANGE: tuple[int, int, int] = (255, 165, 0)


if __name__ == "__main__":
    unittest.main()
