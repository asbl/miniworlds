from miniworlds import App, World, Actor, Circle
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test225(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(800, 600)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                a = Circle()
                a.direction  = 45
                assert(a.direction == 45)
                assert(a.direction_at_unit_circle == 45)
                a.direction  = 0
                assert(a.direction == 0)
                assert(a.direction_at_unit_circle == 90)
                a.direction  = -90
                assert(a.direction == -90)
                print(a.direction_at_unit_circle)
                assert(a.direction_at_unit_circle == -180)
                a.direction = 180
                print(a.direction)
                assert(abs(a.direction) == 180)
                assert(a.direction_at_unit_circle == -90)

                a.direction_at_unit_circle = -90
                assert(abs(a.direction) == 180)
                print(a.direction_at_unit_circle)
                assert(a.direction_at_unit_circle == -90)

                a.direction_at_unit_circle = -180
                print(a.direction)
                assert(a.direction == -90)
                print(a.direction_at_unit_circle)
                assert(a.direction_at_unit_circle == -180)
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
