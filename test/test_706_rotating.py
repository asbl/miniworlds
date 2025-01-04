from miniworlds import App, World, Polygon, Actor, Line, Rectangle, Ellipse, Circle
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test706(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(800, 600)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                shapes = []
                l = Line((0,0), (400, 300), origin = "topleft")
                shapes.append(l)

                r = Rectangle((0,0),400,300, origin = "topleft")
                r.center = (400,300)
                shapes.append(r)

                e = Ellipse((400,300), 80, 30, origin = "topleft")
                e.position = (0,0)
                shapes.append(e)

                p = Polygon([(400,300), (400,450), (600,450)], origin = "topleft")
                shapes.append(p)
                for shape in shapes:
                    shape.switch_origin("center")
                @world.register
                def act_test(self):
                    for shape in shapes:
                        shape.turn_right(1)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,2,3,4,5,6,7,8]
        QUIT_FRAME = 9
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