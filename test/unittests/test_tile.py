import pytest
from unittest.mock import MagicMock

from miniworlds.worlds.tiled_world.tile import Tile

@pytest.fixture
def mock_world():
    world = MagicMock()
    world.tile_size = 32
    world.get_tile.return_value = Tile((1, 1), world)
    world.get_corner.side_effect = lambda pos: f"Corner at {pos}"
    world.get_center_points.return_value = {(0, 0): (16, 16)}
    return world


def test_tile_initialization(mock_world):
    tile = Tile((2, 3), mock_world)
    assert tile.position == (2, 3)
    assert tile.world == mock_world


def test_from_position(mock_world):
    tile = Tile.from_position((1, 1), mock_world)
    assert isinstance(tile, Tile)
    assert tile.position == (1, 1)


def test_from_actor(mock_world):
    actor = MagicMock()
    actor.world = mock_world
    actor.position = (4, 5)
    mock_world.get_tile.return_value = Tile((4, 5), mock_world)
    tile = Tile.from_actor(actor)
    assert tile.position == (4, 5)


def test_to_pixel(mock_world):
    tile = Tile((2, 3), mock_world)
    assert tile.to_pixel() == (64, 96)


def test_to_center(mock_world):
    tile = Tile((1, 1), mock_world)
    tile.get_local_center_coordinate = MagicMock(return_value=(16, 16))
    center = tile.to_center()
    assert center == (48, 48)  # (1*32, 1*32) + (16, 16)


def test_from_pixel(mock_world):
    from miniworlds.base import app
    app.App.running_world = mock_world
    tile = Tile.from_pixel((64, 64))
    assert tile.position == (2, 2)


def test_get_position_pixel_dict(mock_world):
    center_points = Tile.get_position_pixel_dict(mock_world)
    assert center_points == {(0, 0): (16, 16)}


def test_get_neighbour_corners(mock_world):
    tile = Tile((0, 0), mock_world)
    corners = tile.get_neighbour_corners()
    assert len(corners) == 4
    for corner in corners:
        assert isinstance(corner, str)
        assert corner.startswith("Corner at")

    # Caching test
    mock_world.get_corner.reset_mock()
    cached = tile.get_neighbour_corners()
    mock_world.get_corner.assert_not_called()
    assert cached == corners


def test_sub_and_distance_to(mock_world):
    tile1 = Tile((1, 1), mock_world)
    tile2 = Tile((4, 5), mock_world)

    # Patch vector
    from miniworlds.positions.vector import Vector
    vector = tile1 - tile2
    assert isinstance(vector, Vector)
    assert vector.x == -3
    assert vector.y == -4

    # Distance test
    dist = tile1.distance_to(tile2)
    assert round(dist, 2) == 5.0
