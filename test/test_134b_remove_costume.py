from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test134b(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                actor = Actor(origin = "topleft")
                removed = actor.remove_costume()
                assert actor.costume_count == 0
                actor.add_costume((255,0,0,255))
                assert actor.costume_count == 1

            return world
        
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1]
        QUIT_FRAME = 1
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

        

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()
