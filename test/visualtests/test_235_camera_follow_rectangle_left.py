from miniworlds import App, Rectangle, World
from .screenshot_tester import ScreenshotTester
import unittest


class Test235(unittest.TestCase):
    SCREENSHOT_TITLE = "Test235CameraFollowRectangleLeft"

    def setUp(self):
        def test_code():
            world = World(100, 80)

            @world.register
            def setup_environment(self, test):
                world.camera.world_size = (1000, 80)
                world.draw.default_fill_color = (255, 255, 255, 255)
                world.draw.fill_color = (0, 0, 0, 255)

                player = Rectangle.from_center((500, 40), 40, 20)
                player.fill_color = (220, 20, 60, 255)
                player.speed = 70
                world.camera.from_actor(player)

                expected_centers = {
                    1: (500, 40),
                    2: (430, 40),
                    3: (360, 40),
                    4: (290, 40),
                    5: (220, 40),
                    6: (150, 40),
                    7: (80, 40),
                    8: (10, 40),
                }

                @world.register
                def act_test(self):
                    frame = self.tester.test_frame
                    if frame in expected_centers:
                        test.assertEqual(player.center, expected_centers[frame])
                        if player.center_x >= 50:
                            test.assertEqual(world.camera.get_local_position(player.center), (50, 40))
                        else:
                            test.assertEqual(world.camera.topleft, (0, 0))
                            test.assertEqual(
                                world.camera.get_local_position(player.center),
                                player.center,
                            )

                    player.center_x -= player.speed
                    world.camera.from_actor(player)

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        tester = ScreenshotTester([1, 4, 7, 8], 8, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)
        return world

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
