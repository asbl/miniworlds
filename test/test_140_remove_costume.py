from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test140(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                actor = Actor(origin = "topleft")
                actor.remove_costume()
                assert actor.costume_count == 0
                actor.add_costume((255,0,0))
                assert actor.costume_count == 1
                actor.add_costume((0,255,0))
                assert actor.costume_count == 2
                actor.remove_costume()
                assert actor.costume_count == 1
                actor.remove_costume()
                assert actor.costume_count == 0
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



        return world

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
