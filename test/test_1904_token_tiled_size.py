from miniworlds import App, TiledWorld, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1904(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                actor = Actor((1,1))
                actor = Actor((2,2))
                actor.size = (0.5, 0.5)
                actor = Actor((3,3))
                actor.size = (1.5, 1.5)
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