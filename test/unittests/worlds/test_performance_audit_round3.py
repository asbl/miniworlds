"""Regression tests for the third performance-audit round (large worlds).

Covers:
- _rebuild_static_tile_layer iterates only view candidates (TiledSpatialIndex)
  and produces the same layer as a brute-force scan over all actors
- Background.set_dirty only re-renders costumes of actors in view, and
  _blit_to_window_surface no longer triggers a full sprite repaint itself
- transformation_rotate caches rotozoom results per (image, direction)
- CollisionManager caches detect_actors(filter=None) per actor and frame
- default_event_handler uses isinstance checks (behavior unchanged)
"""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pygame

from miniworlds import Actor, App, World
from miniworlds.appearances.managers.transformations_manager import (
    TransformationsManager,
)
from miniworlds.worlds.manager.event_handler import EventHandler
from miniworlds.worlds.tiled_world.tiled_world import TiledWorld


class TestStaticTileLayerViewCandidates(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = TiledWorld(40, 40, tile_size=32)
        self.world.camera.view = (6, 6)
        self.world.camera.dirty = True
        self.world.camera.topleft = (0, 0)
        self.near = Actor((1, 1), world=self.world)
        self.near.add_costume((220, 20, 20, 128))
        # far enough that its chunk (30//8=3) is outside the camera chunk
        # range (view tiles 0..5 + ring 1 -> chunks -1..1)
        self.far = Actor((30, 30), world=self.world)
        self.far.add_costume((20, 220, 20, 128))

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_candidates_come_from_view_not_all_actors(self):
        candidates = list(self.world._static_layer_candidates())
        self.assertIn(self.near, candidates)
        self.assertNotIn(self.far, candidates)
        self.assertLess(len(candidates), len(self.world.actors))
        # iteration order matches world.actors order (blit order matters)
        actors = list(self.world.actors)
        positions = [actors.index(actor) for actor in candidates]
        self.assertEqual(positions, sorted(positions))

    def test_rebuilt_layer_matches_brute_force(self):
        self.world._rebuild_static_tile_layer()
        layer = self.world._static_tile_layer

        expected = self.world.background.image.copy()
        camera_rect = self.world.camera.rect
        for actor in self.world.actors:
            if not getattr(actor, "_static", False):
                continue
            if self.world.event_manager.registry.has_instance_handlers(actor):
                continue
            if not getattr(actor, "visible", True):
                continue
            costume = getattr(actor, "costume", None)
            if costume is None:
                continue
            rect = actor.position_manager.get_global_rect()
            if not camera_rect.colliderect(rect):
                continue
            try:
                image = actor.image
            except AttributeError:
                continue
            if image is None:
                continue
            topleft_px = self.world.camera.topleft
            expected.blit(image, rect.move(-topleft_px[0], -topleft_px[1]))

        self.assertEqual(
            pygame.image.tostring(layer, "RGBA"),
            pygame.image.tostring(expected, "RGBA"),
        )


class TestStaticLayerScrollPositioning(unittest.TestCase):
    """Regression: the static layer is built in camera-local pixel
    coordinates. It used to subtract tile units from pixel rects, which
    misplaced every static actor once the camera scrolled."""

    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = TiledWorld(8, 3, tile_size=40)
        self.world.camera.world_size_x = 8
        self.world.camera.view = (4, 3)
        self.world.add_background((35, 55, 75, 255))
        self.marker = Actor((2, 0), world=self.world)
        self.marker.add_costume((110, 120, 150, 255))

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_scrolled_camera_places_actor_at_local_origin(self):
        self.world.camera.topleft = (2, 0)  # tile (2, 0) is now top-left of view
        self.world._static_tile_layer_dirty = True
        layer, _ = self.world._refresh_static_tile_layer()

        # marker covers tile (2, 0) -> must be at the layer origin (0, 0)
        self.assertEqual(layer.get_at((5, 5)), (110, 120, 150, 255))
        self.assertEqual(layer.get_at((35, 35)), (110, 120, 150, 255))
        # one tile further right is background again
        self.assertEqual(layer.get_at((45, 5)), (35, 55, 75, 255))

    def test_unscrolled_camera_places_actor_at_world_position(self):
        self.world.camera.topleft = (0, 0)
        self.world._static_tile_layer_dirty = True
        layer, _ = self.world._refresh_static_tile_layer()

        # marker covers tile (2, 0) -> world pixels 80..120
        self.assertEqual(layer.get_at((85, 5)), (110, 120, 150, 255))
        self.assertEqual(layer.get_at((5, 5)), (35, 55, 75, 255))


class TestBackgroundSetDirty(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(400, 400)
        self.world.camera.view = (100, 100)
        self.world.camera.dirty = True
        self.world.camera._clear_camera_cache()
        self.in_view = Actor((10, 10), world=self.world)
        self.in_view.add_costume((255, 0, 0, 255))
        self.off_view = Actor((350, 350), world=self.world)
        self.off_view.add_costume((0, 255, 0, 255))
        self.world.backgrounds._is_display_initialized = True

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_set_dirty_reloads_only_view_actor_costumes(self):
        in_spy = Mock(wraps=self.in_view.costume.set_dirty)
        off_spy = Mock(wraps=self.off_view.costume.set_dirty)
        self.in_view.costume.set_dirty = in_spy
        self.off_view.costume.set_dirty = off_spy

        self.world.background.set_dirty("all", self.world.background.LOAD_NEW_IMAGE)

        in_spy.assert_called_once()
        off_spy.assert_not_called()
        # display-initialized flag is still propagated to all actors
        self.assertTrue(self.in_view.costume_manager._is_display_initialized)
        self.assertTrue(self.off_view.costume_manager._is_display_initialized)

    def test_blit_to_window_surface_blits_and_repaints(self):
        # The repaint inside _blit_to_window_surface is load-bearing (camera
        # reloads during camera._update rely on it), so it stays.
        background = self.world.background
        background.repaint = Mock()
        self.world.app.window = SimpleNamespace(surface=Mock())
        self.world.app.add_display_to_repaint_areas = Mock()
        self.world.app.add_running_world(self.world)

        background._blit_to_window_surface()

        self.world.app.window.surface.blit.assert_called_once()
        self.world.app.add_display_to_repaint_areas.assert_called_once()
        background.repaint.assert_called_once_with()


class TestRotationCache(unittest.TestCase):
    def _make_manager(self, direction=90):
        appearance = SimpleNamespace(
            parent=SimpleNamespace(direction=direction, size=(20, 10), dirty=0),
            _is_rotatable=True,
        )
        return TransformationsManager(appearance), appearance

    def test_rotate_result_cached_per_direction(self):
        manager, appearance = self._make_manager(direction=90)
        image = pygame.Surface((20, 10), pygame.SRCALPHA)

        with patch(
            "pygame.transform.rotozoom", wraps=pygame.transform.rotozoom
        ) as rotozoom_spy:
            first = manager.transformation_rotate(image, appearance)
            second = manager.transformation_rotate(image, appearance)
            self.assertIs(first, second)
            self.assertEqual(rotozoom_spy.call_count, 1)

            appearance.parent.direction = 45
            third = manager.transformation_rotate(image, appearance)
            self.assertIsNot(first, third)
            self.assertEqual(rotozoom_spy.call_count, 2)

    def test_rotate_cache_survives_render_revision_bump(self):
        manager, appearance = self._make_manager(direction=90)
        image = pygame.Surface((20, 10), pygame.SRCALPHA)

        with patch(
            "pygame.transform.rotozoom", wraps=pygame.transform.rotozoom
        ) as rotozoom_spy:
            manager.process_transformation_pipeline(image, appearance)
            manager.flag_reload_actions_for_transformation_pipeline("all")
            manager.process_transformation_pipeline(image, appearance)
            # direction unchanged -> no second rotozoom
            self.assertEqual(rotozoom_spy.call_count, 1)


class R3Wall(Actor):
    pass


class R3Hunter(Actor):
    def __init__(self, *args, **kwargs):
        self.detected = []
        super().__init__(*args, **kwargs)

    def on_detecting(self, other):
        self.detected.append(("all", other))

    def on_detecting_r3wall(self, other):
        self.detected.append(("wall", other))


class TestCollisionDetectCache(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(200, 200)
        self.wall = R3Wall((50, 50), world=self.world)
        self.wall.collision_type = "rect"
        self.hunter = R3Hunter((50, 50), world=self.world)
        self.hunter.collision_type = "rect"

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_detect_actors_called_once_per_actor_per_frame(self):
        spy = Mock(wraps=self.hunter.sensor_manager.detect_actors)
        self.hunter.sensor_manager.detect_actors = spy

        self.world._collision_manager._handle_all_collisions()

        unfiltered_calls = [
            c for c in spy.call_args_list if c.kwargs.get("filter", None) is None
        ]
        self.assertEqual(len(unfiltered_calls), 1)
        # both handlers still fired with the correct target
        self.assertIn(("all", self.wall), self.hunter.detected)
        self.assertIn(("wall", self.wall), self.hunter.detected)


class _Recorder:
    def __init__(self):
        self.calls = []

    def on_custom(self, data):
        self.calls.append(data)


def _make_handler(event_handler_world_builder, event_registry_builder, collidepoint):
    recorder = _Recorder()
    registry = event_registry_builder({"on_custom": {recorder.on_custom}})
    world = event_handler_world_builder(
        camera=SimpleNamespace(
            is_in_screen=Mock(return_value=True),
            screen_rect=SimpleNamespace(collidepoint=Mock(return_value=collidepoint)),
        )
    )
    return EventHandler(world, registry), recorder


def test_event_handler_tuple_data_inside_screen_is_delivered(
    event_handler_world_builder, event_registry_builder
):
    handler, recorder = _make_handler(
        event_handler_world_builder, event_registry_builder, collidepoint=True
    )
    handler.handle_event("custom", (10, 10))
    assert len(recorder.calls) == 1


def test_event_handler_tuple_data_outside_screen_is_dropped(
    event_handler_world_builder, event_registry_builder
):
    handler, recorder = _make_handler(
        event_handler_world_builder, event_registry_builder, collidepoint=False
    )
    handler.handle_event("custom", (10000, 10000))
    assert recorder.calls == []


def test_event_handler_list_data_is_delivered(
    event_handler_world_builder, event_registry_builder
):
    handler, recorder = _make_handler(
        event_handler_world_builder, event_registry_builder, collidepoint=True
    )
    handler.handle_event("custom", [1, 2])
    assert len(recorder.calls) == 1


if __name__ == "__main__":
    unittest.main()
