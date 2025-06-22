from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1101(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                arr = world.background.to_colors_array()
                print(arr)
                for x in range(len(arr)):
                    for y in range(len(arr[0])):
                        arr[x][y][0] = ((x +1 ) / world.width) * 255
                        arr[x][y][1] = ((y +1 ) /world.width) * 255
                world.background.from_array(arr)
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
