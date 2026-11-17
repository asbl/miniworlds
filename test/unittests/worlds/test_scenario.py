"""Greenfoot-style scenario control against a real world."""
from __future__ import annotations

import unittest

from miniworlds import Actor, App, World
from miniworlds.tools.scenario import MAX_SPEED, MIN_SPEED, Scenario


class Walker(Actor):
    acts = 0

    def act(self):
        Walker.acts += 1


class TestScenario(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        Walker.acts = 0
        self.world = World(200, 200)
        self.scenario = Scenario(self.world)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    async def frames(self, count):
        for _ in range(count):
            await self.world.app._update()

    async def test_act_runs_exactly_one_frame_and_stays_paused(self):
        self.scenario.place(Walker, 50, 50)
        await self.frames(3)
        self.assertEqual(Walker.acts, 0)
        self.scenario.act()
        await self.frames(3)
        self.assertEqual(Walker.acts, 1)
        self.assertTrue(self.world.is_paused)

    async def test_run_resumes_and_pause_stops(self):
        self.scenario.place(Walker, 50, 50)
        self.scenario.run()
        await self.frames(3)
        self.assertGreaterEqual(Walker.acts, 2)
        self.scenario.pause()
        seen = Walker.acts
        await self.frames(3)
        self.assertEqual(Walker.acts, seen)

    def test_place_pick_move_delete(self):
        handle = self.scenario.place(Walker, 100, 80)
        self.assertEqual(self.scenario.resolve(handle).center, (100, 80))
        self.assertEqual(self.scenario.pick(100, 80), handle)
        self.assertIsNone(self.scenario.pick(5, 5))
        self.scenario.move(handle, 40, 60)
        self.assertEqual(self.scenario.resolve(handle).center, (40, 60))
        self.scenario.delete(handle)
        self.assertEqual(len(self.world.actors), 0)

    def test_place_rejects_non_actor_classes(self):
        with self.assertRaises(TypeError):
            self.scenario.place(dict, 1, 1)
        with self.assertRaises(TypeError):
            self.scenario.place(Walker(), 1, 1)

    def test_place_supports_custom_init_with_extra_state(self):
        class Plain(Actor):
            def __init__(self, position=(0, 0)):
                self.energy = 3
                super().__init__(position)

        handle = self.scenario.place(Plain, 70, 30)
        actor = self.scenario.resolve(handle)
        self.assertEqual((actor.center, actor.energy), ((70, 30), 3))

    def test_speed_is_clamped_and_scales_fps(self):
        base = self.world.fps
        self.assertEqual(self.scenario.set_speed(2), 2.0)
        self.assertEqual(self.world.fps, base * 2)
        self.assertEqual(self.scenario.set_speed(1000), MAX_SPEED)
        self.assertEqual(self.scenario.set_speed(0), MIN_SPEED)
        with self.assertRaises(TypeError):
            self.scenario.set_speed("fast")

    def test_speed_follows_a_frame_rate_the_program_changed(self):
        self.world.fps = 20
        self.scenario.set_speed(2)
        self.assertEqual(self.world.fps, 40)
        self.world.fps = 10  # the program lowers the base rate itself
        self.scenario.set_speed(2)
        self.assertEqual(self.world.fps, 20)
        self.scenario.set_speed(1)
        self.assertEqual(self.world.fps, 10)

    def test_handles_of_removed_actors_are_released(self):
        first = self.scenario.place(Walker, 10, 10)
        handles = [self.scenario.place(Walker, 20 + i, 20) for i in range(40)]
        for handle in handles[:35]:
            self.world.invoke(self.scenario.resolve(handle).remove)
        # registering past the threshold (64) prunes the dead actors
        for i in range(30):
            self.scenario.place(Walker, 5 + i, 5)
        with self.assertRaises(LookupError):
            self.scenario.resolve(handles[0])
        self.assertIsNotNone(self.scenario.resolve(first))
        self.assertIsNotNone(self.scenario.resolve(handles[-1]))
        self.assertLess(len(self.scenario.session._objects), 50)

    def test_deleted_handles_are_not_reused(self):
        first = self.scenario.place(Walker, 10, 10)
        self.scenario.delete(first)
        second = self.scenario.place(Walker, 10, 10)
        self.assertNotEqual(first, second)
        with self.assertRaises(LookupError):
            self.scenario.resolve(first)

    def test_snapshot_lists_actors_with_stable_handles(self):
        handle = self.scenario.place(Walker, 10, 20)
        first = self.scenario.snapshot()
        second = self.scenario.snapshot()
        self.assertEqual(first["actors"][0]["handle"], handle)
        self.assertEqual(first["actors"], second["actors"])
        self.assertEqual(first["actors"][0]["cls"], "Walker")
        self.assertTrue(first["world"]["paused"])

    def test_export_setup_code_recreates_actors(self):
        a = self.scenario.place(Walker, 100, 80)
        self.scenario.resolve(a).direction = 90
        self.scenario.place(Walker, 30, 40)
        code = self.scenario.export_setup_code(indent="")
        self.assertEqual(
            code.splitlines(),
            [
                "walker_1 = Walker((100, 80))",
                "walker_1.direction = 90",
                "walker_2 = Walker((30, 40))",
            ],
        )
