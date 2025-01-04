from miniworlds import App, World, Actor, ActionTimer
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test303(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World(280, 100)

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.add_background("images/water.png")
                world.speed = 1
                # Should show: A1, B1, C1, C2, C3, A1
                robo = Actor(position=(0, 0), origin="topleft")

                costume_a = robo.add_costume(
                    ["images/a1.png", "images/a2.png", "images/a3.png"]
                )
                costume_b = robo.add_costume(
                    ["images/b1.png", "images/b2.png", "images/b3.png"]
                )
                costume_c = robo.add_costume(
                    ["images/c1.png", "images/c2.png", "images/c3.png"]
                )

                @costume_c.register
                def after_animation(self):
                    self.actor.switch_costume(costume_a)
                    print("after animation")

                robo.size = (99, 99)

                costume_a.animation_speed = 80
                costume_b.animation_speed = 80
                costume_c.animation_speed = 80

                ActionTimer(30, robo.animate_costume, costume_b)
                ActionTimer(90, robo.animate_costume, costume_c)
                robo.costume.animate()

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [
            1,
            2,
            3,
            4,
            6,
            8,
            10,
            12,
            14,
            16,
            18,
            20,
            22,
            30,
            40,
            60,
            80,
            100,
            120,
            140,
            160,
        ]
        QUIT_FRAME = 161
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
