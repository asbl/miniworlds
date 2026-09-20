from __future__ import annotations

import unittest
import warnings

from miniworlds import Actor, App, World
from miniworlds.base.exceptions import (
    MissingSuperInitError,
    NotImplementedOrRegisteredError,
    RegisterError,
    WrongArgumentsError,
)


class TestInheritanceHooks(unittest.TestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def _new_world(self) -> World:
        App.reset(unittest=True, file=__file__)
        return World(100, 100)

    # --- No-op hooks exist on the base classes ---

    def test_actor_has_act_and_on_setup_hooks(self):
        self.assertTrue(callable(getattr(Actor, "act", None)))
        self.assertTrue(callable(getattr(Actor, "on_setup", None)))

    def test_world_has_act_hook(self):
        world = self._new_world()
        self.assertTrue(callable(getattr(type(world), "act", None)))

    def test_super_act_and_on_setup_work_in_direct_subclass(self):
        class SubActor(Actor):
            def call_super_act(self):
                return super().act()

            def call_super_on_setup(self):
                return super().on_setup()

        world = self._new_world()
        actor = SubActor((10, 10), world=world)
        self.assertIsNone(actor.call_super_act())
        self.assertIsNone(actor.call_super_on_setup())

    def test_super_act_works_in_world_subclass(self):
        class SubWorld(World):
            def call_super_act(self):
                return super().act()

        App.reset(unittest=True, file=__file__)
        world = SubWorld(100, 100)
        self.assertIsNone(world.call_super_act())

    # --- Registration neutrality (performance guard) ---

    def test_plain_actor_does_not_register_act(self):
        world = self._new_world()
        Actor((1, 1), world=world)
        self.assertNotIn("act", world.event_manager.registered_events)

    def test_subclass_without_act_does_not_register_act(self):
        class NoActActor(Actor):
            pass

        world = self._new_world()
        NoActActor((1, 1), world=world)
        self.assertNotIn("act", world.event_manager.registered_events)

    def test_subclass_with_act_registers_exactly_one_handler(self):
        class ActingActor(Actor):
            def act(self):
                pass

        world = self._new_world()
        ActingActor((1, 1), world=world)
        self.assertIn("act", world.event_manager.registered_events)
        handlers = world.event_manager.registry._event_handlers["act"]
        self.assertEqual(len(handlers), 1)

    def test_plain_actors_do_not_fill_reload_costumes_queue(self):
        world = self._new_world()
        for index in range(50):
            Actor((index % 50, index // 50), world=world)
        self.assertEqual(len(world._mainloop.reload_costumes_queue), 0)

    # --- on_setup hook semantics ---

    def test_subclass_on_setup_is_called_once_on_world_entry(self):
        calls = []

        class SetupActor(Actor):
            def on_setup(self):
                calls.append(self.actor_id)

        world = self._new_world()
        SetupActor((1, 1), world=world)
        self.assertEqual(len(calls), 1)

    def test_child_inherits_parent_on_setup(self):
        calls = []

        class ParentActor(Actor):
            def on_setup(self):
                calls.append("parent")

        class ChildActor(ParentActor):
            pass

        world = self._new_world()
        ChildActor((1, 1), world=world)
        self.assertEqual(calls, ["parent"])

    def test_super_on_setup_chains_to_parent(self):
        calls = []

        class ParentActor(Actor):
            def on_setup(self):
                calls.append("parent")

        class ChildActor(ParentActor):
            def on_setup(self):
                super().on_setup()
                calls.append("child")

        world = self._new_world()
        ChildActor((1, 1), world=world)
        self.assertEqual(calls, ["parent", "child"])

    def test_registered_on_setup_is_called_immediately(self):
        calls = []
        world = self._new_world()
        actor = Actor((1, 1), world=world)

        @actor.register
        def on_setup(self):
            calls.append(1)

        self.assertEqual(calls, [1])

    # --- Error messages ---

    def test_missing_super_init_raises_helpful_error(self):
        class NoSuperInitActor(Actor):
            def __init__(self, position):
                self.my_attribute = 42

        with self.assertRaises(MissingSuperInitError) as ctx:
            NoSuperInitActor((10, 10))

        message = str(ctx.exception)
        self.assertIn("super().__init__()", message)
        self.assertIn("NoSuperInitActor", message)

    def test_missing_super_init_error_on_position_access(self):
        class NoSuperInitActor(Actor):
            def __init__(self, position):
                self.my_attribute = 42

        with self.assertRaises(MissingSuperInitError):
            NoSuperInitActor((10, 10))

    def test_super_call_on_event_hook_is_silent(self):
        world = self._new_world()

        class DirectActor(Actor):
            def on_key_down(self, key):
                super().on_key_down(key)

        actor = DirectActor((1, 1), world=world)
        self.assertIsNone(actor.on_key_down(["a"]))

    def test_direct_call_on_unimplemented_hook_raises_helpful_error(self):
        world = self._new_world()
        actor = Actor((1, 1), world=world)

        with self.assertRaises(NotImplementedOrRegisteredError) as ctx:
            actor.on_key_down(["a"])

        message = str(ctx.exception)
        self.assertIn("on_key_down", message)
        self.assertIn("not overwritten or registered", message)
        self.assertIn("class Actor(Actor):", message)

    def test_direct_call_on_subclass_without_override_raises(self):
        world = self._new_world()

        class NoOverrideActor(Actor):
            pass

        actor = NoOverrideActor((1, 1), world=world)
        with self.assertRaises(NotImplementedOrRegisteredError):
            actor.on_mouse_left((10, 10))

    def test_register_error_suggests_close_event_name(self):
        world = self._new_world()
        actor = Actor((1, 1), world=world)

        with self.assertRaises(RegisterError) as ctx:

            @actor.register
            def on_key_dwon(self, key):
                pass

        message = str(ctx.exception)
        self.assertIn("on_key_dwon", message)
        self.assertIn("Did you mean `on_key_down`?", message)

    def test_wrong_signature_act_raises_wrong_arguments_error(self):
        class WrongSignatureActor(Actor):
            def act(self, unexpected_arg):
                pass

        world = self._new_world()
        WrongSignatureActor((1, 1), world=world)

        with self.assertRaises(WrongArgumentsError) as ctx:
            world.event_manager.act_all()

        message = str(ctx.exception)
        self.assertIn("def act(self):", message)

    def test_wrong_signature_on_setup_raises_on_world_entry(self):
        class SetupWithArgsActor(Actor):
            def on_setup(self, arg):
                pass

        with self.assertRaises(WrongArgumentsError) as ctx:
            SetupWithArgsActor((1, 1), world=self._new_world())

        message = str(ctx.exception)
        self.assertIn("def on_setup(self):", message)

    def test_legitimate_handler_signatures_still_work(self):
        received = []

        class LegitActor(Actor):
            def act(self):
                received.append("act")

            def on_key_down(self, key):
                received.append(("key", tuple(key)))

            def flexible(self, *args):
                received.append(("flexible", args))

            def with_default(self, speed=1):
                received.append(("default", speed))

        world = self._new_world()
        actor = LegitActor((1, 1), world=world)
        world.event_manager.act_all()
        actor.on_key_down(["a"])
        actor.flexible(1, 2)
        actor.with_default()

        self.assertIn("act", received)
        self.assertIn(("key", ("a",)), received)
        self.assertIn(("flexible", (1, 2)), received)
        self.assertIn(("default", 1), received)


class TestEventTypoWarnings(unittest.TestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def _new_world(self) -> World:
        App.reset(unittest=True, file=__file__)
        return World(100, 100)

    def test_typo_in_actor_subclass_warns_with_suggestion(self):
        class TypoActor(Actor):
            def on_key_dwon(self, key):
                pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            world = self._new_world()
            TypoActor((1, 1), world=world)

        messages = [str(warning.message) for warning in caught]
        typo_warnings = [m for m in messages if "on_key_dwon" in m]
        self.assertEqual(len(typo_warnings), 1)
        self.assertIn("Did you mean 'on_key_down'?", typo_warnings[0])
        self.assertIn("TypoActor", typo_warnings[0])

    def test_typo_warning_is_emitted_once_per_class(self):
        class TypoActor(Actor):
            def on_key_dwon(self, key):
                pass

        world = self._new_world()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            TypoActor((1, 1), world=world)
        self.assertEqual(len([w for w in caught if "on_key_dwon" in str(w.message)]), 1)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            TypoActor((2, 2), world=world)
        self.assertEqual(
            len([w for w in caught if "on_key_dwon" in str(w.message)]), 0
        )

    def test_custom_on_method_without_close_match_stays_silent(self):
        class HelperActor(Actor):
            def on_my_helper(self):
                pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            world = self._new_world()
            HelperActor((1, 1), world=world)

        typo_warnings = [
            str(warning.message)
            for warning in caught
            if "looks like an event handler" in str(warning.message)
        ]
        self.assertEqual(typo_warnings, [])

    def test_typo_in_world_subclass_warns_with_suggestion(self):
        class TypoWorld(World):
            def on_key_dwon(self, key):
                pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            TypoWorld(100, 100)

        messages = [str(warning.message) for warning in caught]
        typo_warnings = [m for m in messages if "on_key_dwon" in m]
        self.assertEqual(len(typo_warnings), 1)
        self.assertIn("Did you mean 'on_key_down'?", typo_warnings[0])
        self.assertIn("TypoWorld", typo_warnings[0])

    def test_world_register_typo_raises_register_error(self):
        world = self._new_world()

        with self.assertRaises(RegisterError) as ctx:

            @world.register
            def on_key_dwon(self, key):
                pass

        message = str(ctx.exception)
        self.assertIn("on_key_dwon", message)
        self.assertIn("Did you mean `on_key_down`?", message)

    def test_valid_event_handlers_do_not_warn(self):
        class ValidActor(Actor):
            def act(self):
                pass

            def on_key_down(self, key):
                pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            world = self._new_world()
            ValidActor((1, 1), world=world)

        typo_warnings = [
            str(warning.message)
            for warning in caught
            if "looks like an event handler" in str(warning.message)
        ]
        self.assertEqual(typo_warnings, [])


if __name__ == "__main__":
    unittest.main()
