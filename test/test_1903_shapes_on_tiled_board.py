from miniworlds import App, TiledWorld, Actor, Circle
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1903(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.grid = True
                circle = Circle((0,0))
                print(circle.position, circle.size)
                @circle.register
                def act(self):
                    print(circle.position, circle.rect)
                    self.x += 1
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 2, 3, 4, 5]
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
