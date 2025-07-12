from miniworlds import App, World, Actor, World
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test614(unittest.TestCase):

    def setUp(self):
        def test_code():
            class World1(World):
                def setup_environment(self, test):
                    self.rows = 100
                    self.columns = 100
                    self.add_background((0,0,100,255))
                    print("world 1 was created")
                    self.actor = Actor((10,10), origin = "topleft")
                    self.actor.color = (255, 0, 0)
                    self.actor.direction = "right"
                    
                def act_test(self):
                    print("act", self.frame)
                    if self.frame < 30:
                        self.actor.move()
                    elif self.frame == 30:
                        print("switch to world 2", self.frame)
                        world2 = World2(400, 600)
                        self.attach_world(world2)
                        self.layout.switch_world(world2)
                        
                
            class World2(World):
                def on_setup(self):
                    self.add_background((255,255,255,255))
                    self.actor = Actor((80,80), origin = "topleft")
                    print("self", self)
                    print("created actor", self.actor, "on world ", self.actor.world)
                    self.actor.color = (0,255,0)
                    self.actor.costume.set_dirty("all", 2)
                    self.actor.dirty = 1
                    print("actor created at", self.actor.get_local_rect())
                    print("world 2 was created")
                    
                def act(self):
                    self.test()
                    if self.frame > 80:
                        self.actor.move()
                        print("actor rect", self.actor.get_local_rect())
                    

            world = World1(400,600)
            return world
                
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,41, 81, 101]
        QUIT_FRAME = 101
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

