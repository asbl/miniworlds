from miniworlds import App, World
from .screenshot_tester import ScreenshotTester
import unittest


class Test000(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(1, 1)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                pass
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
