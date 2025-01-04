from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test108(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(400, 400)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.add_background((100, 0, 0, 255))
                a = Actor()
                a.position = (0,0)
                b = Actor()
                b.topleft = (100,100)
                c = Actor()
                c.position = (200,200)
                d = Actor()
                d.center = (250,250)
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



    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
