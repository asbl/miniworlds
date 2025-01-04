from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test306(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                background = world.add_background("images/1.png")
                background.add_image("images/2.png")
                background.animate()
                background.loop = True
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 5, 10, 15, 20]
        QUIT_FRAME = 21 
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