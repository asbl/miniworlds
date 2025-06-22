from miniworlds import App, TiledWorld, Actor
from .screenshot_tester import ScreenshotTester
import unittest


class Test231(unittest.TestCase):
    def setUp(self):
        def test_code():
            # A circle leaves the screen
            world = TiledWorld(3, 3)
            print(world.camera.view)

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                t = Actor((0, 0))

                @t.register
                def act(self):
                    self.x += 1

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,2,3,4]
        QUIT_FRAME = 5
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
