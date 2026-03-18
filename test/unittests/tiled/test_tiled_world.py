from collections import defaultdict
from types import SimpleNamespace
from unittest.mock import Mock

from miniworlds.worlds.tiled_world.tiled_world import TiledWorld


def _make_world(width=120, height=50):
    world = SimpleNamespace()
    world.camera = SimpleNamespace(width=width, height=height)
    world.get_tile_from_pixel = Mock(return_value=SimpleNamespace(position=(3, 4)))
    return world


def _make_detection_world():
    """Minimal world stub for detect_actors_at_position tests."""
    world = SimpleNamespace()
    world._dynamic_actors = []
    world._dynamic_actors_dict = defaultdict(list)
    world.static_actors_dict = defaultdict(list)
    world._update_actor_positions = lambda: world._dynamic_actors_dict.clear()
    return world


def test_get_from_pixel_rejects_outside_bounds_and_negatives():
    world = _make_world(width=120, height=50)

    assert TiledWorld.get_from_pixel(world, (-1, 10)) is None
    assert TiledWorld.get_from_pixel(world, (10, -1)) is None
    assert TiledWorld.get_from_pixel(world, (120, 10)) is None
    assert TiledWorld.get_from_pixel(world, (10, 50)) is None

    world.get_tile_from_pixel.assert_not_called()


def test_get_from_pixel_uses_camera_width_for_x_bound():
    world = _make_world(width=120, height=50)

    position = TiledWorld.get_from_pixel(world, (80, 10))

    assert position == (3, 4)
    world.get_tile_from_pixel.assert_called_once_with((80, 10))


def test_detect_actors_at_position_finds_static_actor_when_x_ne_y():
    """Regression: static_actors_dict was keyed by (y, y), missing actors when x != y."""
    world = _make_detection_world()
    actor = SimpleNamespace(name="static_actor")
    world.static_actors_dict[(2, 3)] = [actor]

    result = TiledWorld.detect_actors_at_position(world, (2, 3))

    assert actor in result


def test_detect_actors_at_position_ignores_wrong_position():
    """Static actor at (2, 3) must NOT appear when querying (5, 1)."""
    world = _make_detection_world()
    actor = SimpleNamespace(name="other_actor")
    world.static_actors_dict[(2, 3)] = [actor]

    result = TiledWorld.detect_actors_at_position(world, (5, 1))

    assert actor not in result
