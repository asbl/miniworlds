from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test118(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                actor = Actor(origin = "topleft")
                costume = actor.add_costume("images/1.png")
                costume.add_image("images/2.png")
                assert len(actor.costumes) == 1
                assert len(actor.costume.images) == 2
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

if __name__ == "__main__":
    unittest.main()