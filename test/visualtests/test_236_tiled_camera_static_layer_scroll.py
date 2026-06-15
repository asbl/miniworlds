from miniworlds import Actor, App, TiledWorld
from .screenshot_tester import ScreenshotTester
import unittest


class Test236TiledCameraStaticLayerScroll(unittest.TestCase):
    SCREENSHOT_TITLE = "Test236TiledCameraStaticLayerScroll"

    def setUp(self):
        def test_code():
            world = TiledWorld(4, 3)
            world.camera.world_size_x = 8
            world.camera.world_size_y = 3
            world.add_background((35, 55, 75, 255))

            @world.register
            def setup_environment(self, test):
                for x in range(8):
                    marker = Actor((x, 0))
                    marker.add_costume((70 + x * 20, 120, 150, 255))

                player = Actor((1, 1))
                player.add_costume((230, 40, 50, 255))

                @player.register
                def act(self):
                    self.x += 1
                    self.world.camera.from_actor(self)

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        tester = ScreenshotTester([1, 2, 3, 4], 4, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
