from miniworlds import Actor, App, HexWorld
from .screenshot_tester import ScreenshotTester
import unittest


class Test237HexCameraScroll(unittest.TestCase):
    SCREENSHOT_TITLE = "Test237HexCameraScroll"

    def setUp(self):
        def test_code():
            world = HexWorld(16, 12, tile_size=40)
            # Camera view smaller than the world: the camera follows a
            # moving actor, so static markers and the grid must scroll
            # with the visible window.
            world.camera.width = 8
            world.camera.height = 6

            @world.register
            def setup_environment(self, test):
                world.background.grid = True
                # Static markers all over the world: they must stay visible
                # while the camera scrolls over them.
                for x in range(0, 16, 3):
                    for y in range(0, 12, 3):
                        marker = Actor((x, y))
                        marker.add_costume((40 + x * 12, 90, 160, 255))
                        marker.static = True
                player = Actor((3, 3))
                player.add_costume((230, 40, 50, 255))

                @player.register
                def act(self):
                    self.move_in_direction("o")
                    self.world.camera.from_actor(self)

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        TEST_FRAMES = [1, 2, 3, 4, 5]
        QUIT_FRAME = 5
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
