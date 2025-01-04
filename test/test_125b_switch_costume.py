from miniworlds import App, World, Actor, CostumeOutOfBoundsError, timer
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test125b(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(120,60)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                t1 = Actor()
                costume =t1.add_costume("images/1.png")
                t1.add_costume("images/2.png")
                t1.switch_costume(1)
                t1.origin = "topleft"

                t2 = Actor((40,0))
                t2.add_costume((100,0,0))
                t2.add_costume((0,100,0))
                t2.origin = "topleft"

                @timer(frames = 20)
                def switch():
                    print("switch t1")
                    t1.switch_costume(0)

                @timer(frames = 40)
                def switch():
                    print("switch t2")
                    t2.switch_costume(0)
                    print("switch t3")
                    t3.switch_costume(0)

                    
                @timer(frames = 60)
                def switch():
                    print("switch t2")
                    t2.switch_costume(1)
                    print("switch t3")
                    t3.switch_costume(1)
                    

                t3 = Actor((80,0))
                t3.add_costume("images/1.png")
                t3.add_costume("images/2.png")
                t3.origin = "topleft"
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 21, 41, 61]
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

