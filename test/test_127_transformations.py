from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test127(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(800, 400)

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                def create_actor(x, y):
                    t = Actor()
                    t.position = (x, y)
                    t.add_costume("images/alien1.png")
                    t.border = 1
                    return t

                def create_player(x, y):
                    t = Actor()
                    t.position = (x, y)
                    t.add_costume("images/player.png")
                    t.border = 1
                    return t

                t0 = create_actor(60, 80)

                t0b = create_actor(120, 80)
                t0b.size = (60, 60)

                t = create_actor(180, 80)
                t.size = (60, 60)
                t.costume.is_scaled = True

                t = create_actor(260, 80)
                t.size = (60, 60)
                t.costume.is_scaled_to_width = True

                t = create_actor(340, 80)
                t.size = (60, 60)
                t.costume.is_scaled_to_height = True

                t = create_actor(420, 80)
                t.size = (60, 60)
                t.costume.is_textured = True

                t = create_actor(500, 80)
                t.size = (60, 60)
                t.costume.is_textured = True
                t.costume.texture_size = (10, 10)

                t = create_actor(580, 80)
                t.size = (60, 60)
                t.flip_x()

                t = create_actor(660, 80)
                t.is_rotatable = False
                t.size = (60, 60)
                t.flip_x()

                # ----------------- row 2

                t = create_actor(60, 170)
                t.size = (60, 60)

                t = create_actor(140, 170)
                t.orientation = -90
                t.size = (60, 60)

                t = create_actor(220, 170)
                t.orientation = -180
                t.size = (60, 60)

                t = create_actor(300, 170)
                t.orientation = -270
                t.size = (60, 60)

                t = create_actor(360, 170)
                t.orientation = -270
                t.size = (60, 60)

                t = create_actor(420, 170)
                t.direction = 90
                t.size = (60, 60)

                t = create_actor(480, 170)
                t.orientation = 180
                t.size = (60, 60)

                t = create_actor(540, 170)
                t.orientation = 270
                t.size = (60, 60)

                t = create_actor(600, 170)
                t.orientation = 45
                t.size = (60, 60)

                # -- row 3

                t = create_player(60, 260)
                t.size = (60, 60)

                t = create_player(140, 260)
                t.costume.is_upscaled = True
                t.size = (60, 60)

                t = create_player(220, 260)
                t.costume.is_scaled = True
                t.size = (60, 60)

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
