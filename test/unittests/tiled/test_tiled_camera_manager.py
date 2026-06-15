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


def test_update_does_not_reload_camera_when_clean(camera):
    camera.dirty = False
    camera._reload_camera = MagicMock()
    camera._cache_rects = MagicMock()

    camera._update()

    camera._reload_camera.assert_not_called()
    camera._cache_rects.assert_not_called()
    assert camera.dirty is False


def test_update_refreshes_rect_cache_once_when_dirty(camera):
    camera.dirty = True
    camera._reload_camera = MagicMock()
    camera._cache_rects = MagicMock()

    camera._update()

    camera._reload_camera.assert_called_once_with()
    camera._cache_rects.assert_called_once_with()
    assert camera.dirty is False


def test_view_size_change_still_reloads_camera(camera):
    camera._reload_camera = MagicMock()

    camera.width = 12

    camera._reload_camera.assert_called_once_with()
    assert camera.dirty is True


def test_setting_same_topleft_does_not_mark_camera_dirty(camera):
    camera.world_size = (100, 100)
    camera._topleft = (2, 3)
    camera.dirty = False
    camera._reload_actors_in_view = MagicMock()

    camera.topleft = (2, 3)

    camera._reload_actors_in_view.assert_not_called()
    assert camera.dirty is False


def test_setting_same_axis_position_does_not_mark_camera_dirty(camera):
    camera.world_size = (100, 100)
    camera._topleft = (2, 3)
    camera.dirty = False
    camera._reload_actors_in_view = MagicMock()

    camera.x = 2
    camera.y = 3

    camera._reload_actors_in_view.assert_not_called()
    assert camera.dirty is False


def test_setting_same_view_size_does_not_reload_camera(camera):
    camera.dirty = False
    camera._reload_camera = MagicMock()

    camera.width = camera.view[0]
    camera.height = camera.view[1]

    camera._reload_camera.assert_not_called()
    assert camera.dirty is False


def test_moving_topleft_marks_camera_and_static_layer_dirty(camera):
    camera.world_size = (100, 100)
    camera.world._static_tile_layer_dirty = False
    camera._reload_actors_in_view = MagicMock()

    camera.topleft = (2, 3)

    camera._reload_actors_in_view.assert_called_once_with()
    assert camera.dirty is True
    assert camera.world._static_tile_layer_dirty is True


def test_moving_axis_position_marks_camera_dirty_once(camera):
    camera.world_size = (100, 100)
    camera._reload_actors_in_view = MagicMock()

    camera.x = 2
    camera.y = 3

    assert camera._topleft == (2, 3)
    assert camera._reload_actors_in_view.call_count == 2
    assert camera.dirty is True


def test_repeated_clean_updates_do_not_reload_after_camera_move(camera):
    camera.world_size = (100, 100)
    camera.topleft = (2, 3)
    camera._reload_camera = MagicMock()

    camera._update()
    for _ in range(10):
        camera._update()

    camera._reload_camera.assert_called_once_with()
    assert camera.dirty is False
