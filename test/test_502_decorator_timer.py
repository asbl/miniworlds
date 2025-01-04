from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test502(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.columns=20
                world.rows=8
                world.tile_size=40
                world.add_background("images/soccer_green.jpg")
                world.add_background("images/space.jpg")
                world.speed = 30

                player = Actor(position=(3, 4))
                player.add_costume("images/char_blue.png")
                player.costume.orientation = - 90

                @timer(frames = 24)
                def moving():
                    player.move()

                @loop(frames = 48)
                def moving():
                    player.turn_left()
                    player.move(2)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,2,3,4,5,]
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


from miniworlds import *
import imgcompare
import os
import unittest
import random


    
def diff(ia, ib):
    percentage = imgcompare.image_diff_percent(ia, ib)
    return percentage
