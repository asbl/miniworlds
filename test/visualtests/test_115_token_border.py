from miniworlds import App, TiledWorld, Actor
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test115(unittest.TestCase):

    def setUp(self):
        def test_code():
            class MyWorld(TiledWorld):
                def setup_environment(self, test):
                    self.columns = 5
                    self.rows = 5
                    self.tile_size = 40
                    self.add_background("images/soccer_green.jpg")
                    self.draw.default_border_color = (255,100,100,255)
                    self.draw.default_border = 5
                    
                    actor = Actor()
                    actor.position = (0, 0)
                    actor.add_costume((100, 100, 100))
                    
                    actor2 = Actor()
                    actor2.fill = True
                    actor2.fill_color = (0,100,0)
                    actor2.border = 10
                    actor2.costume.stroke_color = (0,200,0)
                    actor2.position = (1, 0)
                    
                    actor = Actor()
                    actor.costume.add_image((0,200,200))
                    actor.position = (2, 0)
                    self.init_test()
                
            world = MyWorld(8, 6)
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


