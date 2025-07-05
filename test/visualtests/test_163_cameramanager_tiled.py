from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from miniworlds import TiledWorld, Toolbar, Console, Actor, Button, Label, PagerHorizontal
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test163(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld()
            world.columns = 8
            world.rows = 8
            world.tile_size = 24
            world.camera.world_size_x = 16
            world.camera.world_size_y = 16
            world.add_background((255, 255, 255, 255))
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                def create_wall(pos):
                    w = Actor(pos)
                    w.add_costume("images/wall.png")
                create_wall((3,3))


                player = Actor((1, 1))


                @player.register
                def on_setup(self):
                    self.add_costume("images/knight")
                    self.costume.is_rotatable = False
                    self.layer = 3
                    self.is_blockable = True


                @player.register
                def act(self):
                    self.move(direction = "right")
                    self.move(direction = "down")
                    self.world.camera.from_actor(self)

            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,2,3,4]
        QUIT_FRAME = 5
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()