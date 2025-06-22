from miniworlds import App, World, Actor, TiledWorld, timer
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test154(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld(2,2)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                actor = Actor(origin = "topleft")
                
                @timer(frames = 60)
                def hide():
                    print("test output >>> HIDE", self.frame)
                    actor.hide()

                @timer(frames = 120)
                def show():
                    print("test output >>> SHOW", self.frame)
                    actor.show()
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 4, 7] # multiplied by 20
        QUIT_FRAME = 9
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