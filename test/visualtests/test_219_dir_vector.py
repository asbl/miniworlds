from miniworlds import App, World, Actor, Rectangle, Vector
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test219(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(400, 400)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                player = Rectangle((200,200),40, 40)
                player.speed = 1
                player.direction = 80

                @player.register
                def act(self):
                    v1 = Vector.from_actor_direction(self)
                    v1.rotate(-1)
                    self.direction = v1
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 20, 40]
        QUIT_FRAME = 41
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