import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame

from miniworlds.base.exceptions import MissingPositionManager
from miniworlds.worlds.world_runtime_facade import WorldRuntimeFacade


class TestWorldRuntimeFacade(unittest.TestCase):
    @staticmethod
    def _actor_with_rects(global_rect: pygame.Rect, screen_rect: pygame.Rect):
        return SimpleNamespace(
            position_manager=SimpleNamespace(
                get_global_rect=MagicMock(return_value=global_rect),
                get_screen_rect=MagicMock(return_value=screen_rect),
            )
        )

    def test_detect_actors_uses_camera_candidates_for_visible_positions(self):
        in_view_actor = self._actor_with_rects(
            pygame.Rect(10, 10, 20, 20), pygame.Rect(10, 10, 20, 20)
        )
        excluded_actor = self._actor_with_rects(
            pygame.Rect(10, 10, 20, 20), pygame.Rect(10, 10, 20, 20)
        )

        camera = SimpleNamespace(
            rect=pygame.Rect(0, 0, 100, 100),
            screen_rect=pygame.Rect(0, 0, 100, 100),
            get_actors_in_view=MagicMock(return_value=[in_view_actor]),
        )
        world = SimpleNamespace(camera=camera, actors=[in_view_actor, excluded_actor])
        facade = WorldRuntimeFacade(world)

        detected = facade.detect_actors((15, 15))

        self.assertEqual(detected, [in_view_actor])
        excluded_actor.position_manager.get_global_rect.assert_not_called()

    def test_detect_actors_falls_back_to_all_actors_outside_camera_view(self):
        offscreen_actor = self._actor_with_rects(
            pygame.Rect(150, 150, 30, 30), pygame.Rect(0, 0, 0, 0)
        )
        other_actor = self._actor_with_rects(
            pygame.Rect(0, 0, 20, 20), pygame.Rect(0, 0, 20, 20)
        )

        camera = SimpleNamespace(
            rect=pygame.Rect(0, 0, 100, 100),
            screen_rect=pygame.Rect(0, 0, 100, 100),
            get_actors_in_view=MagicMock(return_value=set()),
        )
        world = SimpleNamespace(camera=camera, actors=[offscreen_actor, other_actor])
        facade = WorldRuntimeFacade(world)

        detected = facade.detect_actors((160, 160))

        self.assertEqual(detected, [offscreen_actor])
        camera.get_actors_in_view.assert_not_called()

    def test_get_actors_from_pixel_uses_camera_candidates(self):
        visible_actor = self._actor_with_rects(
            pygame.Rect(0, 0, 0, 0), pygame.Rect(10, 10, 20, 20)
        )
        excluded_actor = self._actor_with_rects(
            pygame.Rect(0, 0, 0, 0), pygame.Rect(10, 10, 20, 20)
        )

        camera = SimpleNamespace(
            rect=pygame.Rect(0, 0, 100, 100),
            screen_rect=pygame.Rect(0, 0, 100, 100),
            get_actors_in_view=MagicMock(return_value=[visible_actor]),
        )
        world = SimpleNamespace(camera=camera, actors=[visible_actor, excluded_actor])
        facade = WorldRuntimeFacade(world)

        detected = facade.get_actors_from_pixel((15, 15))

        self.assertEqual(detected, [visible_actor])
        excluded_actor.position_manager.get_screen_rect.assert_not_called()

    def test_get_from_pixel_rejects_negative_coordinates(self):
        world = SimpleNamespace(camera=SimpleNamespace(width=100, height=80), actors=[])
        facade = WorldRuntimeFacade(world)

        self.assertIsNone(facade.get_from_pixel((-1, 10)))
        self.assertIsNone(facade.get_from_pixel((10, -1)))

    def test_detect_actors_skips_actor_with_missing_position_manager(self):
        valid_actor = self._actor_with_rects(
            pygame.Rect(10, 10, 20, 20), pygame.Rect(0, 0, 0, 0)
        )

        broken_actor = SimpleNamespace()
        broken_actor.position_manager = SimpleNamespace(
            get_global_rect=MagicMock(side_effect=MissingPositionManager(object()))
        )

        camera = SimpleNamespace(
            rect=pygame.Rect(0, 0, 100, 100),
            screen_rect=pygame.Rect(0, 0, 100, 100),
            get_actors_in_view=MagicMock(return_value=[valid_actor, broken_actor]),
        )
        world = SimpleNamespace(camera=camera, actors=[valid_actor, broken_actor])
        facade = WorldRuntimeFacade(world)

        detected = facade.detect_actors((15, 15))

        self.assertEqual(detected, [valid_actor])

    def test_get_actors_from_pixel_returns_empty_for_invalid_point_shape(self):
        camera = SimpleNamespace(
            rect=pygame.Rect(0, 0, 100, 100),
            screen_rect=pygame.Rect(0, 0, 100, 100),
            get_actors_in_view=MagicMock(return_value=[]),
        )
        world = SimpleNamespace(camera=camera, actors=[])
        facade = WorldRuntimeFacade(world)

        self.assertEqual(facade.get_actors_from_pixel((10,)), [])


if __name__ == "__main__":
    unittest.main()
