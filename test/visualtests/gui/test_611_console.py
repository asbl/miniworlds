from miniworlds import App, World, Console, loop

from .. import VISUALTESTS_ROOT_FILE
from ..screenshot_tester import ScreenshotTester
import unittest


class TestConsoleMessageLog(unittest.TestCase):
    SCREENSHOT_TITLE = "Test611"

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                console = Console()
                console.newline("test")

                @loop(frames = 50)
                def newline():
                    console.newline(f"newline at frame {world.frame}")

                world.camera.add_bottom(console)

                @world.register
                def on_message(self, message):
                    print(message)
            return world
        App.reset(unittest=True, file=str(VISUALTESTS_ROOT_FILE))
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,50,100,150,200]
        QUIT_FRAME = 200
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
