from miniworlds import App, World, Actor, World
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test312(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World(200, 100)

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.add_background("images/water.png")
                world.speed = 1
                robo = Actor(position=(10, 0), origin="topleft")
                c1 = robo.add_costume(["images/1.png", "images/2.png"])
                c2 = robo.add_costume(["images/3.png", "images/4.png"])
                c1.animate()
                robo.switch_costume(c1)
                robo.size = (99, 99)
                c1.loop = True
                robo.costumes.orientation = -90
                robo.costumes.animation_speed = 20
                robo.direction = "right"
                print(robo.costumes)
                for costume in robo.costumes:
                    print(costume)

                @robo.register
                def act(self):
                    if self.world.frame % 100 == 0:
                        self.switch_costume(c2)
                        c2.set_image(0)
                        c2.animate()

                    if self.world.frame % 200 == 0:
                        self.switch_costume(c1)
                        c1.set_image(0)
                        c1.animate()

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 20, 40, 60, 80, 120, 140, 180, 200]
        QUIT_FRAME = 200
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
