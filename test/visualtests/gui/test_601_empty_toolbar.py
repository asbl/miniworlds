from miniworlds import App, World, Toolbar

from .. import VISUALTESTS_ROOT_FILE
from ..screenshot_tester import ScreenshotTester
import unittest


class TestEmptyToolbarDocking(unittest.TestCase):
    SCREENSHOT_TITLE = "Test601"

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                toolbar = Toolbar()
                world.camera.add_right(toolbar, size = 200)
                assert(world.width == 400)
                assert(world.height == 400)
                assert(toolbar.width == 200)
                assert(toolbar.height == 400)
            return world
        App.reset(unittest=True, file=str(VISUALTESTS_ROOT_FILE))
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
