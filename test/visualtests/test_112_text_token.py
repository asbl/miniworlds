from miniworlds import App, World, Actor, Text, Number
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test112(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 200)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.default_fill_color = (0,255,255,255)

            actor = Text((0,0), text = "Hello World!", origin = "topleft")
            actor.auto_size = "font"

            actor2 = Text((0,60), origin = "topleft")
            actor2.set_text("Hello!")
            actor2.auto_size = "actor"
            actor2.font_size = 32

            actor3 = Number((0,150), origin = "topleft")
            actor3.auto_size = None
            actor3.font_size=64

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

