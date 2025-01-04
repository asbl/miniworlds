from miniworlds import App, World, Actor, Rectangle, ActionTimer
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test117(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                player = Actor()
                player.origin = "topleft"
                rectangle = Rectangle((80, 70), 60, 50, origin = "topleft")
                ActionTimer(20, player.remove, None)
                ActionTimer(40, rectangle.remove, None)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 22, 41]
        QUIT_FRAME = 42
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)



    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()