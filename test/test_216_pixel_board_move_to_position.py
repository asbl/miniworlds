from miniworlds import App, World, Actor, World
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test216(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World()

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.columns = 400
                world.rows = 400
                player = Actor(origin="topleft")
                player.add_costume("images/player_1.png")
                player.position = (200, 200)

                @player.register
                def act(self):
                    self.move_towards((280, 260))

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 10, 30, 40, 80]
        QUIT_FRAME = 81

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
