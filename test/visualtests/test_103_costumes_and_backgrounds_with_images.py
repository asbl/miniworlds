from miniworlds import TiledWorld, Actor, App
import unittest
from .screenshot_tester import ScreenshotTester

class Test103(unittest.TestCase):

    def setUp(self):
        def test_code():
            print("run test...")
            world = TiledWorld()
            # Black world
            @world.register
            def setup_environment(self, test):
                print("setup environment")
                world.add_background((200, 200, 200, 255))
                world.columns = 5
                world.rows = 5
                world.tile_size = 40
                print("background added")

                # Actor1 at position (2,1) with player costume
                actor1 = Actor(position=(2, 1))
                actor1.add_costume("images/player.png")
                assert(actor1.position == (2, 1))
                # Actor2 at position (3,1) with purple background
                actor2 = Actor(position=(3, 1))
                actor2.add_costume((100, 0, 100, 100))
                try:
                    actor2.size = (1, 1)
                except Exception as e:
                    print(e)

                actor3 = Actor(position=(3, 2))
                actor3.add_costume("images/player.png")
                
                Actor(position=(4, 1))

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
