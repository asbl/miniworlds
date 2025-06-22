from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test220(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World()

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                actor = Actor(origin="topleft")
                actor.add_costume("images/alien1.png")
                actor.height = 400
                actor.width = 100
                actor.is_rotatable = False

                @actor.register
                def act(self):
                    if self.world.frame % 20 == 0:
                        print("flip")
                        if self.costume.is_flipped:
                            self.costume.is_flipped = False
                        else:
                            self.costume.is_flipped = True

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 21, 41]
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
