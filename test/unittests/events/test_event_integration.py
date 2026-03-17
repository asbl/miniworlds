from __future__ import annotations

import unittest
from unittest.mock import Mock

import pygame

from miniworlds import Actor, Button, Toolbar, World
from miniworlds.base.app import App


class KeyWorld(World):
    def __init__(self) -> None:
        self.received_events: list[tuple[str, tuple[str, ...] | None]] = []
        super().__init__(80, 80)

    def on_key_down(self, keys) -> None:
        self.received_events.append(("key_down", tuple(keys)))

    def on_key_pressed(self, keys) -> None:
        self.received_events.append(("key_pressed", tuple(keys)))

    def on_key_pressed_a(self) -> None:
        self.received_events.append(("key_pressed_a", None))


class FocusActor(Actor):
    def __init__(self, position=(0, 0), *args, **kwargs) -> None:
        self.received_events: list[str] = []
        super().__init__(position, *args, **kwargs)
        self.is_focusable = True

    def on_focus(self) -> None:
        self.received_events.append("focus")

    def on_focus_lost(self) -> None:
        self.received_events.append("focus_lost")


class HoverActor(Actor):
    def __init__(self, position=(0, 0), *args, **kwargs) -> None:
        self.received_events: list[str] = []
        self.hovered = False
        super().__init__(position, *args, **kwargs)

    def detect_pixel(self, position) -> bool:
        return self.hovered

    def on_mouse_enter(self, position) -> None:
        self.received_events.append("enter")

    def on_mouse_leave(self, position) -> None:
        self.received_events.append("leave")


class MessageWorld(World):
    def __init__(self) -> None:
        self.messages: list[str] = []
        super().__init__(100, 100)

    def on_message(self, message) -> None:
        self.messages.append(message)


class TestEventIntegration(unittest.IsolatedAsyncioTestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    async def _run_frame(self, world: World, events, mouse_pos=(10, 10)) -> None:
        world.app.platform.poll_events = Mock(return_value=list(events))
        world.app.platform.get_mouse_pos = Mock(return_value=mouse_pos)
        await world.app._update()

    async def test_key_hold_sequence_dispatches_down_and_pressed_events(self):
        App.reset(unittest=True, file=__file__)
        world = KeyWorld()

        await self._run_frame(
            world,
            [pygame.event.Event(pygame.KEYDOWN, {"unicode": "a", "key": pygame.K_a})],
        )
        await self._run_frame(world, [])

        self.assertIn(("key_down", ("a",)), world.received_events)
        self.assertGreaterEqual(world.received_events.count(("key_pressed", ("a",))), 2)
        self.assertGreaterEqual(world.received_events.count(("key_pressed_a", None)), 2)

    async def test_focus_switch_dispatches_focus_and_focus_lost(self):
        App.reset(unittest=True, file=__file__)
        world = World(80, 80)
        first = FocusActor((10, 10), world=world)
        second = FocusActor((20, 20), world=world)
        world.detect_actors = Mock(side_effect=[[first], [second]])

        await self._run_frame(
            world,
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1})],
            mouse_pos=(10, 10),
        )
        await self._run_frame(
            world,
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1})],
            mouse_pos=(20, 20),
        )

        self.assertEqual(first.received_events, ["focus", "focus_lost"])
        self.assertEqual(second.received_events, ["focus"])

    async def test_mouse_motion_dispatches_enter_and_leave(self):
        App.reset(unittest=True, file=__file__)
        world = World(80, 80)
        actor = HoverActor((10, 10), world=world)
        world.camera.is_in_screen = Mock(return_value=True)

        actor.hovered = True
        await self._run_frame(
            world,
            [pygame.event.Event(pygame.MOUSEMOTION, {})],
            mouse_pos=(10, 10),
        )

        actor.hovered = False
        await self._run_frame(
            world,
            [pygame.event.Event(pygame.MOUSEMOTION, {})],
            mouse_pos=(10, 10),
        )

        self.assertEqual(actor.received_events, ["enter", "leave"])

    async def test_button_message_reaches_world_without_visual_test(self):
        App.reset(unittest=True, file=__file__)
        world = MessageWorld()
        toolbar = Toolbar()
        world.camera.add_right(toolbar, size=120)
        button = toolbar.add(Button("Start Rocket"))

        button.on_clicked_left((5, 5))
        await self._run_frame(world, [])

        self.assertIn("Start Rocket", world.messages)


if __name__ == "__main__":
    unittest.main()