from miniworlds import App, World, Actor, CostumeOutOfBoundsError, timer
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test125(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                actor = Actor()
                actor.origin = "topleft"

                world.add_background("images/1.png")
                world.add_background((255, 0, 0, 255))
                world.add_background("images/2.png")

                @timer(frames = 20)
                def switch():
                    world.switch_background(0)

                @timer(frames = 40)
                def switch():
                    world.switch_background(1)
                    
                @timer(frames = 60)
                def switch():
                    world.switch_background(2)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,21, 41, 61]
        QUIT_FRAME = 62
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()

