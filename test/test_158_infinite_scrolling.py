from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test158(unittest.TestCase):

    def setUp(self):
        def test_code():
            # Infinite Scrolling with sliding background
            WIDTH, HEIGHT = 800, 400
            world = World(WIDTH, HEIGHT)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                nonlocal WIDTH, HEIGHT
                left, bottom = WIDTH/2, HEIGHT/2
                
                
                BACKGROUND = "desertback"
                # Background 0 at position (0,0)
                back0 = Actor((0,0), origin = "topleft")
                back0.add_costume(BACKGROUND)
                back0.size = WIDTH, HEIGHT
                # background 1 at position WIDTH
                back1 = Actor((WIDTH, 0), origin = "topleft")
                back1.size = WIDTH, HEIGHT
                back1.add_costume(BACKGROUND)
                backs = [back0, back1]

                # The actor, a walking robot
                walker = Actor((100, HEIGHT - 100), origin = "topleft")
                walker.size = 100, 60
                walker.add_costumes(["walk1", "walk2"])
                walker.speed = 1
                walker.count = 0

                @world.register
                def act_test(self):
                    for back in backs:
                        back.x -= 1
                        if back.x <= - WIDTH:
                            back.x = WIDTH
                    walker.count += walker.speed
                    if walker.count > 11:
                        costume = walker.next_costume()
                        walker.count = 0
                
                @world.register
                def on_key_down(self, keys):
                    if "q" in keys:
                        world.quit
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 20, 40, 60, 80]
        QUIT_FRAME = 100
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)



        return world

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()