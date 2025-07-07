from miniworlds import App, World, Polygon, Actor, Line, Rectangle, Ellipse, Circle
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test708(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 200)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.draw.default_fill_color = (255,255,255,100)

                # White ellipse at left center
                Ellipse.from_topleft((0,100), 200, 100)

                # Red Ellipse in the center of the screen
                world.draw.default_fill_color = (255,0,0,100)
                Ellipse.from_center((100,100),20, 10)

                # Green Ellipse - top left at center of screen
                world.draw.default_fill_color = (0,255,0,100)
                e = Ellipse.from_center((100,100),10, 10)

                # Green Ellipse at center - top left at center of screen
                world.draw.default_fill_color = (0,255,0,50)
                e = Ellipse.from_center((100,100),18.1, 18.1)
                
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