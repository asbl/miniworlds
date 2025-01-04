from miniworlds import App, World, Actor, Text, Line
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1501(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(640, 500)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                Line((320,0), (320, 500))

                t1 = Text((320,100), "Test1")
                t1.origin = "center"
                print(t1.width)
                t1.text = "Test1: " + str(t1.width)
                print(t1.width)
                t1.border = 1

                t2 = Text((320,150), "Test2")
                t2.text = "Test2: " + str(t2.width)
                t2.font_size = 50
                t2.border = 1
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