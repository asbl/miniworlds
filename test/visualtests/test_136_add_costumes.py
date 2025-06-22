from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test136(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(100,60)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                actor = Actor((10,10), origin = "topleft")
                world.speed = 30
                costume1 = actor.add_costume((255,255,0))
                costume2 = actor.add_costume((255,0,255))
                @actor.register
                def act(self):
                    if self.costume == costume1:
                        self.switch_costume(costume2)
                    else:
                        self.switch_costume(costume1)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 2, 3, 4, 5, 6]
        QUIT_FRAME = 7
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()

