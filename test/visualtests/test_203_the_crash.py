from miniworlds import App, World, Actor, TiledWorld
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test203(unittest.TestCase):

    def setUp(self):
        def test_code():
            class MyWorld(TiledWorld):

                def setup_environment(self, test):
                    robot1 = Robot(position=(0, 0))
                    robot1.add_costume("images/robo_green.png")
                    robot1.costume.orientation = - 90
                    robot1.direction = "right"
                    robot2 = Robot(position=(4, 0))
                    robot2.add_costume("images/robo_yellow.png")
                    robot2.costume.orientation = - 90
                    robot2.direction = "left"
                    self.add_background("images/water.png")
                    self.init_test()

            class Explosion(Actor):
                def on_setup(self):
                    self.add_costume("images/explosion.png")


            class Robot(Actor):

                def act(self):
                    self.move()
                    other = self.detect(actors=Robot)
                    if other:
                        print("sensed", self, other, self.world.actors)
                        explosion = Explosion(position=self.position)
                        print("exploded")
                        self.remove()
                        print("self.removed")
                        other.remove()
                        print("other.removed")
                        


            world = MyWorld(5, 1)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,2,3,4,5]
        QUIT_FRAME = 5
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

