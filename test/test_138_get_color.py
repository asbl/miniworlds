from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test138(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(100, 60)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                self.add_background((255, 0, 0))
                assert self.get_color_from_pixel((5, 5)) == (255, 0, 0, 255)
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
