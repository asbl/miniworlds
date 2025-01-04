from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test222(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 400)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                actor = Actor((50,50),)
                actor.add_costume("images/ball.png")
                actor.direction = 10

                @actor.register
                def act(self):
                    self.move()
                    borders = self.detect_borders()
                    if borders:
                        self.bounce_from_border(borders)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES =  [1, 10, 30, 40, 50, 60, 90]
        QUIT_FRAME = 90
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
