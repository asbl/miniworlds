from miniworlds import App, World, Circle
from .screenshot_tester import ScreenshotTester
import unittest


class TestLeavingScreenCopy(unittest.TestCase):
    SCREENSHOT_TITLE = "Test230"

    def setUp(self):
        def test_code():
            # A circle leaves the screen
            world = World(100, 100)
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                t = Circle((50,50))
                @t.register
                def act(self):
                    self.x += 1
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 20, 40, 60]
        QUIT_FRAME = 70
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
