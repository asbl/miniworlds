from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1205(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                
                wall=Actor((200,0), origin = "topleft")
                wall.color = (255,255,255)
                wall.size = (20, 400)

                for i in range(7):
                    actor = Actor((10,i*60))
                    actor.color = (255,255,255)
                    actor.range = i * 10
                    actor.number = i % 4
                    actor.origin = "topleft"
                    @actor.register
                    def act(self):
                        if self.number == 0:
                            if not self.detect(wall):
                                self.direction = "right"
                                self.move()
                        if self.number == 1:
                            if not self.detect():
                                self.direction = "right"
                                self.move()
                        if self.number == 2:
                            if not self.detect():
                                self.direction = "right"
                                self.move()
                        if self.number == 3:
                            if not self.detect(wall):
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



        return world

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
