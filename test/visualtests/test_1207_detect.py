from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1207(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(100, 100)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                
                wall=Actor((80,0), origin = "topleft")
                wall.color = (255,255,255)

                player = Actor((0,0))
                @player.register
                def act(self):
                    self.move(direction = "right")
                    if self.detect():
                        self.color = (0,255,0)
                    
                @player.register
                def on_detecting_actor(self, other):
                    other.color = (255,0,0)
            return world
                        
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 62]
        QUIT_FRAME = 63
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
