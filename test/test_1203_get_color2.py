from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1203(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.background.draw((255,0,0), (200,0), 20, 400)

                for i in range(7):
                    actor = Actor((10,i*60), origin = "topleft")
                    actor.range = i * 10
                    @actor.register
                    def act(self):
                        if not self.detect_color_at(self.direction, self.range) == (255,0,0,255):
                            self.direction = "right"
                            self.move()
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,20,40,60,80,120,140,150,170]
        QUIT_FRAME = 170
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()
