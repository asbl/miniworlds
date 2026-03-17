from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from miniworlds import Actor, World
from miniworlds.appearances.background import Background
from miniworlds.base.app import App
from miniworlds.base.manager.app_worlds_manager import WorldsManager
import miniworlds.worlds.world_base as world_base
from miniworlds.worlds.manager.camera_manager import CameraManager
from miniworlds.worlds.manager.layout_manager import LayoutManager
from test.unittests.support.builders import (
    make_app_with_event_queue,
    make_managed_world,
    make_worlds_manager_app,
)


class TestWorldProxies(unittest.TestCase):
    def test_world_proxies_delegate_to_camera_data_and_event_manager(self):
        world = World.__new__(World)
        world.camera = Mock()
        world.data = Mock()
        world.app = make_app_with_event_queue()

        new_world = Mock()
        World.switch_world(world, new_world, reset=True)
        World.save_to_db(world, "save.db")
        World.load_world_from_db(world, "save.db")
        World.load_actors_from_db(world, "save.db", [Actor])
        World.send_message(world, "saved", {"unused": True})

        world.camera.switch_world.assert_called_once_with(new_world, True)
        world.data.save_to_db.assert_called_once_with("save.db")
        world.data.load_world_from_db.assert_called_once_with("save.db")
        world.data.load_actors_from_db.assert_called_once_with("save.db", [Actor])
        world.app.event_manager.to_event_queue.assert_called_once_with(
            "message", ("saved", {"unused": True})
        )

    def test_world_layout_proxy_returns_camera_for_example_compatibility(self):
        world = World.__new__(World)
        world.camera = Mock()

        self.assertIs(World.layout.__get__(world, World), world.camera)


class TestCameraDockingProxy(unittest.TestCase):
    def test_camera_proxy_delegates_docking_methods_to_layout(self):
        layout = Mock()
        camera = CameraManager.__new__(CameraManager)
        camera.world = SimpleNamespace(_layout=layout)
        other_world = Mock()

        CameraManager.add_right(camera, other_world, 120)
        CameraManager.add_bottom(camera, other_world, 80)
        CameraManager.remove_world(camera, other_world)
        CameraManager.switch_world(camera, other_world, reset=True)

        layout.add_right.assert_called_once_with(other_world, 120)
        layout.add_bottom.assert_called_once_with(other_world, 80)
        layout.remove_world.assert_called_once_with(other_world)
        layout.switch_world.assert_called_once_with(other_world, True)


class TestActorLifecycle(unittest.TestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_actor_can_be_initialized_with_explicit_world(self):
        App.reset(unittest=True, file=__file__)
        world = World(40, 40)

        actor = Actor((5, 5), world=world)

        self.assertIs(actor.world, world)

    def test_actor_uses_running_world_when_no_world_argument_is_passed(self):
        App.reset(unittest=True, file=__file__)
        world = World(40, 40)

        with patch("miniworlds.base.app.App.get_running_world", return_value=world):
            actor = Actor((6, 6))

        self.assertIs(actor.world, world)

    def test_actor_send_message_uses_world_app_event_queue(self):
        actor = Actor.__new__(Actor)
        actor._world = SimpleNamespace(app=make_app_with_event_queue())

        Actor.send_message(actor, "hello")

        actor.world.app.event_manager.to_event_queue.assert_called_once_with("message", "hello")


class TestWorldInitialization(unittest.TestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_world_creates_event_manager_only_once(self):
        App.reset(unittest=True, file=__file__)
        original = world_base.WorldBase._create_event_manager
        created_for = []

        def create_event_manager(instance):
            created_for.append(instance)
            return original(instance)

        with patch.object(
            world_base.WorldBase,
            "_create_event_manager",
            autospec=True,
            side_effect=create_event_manager,
        ):
            world = World(40, 40)

        self.assertEqual(len(created_for), 1)
        self.assertIs(created_for[0], world)
        self.assertIs(world.event_manager.world, world)


class TestLayoutManager(unittest.TestCase):
    def test_layout_manager_delegates_to_worlds_manager(self):
        app = SimpleNamespace(worlds_manager=Mock())
        world = Mock()
        layout = LayoutManager(world, app)
        other_world = Mock()

        layout.add_right(other_world, size=120)
        layout.add_bottom(other_world, size=80)
        layout.remove_world(other_world)
        layout.switch_world(other_world, reset=True)

        app.worlds_manager.add_world.assert_any_call(other_world, dock="right", size=120)
        app.worlds_manager.add_world.assert_any_call(other_world, dock="bottom", size=80)
        app.worlds_manager.remove_world.assert_called_once_with(other_world)
        app.worlds_manager.switch_world.assert_called_once_with(world, other_world, True)


class TestWorldsManager(unittest.TestCase):
    def test_activate_world_initializes_and_tracks_running_world(self):
        app = make_worlds_manager_app()
        manager = WorldsManager(app)
        world = make_managed_world()

        manager._activate_world(world, reset=True, setup=True, run=True)

        app.set_running_world.assert_called_once_with(world)
        app.add_running_world.assert_called_once_with(world)
        world.backgrounds._init_display.assert_called_once_with()
        world.on_setup.assert_called_once_with()
        world.reset.assert_called_once_with()
        world._start_listening.assert_called_once_with()
        world.on_change.assert_called_once_with()

    def test_switch_world_updates_running_world_and_calls_transition_steps(self):
        app = make_worlds_manager_app()
        manager = WorldsManager(app)
        old_world = make_managed_world(frame=1)
        new_world = make_managed_world(frame=1)
        app.running_world = old_world
        manager._deactivate_world = Mock()
        manager._activate_world = Mock()
        manager._finalize_world_switch = Mock()

        manager.switch_world(old_world, new_world, reset=False, setup=True)

        app.set_running_world.assert_called_once_with(new_world)
        manager._deactivate_world.assert_called_once_with(old_world)
        manager._activate_world.assert_called_once_with(new_world, False, True)
        manager._finalize_world_switch.assert_called_once_with(old_world, new_world)


class TestBackgroundLifecycle(unittest.TestCase):
    def test_active_background_blits_and_marks_repaint(self):
        background = Background.__new__(Background)
        world = SimpleNamespace(
            app=SimpleNamespace(
                running_worlds=[],
                window=SimpleNamespace(surface=Mock()),
                add_display_to_repaint_areas=Mock(),
            ),
            camera=SimpleNamespace(screen_topleft=(3, 4)),
            actors=SimpleNamespace(clear=Mock(), draw=Mock(return_value=[])),
        )
        world.app.running_worlds.append(world)
        background.parent = world
        background.get_image = Mock(return_value="background-image")
        background.surface = Mock()
        background.repaint = Mock()

        Background._blit_to_window_surface(background)

        world.app.window.surface.blit.assert_called_once_with("background-image", (3, 4))
        world.app.add_display_to_repaint_areas.assert_called_once_with()
        background.repaint.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()