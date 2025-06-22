from miniworlds import App, World, Actor, TiledWorld
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test201(unittest.TestCase):

    def setUp(self):
        def test_code():
            world=TiledWorld()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                
                world.columns = 4
                world.rows = 1
                world.speed = 20
                fish = Actor()
                fish.border = 1
                fish.add_costume("images/fish.png")
                fish.direction = "right"
                fish.orientation = -90
                
                @fish.register
                def act(self):
                    self.move()

                @fish.register
                def on_not_detecting_world(self):
                    self.undo_move()
                    self.flip_x()
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,2,3,4,5,6,7,8, 10, 11]
        QUIT_FRAME = 12
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()