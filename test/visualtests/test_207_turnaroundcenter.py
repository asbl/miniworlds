from miniworlds import App, World, Actor, World
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test207(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200,200)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                import pygame
                world.add_background((0,0,0,255))
                # Both actors have the same position to begin with
                # Then the second actor is turned by 90 degrees.
                #
                # Output should be a cross, not an inverted L!
                tkn = Actor(origin = "topleft")
                tkn.position = (50,50)
                tkn.add_costume((255,255,255,100))
                tkn.size= (10, 100)
                assert(tkn.position == (50,50))
                assert(tkn.center == (55,100))
                assert(tkn.rect == pygame.Rect(50,50,10,100))

                tkn2 = Actor(origin = "center")
                tkn2.size= (10, 100)
                tkn2.topleft = (50,50)
                tkn2.add_costume((0,255,255,100))
                
                assert tkn2.topleft == (50.0,50.0)
                assert tkn2.center == (55,100)
                tkn2.turn_left(90)
                #print("tkn2, position, center, ", tkn2.position, tkn2.center, tkn2.rect)
                assert tkn2.topleft == (50, 50)
                assert tkn2.center ==  (55, 100)
                assert tkn2.size == (10, 100)
                # print("tkn2, position, center, ", tkn2.position, tkn2.center, tkn2.rect, tkn2.size, tkn2.rect)
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



        return world

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()