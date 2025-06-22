from miniworlds import App, TiledWorld, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1901(unittest.TestCase):

    def setUp(self):
        def test_code():
            # Here comes your code
            class MyWorld(TiledWorld):
                def setup_environment(self, test):
                    self.init_test()            
                    path = os.path.dirname(__file__)
                    world.app.register_path(path)
                    self.columns = 5
                    self.rows = 5
                    self.tile_size = 40
                    self.add_background("images/stone.png")
                    print(self.background)
                    actor = Actor()
                    actor.position = (3,4)
                    assert(actor.costume.is_rotatable == True)
                    print(actor, actor.costumes)
                    print("costume:", actor.costume)
                    print(actor.costume.images)
                    actor.add_costume("images/player.png")
                    print(actor.costumes)
                    
                    print(actor.costume.images)
                    assert(actor.costume.is_upscaled == True)
                    # Bilder von:
                    # https://www.kenney.nl/assets
                        
            world = MyWorld()
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