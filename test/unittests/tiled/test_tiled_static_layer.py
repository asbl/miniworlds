import pygame

from miniworlds import Actor, App, TiledWorld


def test_background_dirty_invalidates_static_tile_layer():
    App.reset(unittest=True)
    world = TiledWorld(2, 2)
    world._static_tile_layer_dirty = False
    world.background._blit_to_window_surface = lambda: None

    world.background.set_dirty("all", world.background.RELOAD_ACTUAL_IMAGE)

    assert world._static_tile_layer_dirty is True


def test_refresh_static_tile_layer_rebuilds_only_when_dirty():
    App.reset(unittest=True)
    world = TiledWorld(2, 2)
    world.add_background((10, 20, 30, 255))
    world._static_tile_layer = None
    world._static_tile_layer_dirty = True

    first_layer, first_rebuilt = world._refresh_static_tile_layer()
    second_layer, second_rebuilt = world._refresh_static_tile_layer()

    assert isinstance(first_layer, pygame.Surface)
    assert first_rebuilt is True
    assert second_layer is first_layer
    assert second_rebuilt is False


def test_static_tile_layer_uses_current_background_image():
    App.reset(unittest=True)
    world = TiledWorld(2, 1)
    world.add_background((20, 40, 60, 255))
    actor = Actor((0, 0), world=world)
    actor.add_costume((220, 20, 20, 128))
    actor.static = True

    world._static_tile_layer_dirty = True
    first_layer, _ = world._refresh_static_tile_layer()
    first_pixel = first_layer.get_at((0, 0))

    world.add_background((80, 100, 120, 255))
    world._static_tile_layer_dirty = True
    second_layer, _ = world._refresh_static_tile_layer()
    second_pixel = second_layer.get_at((0, 0))

    assert first_pixel != second_pixel
    assert second_pixel.r > first_pixel.r


def test_tiled_actor_movement_marks_actor_dirty_without_polluting_pixel_worlds():
    App.reset(unittest=True)
    world = TiledWorld(4, 1)
    actor = Actor((0, 0), world=world)
    actor._dirty = 0

    actor.x = 1

    assert actor._dirty == 1
