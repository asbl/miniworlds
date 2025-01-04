from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test133(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(210,80)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.default_border_color = (0,0, 255)
                world.default_border = 1

                t = Actor((10,10), origin = "topleft")

                t2 = Actor ((60, 10), origin = "topleft")
                t2.border_color = (0,255, 0)
                t2.border = 5 # overwrites default border

                t3 = Actor ((110, 10), origin = "topleft")
                t3.border = None # removes border

                t4 = Actor ((160, 10), origin = "topleft")
                t4.add_costume("images/player.png") # border for sprite

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