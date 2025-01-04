from miniworlds import App, World, Actor, TiledWorld
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test210(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.columns=5
                world.rows=5
                world.tile_size=40
                world.add_background("images/soccer_green.jpg")
                world.add_background("images/space.jpg")
                world.speed = 30

                player1 = Actor(position=(3, 4))
                player1.add_costume("images/char_blue.png")
                player1.costume.orientation = - 90

                @player1.register
                def on_detecting_actor(self, actor):
                    if actor == player2 and self.world.frame == 1:
                        assert(actor == player2)

                player2 = Actor(position=(3, 4))
                player2.add_costume("images/char_blue.png")
                player2.costume.orientation = - 90
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
