from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import pygame

class Test110(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code

            # Black world
            @world.register
            def setup_environment(self, test):
                world.add_background((0, 0, 0, 100))
                world.size = (400, 300)
                # actors looking:
                # * up(dir 0, or:-90)
                # * down(dir 0, or:90)
                # * left(dir 0, or:180)
                # * right(dir 0, or:270)

                # Actor1 at position (2,1) with player costume
                actor1 = Actor(position=(20, 50), origin = "topleft")
                actor1.add_costume("images/player.png")
                actor1.costume.orientation = -90
                assert actor1.position == (20, 50)
                assert actor1.direction == 0
                assert actor1.orientation == -90

                actor2 = Actor(position=(20, 100), origin = "topleft")
                actor2.add_costume("images/player.png")
                actor2.costume.orientation = 90
                actor3 = Actor(position=(20, 150), origin = "topleft")
                actor3.add_costume("images/player.png")
                actor3.costume.orientation = 180
                actor4 = Actor(position=(20, 200), origin = "topleft")
                actor4.add_costume("images/player.png")
                actor4.costume.orientation = 270

                assert actor4.position == (20, 200)
                #assert actor4.rect == pygame.Rect(0, 200, 40, 40)

                class UpActor(Actor):
                    def on_setup(self):
                        self.direction = 0
                        self.costume.orientation = -90

                class LeftActor(Actor):
                    def on_setup(self):
                        self.direction = -90
                        self.costume.orientation = -90

                class DownActor(Actor):
                    def on_setup(self):
                        self.direction = 180
                        self.costume.orientation = -90

                class RightActor(Actor):
                    def on_setup(self):
                        self.costume.orientation = -90
                        self.direction = 90
                r = RightActor(position=(80, 50), origin = "topleft")
                r.add_costume("images/player.png")
                l = LeftActor(position=(80, 100), origin = "topleft")
                l.add_costume("images/player.png")
                u = UpActor(position=(80, 150), origin = "topleft")
                u.add_costume("images/player.png")
                d = DownActor(position=(80, 200), origin = "topleft")
                d.add_costume("images/player.png")
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

