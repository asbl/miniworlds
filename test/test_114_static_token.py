from miniworlds import App, World, Actor, CostumeOutOfBoundsError, TiledWorld
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test114(unittest.TestCase):

    def setUp(self):
        def test_code():
            # Here comes your code
            class MyWorld(TiledWorld):
                def setup_environment(self, test):
                    self.columns = 5
                    self.rows = 5
                    self.tile_size = 40
                    self.add_background("images/soccer_green.jpg")
                    self.border_color = (0,0,0,255)
                    actor = Actor()
                    actor.origin = "topleft"
                    actor.position = (3,4)
                    actor.border = 2
                    actor.add_costume("images/player.png")
            world = MyWorld()
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

