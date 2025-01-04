from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test224(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 400)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world = World(100, 100)
                t = Actor((50, 50))
                t.add_costume("images/arrow.png")
                t.size = (100,100)

                @t.register
                def act(self):
                    t.turn_left(1)
            return world
            
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,10,20]
        QUIT_FRAME = 20
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