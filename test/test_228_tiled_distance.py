from miniworlds import App, World, Actor, TiledWorld, Tile
from screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test228(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = TiledWorld(8, 8)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                tile1 = world.get_tile((0,0))
                tile2 = world.get_tile((6,6))
                t = Actor((5,6))
                tile3 = Tile.from_actor(t)
                tile4 = world.get_tile((7,7))
                t2 = Actor((7,7))
                
                print(tile1)
                print(tile2)
                print(tile1.distance_to(tile2))
                print(tile3.distance_to(tile2))
                print(tile1.distance_to(tile4))
                assert 8 < tile1.distance_to(tile2) < 8.5
                assert 0.9 < tile3.distance_to(tile2) < 1.1
                assert 9.5 < tile1.distance_to(tile4) < 10
                assert tile3.distance_to(tile4) == t.get_distance_to((7,7))
                print(t.get_distance_to(t2), tile3.distance_to(tile4))
                assert abs(t.get_distance_to(t2) - tile3.distance_to(tile4)) < 0.1

                @world.register
                def on_setup(self):
                    self.init_test()            
                    
                @world.register
                def act(self):
                    self.test()
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
