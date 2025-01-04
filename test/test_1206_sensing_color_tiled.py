from miniworlds import App, TiledWorld, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1206(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld(6,6)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                print(world.rows, world.columns)
                assert world.rows == 6
                assert world.columns == 6
                for x in range(world.rows):
                    for y in range(world.columns):
                        color = (x * y) / (world.rows * world.columns) * 255
                        world.background.draw((color, color, color), (x * world.tile_size,y * world.tile_size), 40,40)
                actor = Actor((3,3), origin = "topleft")
                #print(actor.sensing_color((63,63,63)))
                #print(actor.sense_color_at(distance = 1, direction = 90))
                assert(actor.detect_color((63,63,63)) is True)
                assert(actor.detect_color_at(distance = 1, direction = 90) == (85,85,85,255) )
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
