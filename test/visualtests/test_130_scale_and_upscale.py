from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test130(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World(800, 400)

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                def create_player(position, origin):
                    t = Actor()
                    t.position = position
                    t.add_costume("images/player.png")
                    t.border = 1
                    t.origin = origin
                    return t

                t = create_player((0, 180), origin="topleft")
                t.size = (80, 80)

                t = create_player((80, 180), origin="topleft")
                t.costume.is_upscaled = True
                t.size = (80, 80)

                t = create_player((160, 180), origin="topleft")
                t.costume.is_scaled = True
                t.size = (80, 80)

                t = create_player((40, 340), origin="center")
                t.size = (80, 80)

                t = create_player((120, 340), origin="center")
                t.costume.is_upscaled = True
                t.size = (80, 80)

                t = create_player((200, 340), origin="center")
                t.costume.is_scaled = True
                t.size = (80, 80)

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
