from miniworlds import App, World, Actor, Line, Rectangle, Ellipse, Circle
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test702(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(800, 600)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                shapes = []
                x = 0
                
                l = Line((0,0), (400, 300))
                shapes.append(l)

                r = Rectangle((400,300),400,300)
                r.center = r.position
                shapes.append(r)

                e = Ellipse((400,300), 80, 30)
                e.position = (0,0)
                shapes.append(e)

                c = Circle((400,300), 20)
                shapes.append(c)

                @world.register
                def act(self):
                    r.width = r.width + 1
                    c.radius += 1
                    l.end_position = (l.end_position[0], l.end_position[1]+1)
                    e.height = e.height + 1
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

