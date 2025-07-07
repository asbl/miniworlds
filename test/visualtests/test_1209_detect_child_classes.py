from miniworlds import App, TiledWorld, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1208(unittest.TestCase):

    def setUp(self):
        def test_code():

            world = TiledWorld(10, 10)
            # Here comes your code
            @world.register
            def setup_environment(self, test):

                class Wall(Actor):
                    pass


                wall=Wall((3,0), origin = "topleft")
                wall.color = (255,255,255)



                player = Actor((0,0))
                @player.register
                def act(self):
                    self.move(direction = "right")
                    if self.world.frame == 60 and self.detect():
                        self.color = (0,100,100)
                    
                @player.register
                def on_detecting_wall(self, other):
                    if self.world.frame == 60:
                        other.color = (100,0,50)
            return world
                        
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,3,4,5]
        QUIT_FRAME = 6
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
