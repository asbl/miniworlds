from miniworlds import App, HexWorld, Actor
from .screenshot_tester import ScreenshotTester
import unittest


class TestHexWorldGrid(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = HexWorld(7, 7, tile_size=40)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.background.grid = True
                actor = Actor((0, 0))
                actor.fill_color = (255, 0, 0)
                actor = Actor((3, 3))
                actor.fill_color = (0, 200, 0)
                actor = Actor((6, 6))
                actor.fill_color = (0, 0, 255)
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
