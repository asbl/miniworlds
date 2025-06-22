from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test159(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(400,600)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                self.init_test()     
                self.add_background((0,255,0,255))
                self.actor = Actor((10,10), origin = "topleft")

                @world.register
                def act_test(self):
                    if self.frame == 20:
                        self.actor.x += 100
                    if self.frame == 40:
                        self.reset()
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,20,21, 40, 41]
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