from miniworlds import App, World, Polygon, Actor, Line, Rectangle, Ellipse, Circle
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test707(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World(200, 200)

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.default_fill_color = (255, 255, 255, 100)

                # White circle in center of world
                Circle((100, 100), 50)

                # Red circle with center at topleft position at center of world
                world.default_fill_color = (255, 0, 0, 100)
                b = Circle.from_topleft((100, 100), 50)
                # b.direction = 10
                print("###>set to center", b.center)

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
