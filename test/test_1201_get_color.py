from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1201(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 400)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                print(world.background)
                world.add_background((255, 0, 100))
                world.background.dirty = 1
                print(world.background)
                actor = Actor((10,10))
                print(actor.detect_color((255,0,0)))
                print(actor.detect_color_at())
                #assert(actor.detect_color((255,0,0)) is True)
                #assert(actor.detect_color_at() == (255,0,0,255))
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1]
        QUIT_FRAME = 2
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
