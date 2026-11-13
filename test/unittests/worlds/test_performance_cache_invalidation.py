"""Mutation and rendering regressions for the large-world optimizations."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pygame
import pytest

from miniworlds.base.manager.app_worlds_manager import WorldsManager
from miniworlds.worlds.manager.ordered_actor_group import OrderedActorGroup


def test_spatial_candidates_keep_pygame_order_after_mutations():
    group = OrderedActorGroup()
    actors = [pygame.sprite.DirtySprite() for _ in range(4)]
    group.add(*actors)
    candidates = set(actors)
    assert group.ordered_candidates(candidates) == group.sprites()
    group.change_layer(actors[0], 2)
    assert group.ordered_candidates(candidates) == group.sprites()
    group.change_layer(actors[1], 0)  # reorders within the same layer
    assert group.ordered_candidates(candidates) == group.sprites()
    group.remove(actors[2])
    assert group.ordered_candidates(candidates) == group.sprites()
    group.add(actors[2])
    assert group.ordered_candidates(candidates) == group.sprites()
    group.switch_layer(0, 2)
    assert group.ordered_candidates(candidates) == group.sprites()


def test_frame_defers_intermediate_background_repaints():
    calls = []
    loop = SimpleNamespace(_defer_background_repaint=False)

    async def update():
        assert loop._defer_background_repaint
        calls.append("update")
        return 0.01

    def repaint():
        assert not loop._defer_background_repaint
        calls.append("repaint")

    loop.update = update
    loop.repaint = repaint
    loop.blit_surface_to_window_surface = lambda: calls.append("blit")
    manager = WorldsManager(Mock())
    manager.worlds = [SimpleNamespace(dirty=True, frame=1, _mainloop=loop)]
    assert asyncio.run(manager.reload_all_worlds()) == 0.01
    assert calls == ["update", "repaint", "blit"]


def test_repaint_deferral_restored_after_failed_update():
    loop = SimpleNamespace(update=AsyncMock(side_effect=RuntimeError("update failed")))
    manager = WorldsManager(Mock())
    manager.worlds = [SimpleNamespace(dirty=True, frame=1, _mainloop=loop)]
    with pytest.raises(RuntimeError, match="update failed"):
        asyncio.run(manager.reload_all_worlds())
    assert not loop._defer_background_repaint


@pytest.mark.parametrize("position,size", [((-9, -7), (19, 23)), ((7, 7), (2, 2)), ((2.5, 3.5), (31, 17)), ((0, 0), (1, 1))])
def test_large_actor_chunk_span_matches_occupied_tiles(position, size):
    from miniworlds.worlds.manager.tiled_spatial_index import TiledSpatialIndex

    index = TiledSpatialIndex(chunk_size=8)
    actor = type("ActorStub", (), {"position": position, "size": size})()
    index.update(actor)
    expected = {
        ((int(position[0]) + dx) // 8, (int(position[1]) + dy) // 8)
        for dx in range(size[0])
        for dy in range(size[1])
    }
    assert index._actor_chunks[actor] == expected
    for chunk_x, chunk_y in expected:
        assert actor in index.query_position((chunk_x * 8, chunk_y * 8))


@pytest.mark.parametrize("setup_fails", [False, True])
def test_reset_presents_setup_immediately_and_restores_batch(setup_fails):
    from miniworlds.worlds.world_runtime_facade import WorldRuntimeFacade

    loop = SimpleNamespace(_defer_background_repaint=True)

    def setup():
        assert not loop._defer_background_repaint
        if setup_fails:
            raise RuntimeError("setup failed")

    world = SimpleNamespace(_mainloop=loop, on_setup=setup)
    facade = WorldRuntimeFacade(world)
    facade.clear = Mock()
    if setup_fails:
        with pytest.raises(RuntimeError, match="setup failed"):
            facade.reset()
    else:
        facade.reset()
        assert world._is_setup_completed
    assert loop._defer_background_repaint
