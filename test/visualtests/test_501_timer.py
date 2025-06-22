from miniworlds import App, World, Actor, TiledWorld, LoopActionTimer
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test501(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.columns=8
                world.rows=8
                world.tile_size=40
                world.add_background("images/soccer_green.jpg")
                world.add_background("images/space.jpg")
                world.speed = 30

                player = Actor(position=(3, 4))
                player.add_costume("images/char_blue.png")
                player.costume.orientation = - 90
                LoopActionTimer(48, player.move, 1)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,2,3]
        QUIT_FRAME = 4
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
