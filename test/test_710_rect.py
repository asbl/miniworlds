from miniworlds import App, World, Polygon, Actor, Line, Rectangle, Ellipse, Circle
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test710(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 200)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                
                world.fill_color = (0,0,0)
                world.default_fill_color = (255,255,255,255)
                
                center= (100, 100)

                # R1
                Rectangle((10,100), 180, 80)
                r = Rectangle(center, 180, 80)
                r.turn_left(45)

                # R2
                world.default_fill_color = (255,0,0,100)
                Rectangle.from_center(center,20, 10)
                
                # R3
                world.default_fill_color = (0,255,0,100)
                e = Rectangle(center,10, 10)
                e.center = e.position

                # R4
                world.default_fill_color = (255,255,0,50)
                e = Rectangle(center,30, 30)
                e.center = e.position
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
