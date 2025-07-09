from miniworlds import App, World, Actor, timer
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test131(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 400)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                for i in range(50):
                    Actor((random.randint(0,world.width), random.randint(0,world.height)))

                @timer(frames = 10)
                def clean():
                    world._clear()
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [11]
        QUIT_FRAME = 12
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()