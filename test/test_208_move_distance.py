from miniworlds import App, World, Actor, World
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test208(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 200)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                tkn = Actor((0,0), origin = "topleft")
                tkn.move_right(1)
                tkn2 = Actor((0,40), origin = "topleft")
                tkn2.move_right(40)
                tkn3 = Actor((0,80), origin = "topleft")
                tkn3.move_right(80)
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
