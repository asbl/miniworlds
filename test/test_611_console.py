from miniworlds import App, World, Actor, Console, loop
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test611(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            #@TODO: Fix test
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                console = Console()
                console.newline("test")

                @loop(frames = 50)
                def newline():
                    console.newline(f"newline at frame {world.frame}")

                world.add_bottom(console)

                @world.register
                def on_message(self, message):
                    print(message)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,50,100,150,200]
        QUIT_FRAME = 200
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