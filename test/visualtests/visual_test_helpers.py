"""Common helper functions and constants for visual tests.

This module provides reusable components for visual tests including:
- Common test constants (colors, dimensions, positions)
- Helper functions for creating test worlds
- Common setup patterns for visual tests
- Reusable actor configurations
"""

import unittest
from typing import Callable, Optional, Tuple

import miniworlds
from miniworlds import App

from .screenshot_tester import ScreenshotTester

# =============================================================================
# Common Test Constants
# =============================================================================

# Display constants
TEST_WORLD_WIDTH: int = 800
TEST_WORLD_HEIGHT: int = 600
BACKGROUND_COLOR: Tuple[int, int, int] = (240, 240, 240)
TRANSPARENT_BACKGROUND: Tuple[int, int, int, int] = (240, 240, 240, 0)

# Position constants
ORIGIN: Tuple[int, int] = (0, 0)
CENTER_POSITION: Tuple[int, int] = (400, 300)
TOP_LEFT: Tuple[int, int] = (50, 50)
TOP_RIGHT: Tuple[int, int] = (750, 50)
BOTTOM_LEFT: Tuple[int, int] = (50, 550)
BOTTOM_RIGHT: Tuple[int, int] = (750, 550)

# Color constants
RED: Tuple[int, int, int] = (255, 0, 0)
GREEN: Tuple[int, int, int] = (0, 255, 0)
BLUE: Tuple[int, int, int] = (0, 0, 255)
BLACK: Tuple[int, int, int] = (0, 0, 0)
WHITE: Tuple[int, int, int] = (255, 255, 255)
YELLOW: Tuple[int, int, int] = (255, 255, 0)
CYAN: Tuple[int, int, int] = (0, 255, 255)
MAGENTA: Tuple[int, int, int] = (255, 0, 255)
GRAY: Tuple[int, int, int] = (128, 128, 128)
TRANSPARENT_RED: Tuple[int, int, int, int] = (255, 0, 0, 128)

# Dimension constants
SMALL_SIZE: int = 10
MEDIUM_SIZE: int = 50
LARGE_SIZE: int = 100
TINY_SIZE: int = 1
HUGE_SIZE: int = 300

# Edge case constants
ZERO_SIZE: int = 0
NEGATIVE_SIZE: int = -10
VERY_LARGE_SIZE: int = 10000

# Screenshot test constants
TEST_FRAMES: list[int] = [1]
QUIT_FRAME: int = 1


# =============================================================================
# Helper Functions
# =============================================================================


def create_test_world(
    width: int = TEST_WORLD_WIDTH,
    height: int = TEST_WORLD_HEIGHT,
    background: Tuple[int, int, int] = BACKGROUND_COLOR,
) -> miniworlds.World:
    """Create a standard test world with the given parameters.

    Args:
        width: Width of the world in pixels
        height: Height of the world in pixels
        background: Background color as RGB tuple

    Returns:
        A configured World instance
    """
    world: miniworlds.World = miniworlds.World(width, height)
    world.background = background
    return world


def setup_screenshot_tester(
    test_instance: unittest.TestCase,
    world: miniworlds.World,
    test_frames: Optional[list[int]] = None,
    quit_frame: Optional[int] = None,
) -> ScreenshotTester:
    """Set up a ScreenshotTester for a test case.

    Args:
        test_instance: The unittest.TestCase instance
        world: The world to test
        test_frames: List of frames to capture (defaults to TEST_FRAMES)
        quit_frame: Frame at which to quit (defaults to QUIT_FRAME)

    Returns:
        A configured ScreenshotTester instance
    """
    frames: list[int] = test_frames if test_frames is not None else TEST_FRAMES
    qframe: int = quit_frame if quit_frame is not None else QUIT_FRAME
    tester: ScreenshotTester = ScreenshotTester(frames, qframe, test_instance)
    tester.setup(world)
    return tester


def create_screenshot_test_method(
    test_class: type,
    world_factory: Callable[[], miniworlds.World],
    test_name: str = "test_screenshot",
) -> None:
    """Create a screenshot test method dynamically.

    This is a helper for creating consistent test methods across visual tests.

    Args:
        test_class: The test class to add the method to
        world_factory: A callable that creates the test world
        test_name: Name of the test method
    """

    def test_method(self: unittest.TestCase) -> None:
        """Generated screenshot test method."""
        App.reset(unittest=True, file=self.__class__.__module__)
        world: miniworlds.World = world_factory()
        setup_screenshot_tester(self, world)
        with self.assertRaises(SystemExit):
            self.world.run()

    setattr(test_class, test_name, test_method)


# =============================================================================
# Common Test World Setups
# =============================================================================


def create_empty_world() -> miniworlds.World:
    """Create an empty test world with default settings."""
    return create_test_world()


def create_world_with_grid(
    cell_size: int = 50,
    rows: int = 10,
    cols: int = 16,
) -> miniworlds.World:
    """Create a world with a grid background pattern.

    Args:
        cell_size: Size of each grid cell in pixels
        rows: Number of rows
        cols: Number of columns

    Returns:
        A world with grid background
    """
    world: miniworlds.World = create_test_world()
    # Grid background would be implemented here
    return world


# =============================================================================
# Shape Creation Helpers
# =============================================================================


def create_circle_at(
    position: Tuple[int, int],
    radius: int = MEDIUM_SIZE // 2,
    color: Tuple[int, int, int] = RED,
    **kwargs,
) -> miniworlds.Circle:
    """Create a circle actor at the specified position.

    Args:
        position: (x, y) position tuple
        radius: Radius of the circle
        color: RGB color tuple
        **kwargs: Additional keyword arguments for Circle

    Returns:
        A Circle actor
    """
    circle: miniworlds.Circle = miniworlds.Circle(
        position, radius=radius, color=color, **kwargs
    )
    return circle


def create_rectangle_at(
    position: Tuple[int, int],
    width: int = MEDIUM_SIZE,
    height: int = MEDIUM_SIZE,
    color: Tuple[int, int, int] = BLUE,
    **kwargs,
) -> miniworlds.Rectangle:
    """Create a rectangle actor at the specified position.

    Args:
        position: (x, y) position tuple
        width: Width of the rectangle
        height: Height of the rectangle
        color: RGB color tuple
        **kwargs: Additional keyword arguments for Rectangle

    Returns:
        A Rectangle actor
    """
    rect: miniworlds.Rectangle = miniworlds.Rectangle(
        position, width=width, height=height, color=color, **kwargs
    )
    return rect


def create_line_between(
    start: Tuple[int, int],
    end: Tuple[int, int],
    color: Tuple[int, int, int] = BLACK,
    width: int = 2,
    **kwargs,
) -> miniworlds.Line:
    """Create a line actor between two points.

    Args:
        start: Starting (x, y) position
        end: Ending (x, y) position
        color: RGB color tuple
        width: Line width in pixels
        **kwargs: Additional keyword arguments for Line

    Returns:
        A Line actor
    """
    line: miniworlds.Line = miniworlds.Line(
        start, end, width=width, color=color, **kwargs
    )
    return line


def create_text_at(
    position: Tuple[int, int],
    text: str = "Test Text",
    font_size: int = 24,
    color: Tuple[int, int, int] = BLACK,
    **kwargs,
) -> miniworlds.Text:
    """Create a text actor at the specified position.

    Args:
        position: (x, y) position tuple
        text: Text content
        font_size: Font size in pixels
        color: RGB color tuple
        **kwargs: Additional keyword arguments for Text

    Returns:
        A Text actor
    """
    text_actor: miniworlds.Text = miniworlds.Text(
        position, text=text, font_size=font_size, color=color, **kwargs
    )
    return text_actor


# =============================================================================
# Edge Case Helpers
# =============================================================================


def create_zero_size_circle(position: Tuple[int, int]) -> miniworlds.Circle:
    """Create a circle with zero radius."""
    return create_circle_at(position, radius=ZERO_SIZE)


def create_zero_size_rectangle(position: Tuple[int, int]) -> miniworlds.Rectangle:
    """Create a rectangle with zero dimensions."""
    return create_rectangle_at(position, width=ZERO_SIZE, height=ZERO_SIZE)


def create_negative_size_rectangle(position: Tuple[int, int]) -> miniworlds.Rectangle:
    """Create a rectangle with negative dimensions."""
    return create_rectangle_at(position, width=NEGATIVE_SIZE, height=NEGATIVE_SIZE)


def create_transparent_shape(
    shape_type: str = "circle",
    position: Tuple[int, int] = CENTER_POSITION,
    alpha: int = 128,
) -> miniworlds.Circle:
    """Create a transparent shape.

    Args:
        shape_type: Type of shape ('circle', 'rectangle')
        position: Position tuple
        alpha: Alpha value (0-255)

    Returns:
        A shape actor with transparency
    """
    if shape_type == "circle":
        return create_circle_at(position, color=(*RED, alpha))
    else:
        return create_rectangle_at(position, color=(*BLUE, alpha))
