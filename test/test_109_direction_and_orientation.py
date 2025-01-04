from miniworlds import Actor, World, App
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test109(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 400)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.add_background((0, 0, 0, 100))
                # Actor1 at position (2,1) with player costume
                actor1 = Actor(position=(20, 0), origin = "topleft")
                actor1.add_costume("images/player.png")
                actor1.costume.orientation = -90
                assert actor1.position == (20,0)
                assert actor1.direction == 0
                assert actor1.costume.orientation == - 90
                actor2 = Actor(position=(20, 40), origin = "topleft")
                actor2.add_costume("images/player.png")
                actor2.costume.orientation = 90
                actor3 = Actor(position=(20, 80), origin = "topleft")
                actor3.add_costume("images/player.png")
                actor3.costume.orientation = 180
                actor4 = Actor(position=(20, 120), origin = "topleft")
                actor4.add_costume("images/player.png")
                actor4.costume.orientation = 270
                # Unit circle
                actor6 = Actor(position=(120, 0), origin = "topleft")
                actor6.add_costume("images/player.png")
                actor6.costume.orientation = -90
                actor6.direction_at_unit_circle = 0
                actor7 = Actor(position=(120, 40), origin = "topleft")
                actor7.add_costume("images/player.png")
                actor7.costume.orientation = -90
                actor7.direction_at_unit_circle = 90
                actor8 = Actor(position=(120, 80), origin = "topleft")
                actor8.add_costume("images/player.png")
                actor8.costume.orientation = -90
                actor8.direction_at_unit_circle = 180
                actor9 = Actor(position=(120, 120), origin = "topleft")
                actor9.add_costume("images/player.png")
                actor9.costume.orientation = -90
                actor9.direction_at_unit_circle = 270
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

