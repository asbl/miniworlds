from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test304(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(80,40)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                robo = Actor(origin = "topleft")
                robo.costume.add_images(["images/1.png", "images/2.png","images/3.png","images/4.png"])
                robo.costume.animation_speed = 20
                robo.costume.animate()
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [110,20,30,40,50,60,70,80]
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