from __future__ import annotations

import unittest

from miniworlds import Actor, App, World


class MessageReceiver(Actor):
    def __init__(self, position=(0, 0), *args, **kwargs):
        self.received_payloads = []
        self.received_messages = []
        super().__init__(position, *args, **kwargs)


class TestActorMessages(unittest.IsolatedAsyncioTestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    async def test_actor_register_message_receives_payload(self):
        App.reset(unittest=True, file=__file__)
        world = World(100, 100)
        sender = Actor((10, 10), world=world)
        receiver = MessageReceiver((20, 20), world=world)

        @receiver.register_message("boost")
        def on_boost(self, payload):
            self.received_payloads.append(payload)

        sender.world.send_message("boost", {"speed": 4})
        await world.app._update()

        self.assertEqual(receiver.received_payloads, [{"speed": 4}])

    async def test_actor_send_message_reaches_generic_on_message_handler(self):
        App.reset(unittest=True, file=__file__)
        world = World(100, 100)
        sender = Actor((10, 10), world=world)
        receiver = MessageReceiver((20, 20), world=world)

        @receiver.register
        def on_message(self, message):
            self.received_messages.append(message)

        sender.send_message("hello")
        await world.app._update()

        self.assertEqual(receiver.received_messages, ["hello"])
