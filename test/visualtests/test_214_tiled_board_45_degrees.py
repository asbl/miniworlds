from miniworlds import App, World, Actor, TiledWorld
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test214(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                t = Actor()
                t.position = (3, 3)
                x = 0
                @world.register
                def act_test(self):
                    nonlocal x
                    x = x + 1
                    if x < 5:
                        t.direction = 135
                        t.move()
                    if x > 5:
                        t.move_in_direction(45)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,2,3,4,5,6]
        QUIT_FRAME = 6
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
