from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from miniworlds import TiledWorld, Toolbar, Console, Actor, Button, Label, PagerHorizontal, Text
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test165(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.size = (600,300)

                text = Text.from_topleft((200,100), "Hello World")
                text.border = 1
                text.font_size = 100
                text.direction = 5

            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1]
        QUIT_FRAME = 5
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()