from miniworlds import App, World, Actor, World, Console
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test615(unittest.TestCase):

    def setUp(self):
        def test_code():
            # Here comes your code
            class World1(World):
                def setup_environment(self, test):
                    self.add_background((0,255,0,255))
                    print("world 1 was created")
                    actor = Actor((10,10), origin ="topleft")
                    self.console = Console()
                    self.layout.add_bottom(self.console, size = 200)
                    
                def act_test(self):
                    if self.frame == 20:
                        print("world 1 is running", self.frame)
                        world2 = World2(400, 600)
                        self.attach_world(world2)
                        self.layout.switch_world(world2)
                        
                
            class World2(World):
                def on_setup(self):
                    self.add_background((0,0,100,255))
                    actor = Actor((40,40), origin = "topleft")
                    print("world 2 was created")  
                    
                def act(self):
                    self.test()
                    
                
            world = World1(400,600)
            return world
        
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,41]
        QUIT_FRAME = 41
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