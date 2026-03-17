from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from miniworlds import TiledWorld, Toolbar, Console, Actor, Button, Label, PagerHorizontal, Text
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class TestDefaultWorldDrawColors(unittest.TestCase):
    SCREENSHOT_TITLE = "Test166"

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.size = (600,300)
                world.draw.default_is_filled = True
                world.draw.default_stroke_color = (100, 150, 200)
                world.draw.default_border = 10
                world.draw.fill_color = (0, 50, 100)
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