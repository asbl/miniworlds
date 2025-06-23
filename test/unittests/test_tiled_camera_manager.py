import pytest
import pygame
from unittest.mock import MagicMock

import miniworlds.worlds.tiled_world.tiled_world_camera_manager as tiled_camera_manager

@pytest.fixture
def mock_world():
    world = MagicMock()
    world.tile_size = 32
    world_size = (100, 100)
    world.__contains__.side_effect = lambda x: True
    world_size_x = 100
    world_size_y = 100
    world.world_size_x = world_size_x
    world.world_size_y = world_size_y
    return world


@pytest.fixture
def camera(mock_world):
    return tiled_camera_manager.TiledCameraManager(view_x=10, view_y=8, world=mock_world)
    cam.world = mock_world
    cam._topleft = (2, 3)
    cam.world_size_x = 100  # wichtig für _limit_x
    cam.view = (20, 15)     # wichtig für _limit_x
    cam.world_size_y = mock_world.world_size_y
    return cam



def test_topleft_property(camera):
    camera._topleft = (2, 3)
    assert camera.topleft == (2 * 32, 3 * 32)


def test_get_rect(camera):
    rect = camera.get_rect()
    assert isinstance(rect, pygame.Rect)
    assert rect.topleft == (camera.topleft[0], camera.topleft[1])
    assert rect.width == camera.width
    assert rect.height == camera.height

def test_from_actor_without_center(camera):
    actor = MagicMock()
    actor.center = False
    camera.from_actor(actor)

    assert camera._topleft == (0, 0)
