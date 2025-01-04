from miniworlds import App, World, Actor, CostumeOutOfBoundsError
import miniworlds
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test701(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = miniworlds.World(800, 600)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                miniworlds.Line((0,0), (400, 300), origin ="topleft")

                e = miniworlds.Ellipse((400,300), 400, 300, origin ="topleft")
                r = miniworlds.Rectangle((400,300),400,300, origin ="topleft")

                r.switch_origin("center")
                r.center = r.topleft
                r.direction= 5

                l2 = miniworlds.Line((0,0), (400, 300), origin ="topleft")
                l2.start_position = (100,200)

                r2 = miniworlds.Rectangle((400,300),40,30, origin ="topleft")
                r2.center = (0,0)

                r3 = miniworlds.Rectangle((400,300),80,30, origin ="topleft")
                r3.position = (0,0)

                r4 = miniworlds.Rectangle((60,120),80,30, origin ="topleft")
                r4.width = 600

                r5 = miniworlds.Rectangle((60,120),80,30, origin ="topleft")
                r5.height = 600

                e2 = miniworlds.Ellipse((400,300), 40, 30, origin ="topleft")
                e2.center = (0,0)

                e3 = miniworlds.Ellipse((400,300), 80, 30, origin ="topleft")
                e3.position = (0,0)

                e4 = miniworlds.Ellipse((60,120),80,30, origin ="topleft")
                e4.width = 600

                e5 = miniworlds.Ellipse((60,120),80,30, origin ="topleft")
                e5.height = 600
                #world.fill_color=(255,0,0,255)
                p = miniworlds.Polygon([(400,300), (400,450), (600,450)], origin ="topleft")
                p.fill_color = (100,0,0,100)
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

