from miniworlds import App, World, Actor, World
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test301(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(280, 100)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.add_background("images/water.png")
                world.speed = 1
                print(world.speed, world.fps)
                robo = Actor(position=(0, 0), origin = "topleft")
                robo.costume.add_images(["images/1.png", "images/2.png","images/3.png","images/4.png"])
                print(robo.costume)
                robo.size = (100, 100)
                robo.costume.loop = True
                robo.costume.animate()
                robo.costume.orientation = - 90
                robo.costume.animation_speed = 20
                robo.direction = "right"
                @robo.register
                def act(self):
                    if self.detect_world():
                        self.move()
                @robo.register
                def on_not_detecting_world(self):
                    self.flip_x()
                    self.move()
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES =[1, 20, 40, 60, 80, 100, 120]
        QUIT_FRAME = 121
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