from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test221(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World()

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                t1 = Actor((100, 100))
                t1.add_costume("images/alien1.png")

                t2 = Actor((200, 200))
                t2.add_costume("images/alien1.png")
                t2.is_rotatable = False

                @t1.register
                def act(self):
                    self.move()
                    self.direction += 1

                @t2.register
                def act(self):
                    self.move()
                    self.direction += 1

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 10, 20, 40, 60]
        QUIT_FRAME = 60
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
