from miniworlds import App, World, TiledWorld, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test122(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld(4,4)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.tile_margin = 10
                background = world.add_background("images/stone.png")
                background.is_textured = True
                actor = Actor()
                background.grid = True
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