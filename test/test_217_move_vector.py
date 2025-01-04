from miniworlds import App, World, Actor, Vector
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test217(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                t = Actor(origin = "topleft")
                @t.register
                def act(self):
                    self.move_vector(Vector(1,1))
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