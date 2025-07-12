from miniworlds import App, World, Actor, Toolbar, Button, Label, Label, loop
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test610(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                toolbar = Toolbar()
                toolbar.margin_top = 10
                world.layout.add_right(toolbar, size = 200)
                
                button1 = Button("Toolbar Button")
                button1.text = "First Button"
                button1.set_image("images/arrow.png")
                toolbar.add(button1)


            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = []
        QUIT_FRAME = 1
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
