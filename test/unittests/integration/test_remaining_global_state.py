import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from miniworlds.appearances.background import Background
from miniworlds.base.app import App
from miniworlds.worlds.gui.toolbar import Toolbar
from miniworlds.worlds.tiled_world.tile_elements import TileBase


class DummyTile(TileBase):
    @classmethod
    def from_position(cls, position, world):
        return cls(position, world)


class TestRemainingGlobalState(unittest.TestCase):
    def tearDown(self):
        App.reset()

    def test_tile_base_uses_central_running_world_accessor(self):
        world = Mock()
        App.running_world = world

        tile = DummyTile((1, 2), None)

        self.assertIs(tile.world, world)

    def test_toolbar_send_message_uses_instance_app_event_manager(self):
        toolbar = Toolbar.__new__(Toolbar)
        toolbar.app = SimpleNamespace(event_manager=SimpleNamespace(to_event_queue=Mock()))

        Toolbar.send_message(toolbar, "hello")

        toolbar.app.event_manager.to_event_queue.assert_called_once_with("message", "hello")

    def test_background_blits_only_when_world_is_running_in_app(self):
        background = Background.__new__(Background)
        world = SimpleNamespace(
            app=SimpleNamespace(running_worlds=[], window=SimpleNamespace(surface=Mock()), add_display_to_repaint_areas=Mock()),
            camera=SimpleNamespace(screen_topleft=(0, 0)),
            actors=SimpleNamespace(clear=Mock(), draw=Mock(return_value=[])),
        )
        background.parent = world
        background._image = Mock()
        background.surface = Mock()
        background.repaint = Mock()

        Background._blit_to_window_surface(background)

        world.app.window.surface.blit.assert_not_called()
        background.repaint.assert_not_called()


if __name__ == "__main__":
    unittest.main()