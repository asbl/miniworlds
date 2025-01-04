from miniworlds import App, World, Actor, Toolbar, YesNoButton, Button
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test612(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(400, 200)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                toolbar = Toolbar()
                world.add_right(toolbar, size = 300)
                
                toolbar.margin_left =  20
                toolbar.margin_right = 10
                toolbar.background_color = (0,0,255)
                button = YesNoButton("Yes", "No")
                yes = button.get_yes_button()
                yes.background_color = (0, 255, 0)
                no = button.get_no_button()
                no.background_color = (255, 0, 0)
                toolbar.add(button)
                button2 = Button("test")
                toolbar.add(button2)
                
                @world.register
                def on_message(self, message):
                    print(message)
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


if __name__ == "__main__":
    unittest.main()