from miniworlds import App, TiledWorld, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1917a(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.add_background("images/soccer_green.jpg")
                world.columns=20
                world.rows=8
                world.tile_size=40
                world.background.grid = True

                player = Actor(position=(3, 4))
                player.add_costume("images/char_blue.png")
                player.border = 1
                print(player.size)
                print(player.position, player.direction)
                print(player.image)
                player.orientation = -90
                @player.register
                def on_key_down(self, key):
                    self.move()
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
