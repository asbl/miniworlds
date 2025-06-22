from miniworlds import App, TiledWorld, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1913(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld(10,4)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                def create_actor(x, y):
                    t = Actor()
                    t.position = (x, y)
                    t.add_costume("images/alien1.png")
                    t.border = 1
                    return t

                # 0 - 4
                t0 = create_actor(0,0)
                print(t0.size)
                print(t0.costume.is_upscaled)
                print(t0.costume.is_scaled)
                print(t0.costume.is_scaled_to_width)
                print(t0.costume.is_scaled_to_height)

                t0b = create_actor(1,0)

                t = create_actor(2,0)
                t.costume.is_scaled = True

                
                t = create_actor(3,0)
                t.costume.is_scaled_to_width = True
                
                # 5 - 8
                t = create_actor(4,0)
                t.costume.is_scaled_to_height = True

                t = create_actor(5,0)
                t.costume.is_textured = True

                t = create_actor(6,0)
                t.costume.is_textured = True
                t.costume.texture_size = (10,10)

                t = create_actor(7,0)
                t.flip_x()

                t = create_actor(8,0)
                t.is_rotatable = False
                t.flip_x()


                # ----------------- row 2

                t = create_actor(0,1)

                t = create_actor(1,1)
                t.orientation = -90

                t = create_actor(2,1)
                t.orientation = -180

                t = create_actor(3,1)
                t.orientation = -270
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1]
        QUIT_FRAME = 90
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
