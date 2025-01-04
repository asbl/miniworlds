from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test212(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                # Is player 1 sensing player 2? Should return True
                import pygame
                world.columns=300
                world.rows=200
                world.add_background("images/soccer_green.jpg")
                world.add_background("images/space.jpg")
                world.speed = 30

                player1 = Actor(position=(30, 4), origin = "topleft")
                player1.size = (40, 40)
                player1.add_costume("images/char_blue.png")
                player1.costume.orientation = - 90

                player2 = Actor(position=(3, 4), origin = "topleft")
                player2.size = (40, 40)
                player2.add_costume("images/char_blue.png")
                player2.costume.orientation = - 90

                player3 = Actor(position=(90, 4), origin = "topleft")
                player3.size = (40, 40)
                player3.add_costume("images/char_blue.png")
                player3.costume.orientation = - 90

                @player1.register
                def act(self):
                        assert(player1.rect == pygame.Rect(30, 4, 40, 40))

                @player2.register
                def act(self):
                    assert(player2.rect == pygame.Rect(3, 4, 40, 40))

                @player1.register
                def on_detecting_actor(self, actor):
                    assert(actor==player2)
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



        return world

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()