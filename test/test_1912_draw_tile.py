from miniworlds import App, TiledWorld
from screenshot_tester import ScreenshotTester
import unittest


class Test1912(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = TiledWorld()

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.tile_size = 40
                world.background.grid = True
                world.draw_on_image("images/wall.png", (5, 5))

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
