from miniworlds import App, World, Actor, Circle, Ellipse
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test132(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200,80)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.default_fill_color = (0,0, 255)

                t = Actor(origin = "topleft")

                t2 = Actor((40,0), origin = "topleft")
                t2.is_filled = (0, 255, 0)

                t3 = Actor((80, 0), origin = "topleft")
                t3.fill_color = (255, 0, 0)

                t4 = Actor((120, 0), origin = "topleft")
                t4.add_costume((0,0,0))
                t4.fill_color = (255, 255, 0)

                t5 = Actor((160, 0), origin = "topleft")
                t5.add_costume("images/player.png")
                t5.fill_color = (255, 255, 0, 100) # image is overwritten
                assert (t5.is_filled == (255, 255, 0, 100))

                t6 = Circle((0, 40), 20, origin = "topleft")
                t6.fill_color = (255, 255, 255)
                t6.border = 1
                print(t6.position, t6.center, t6.origin)
                assert(t6.origin == "topleft")
                assert(t6.position == (0, 40))
                t7 = Ellipse((40, 40), 40, 40, origin = "topleft")
                t7.fill_color = (255, 0, 255) 

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