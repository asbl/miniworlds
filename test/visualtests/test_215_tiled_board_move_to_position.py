from miniworlds import App, World, Actor, TiledWorld
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test215(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.columns = 8
                world.rows = 8
                world.speed = 30
                player = Actor()
                player.add_costume("images/player_1.png")
                player.position = (4, 4)

                @player.register
                def act(self):
                    self.move_towards((7, 7))
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,2,3,4,5]
        QUIT_FRAME = 5
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