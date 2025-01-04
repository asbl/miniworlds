from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1204(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                
                t1 = Actor((10,10), origin = "topleft")
                t1.color = (255,255,255)
                t2 = Actor((20,10), origin = "topleft")
                t2.color = (255,255,255)
                t3 = Actor((10,10), origin = "topleft")
                t3.color = (255,255,255)
                assert(len(t3.detect_all())==2)
                assert(len(t1.detect_all())==2)
                assert(t1 in t3.detect_all())
                assert(t2 in t3.detect_all())
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1]
        QUIT_FRAME = 1
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()
