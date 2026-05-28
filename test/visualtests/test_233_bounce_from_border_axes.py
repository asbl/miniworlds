from miniworlds import Actor, App, World
from .screenshot_tester import ScreenshotTester
import unittest


class Test233BounceFromBorderAxes(unittest.TestCase):
    SCREENSHOT_TITLE = "Test233"

    def setUp(self):
        def test_code():
            world = World(120, 120)

            @world.register
            def setup_environment(self, test):
                cases = [
                    ((50, 0), 45, (220, 70, 70), 135),
                    ((50, 100), 135, (70, 150, 220), 45),
                    ((0, 50), -45, (80, 190, 120), 45),
                    ((100, 50), 45, (230, 190, 70), -45),
                ]
                for position, direction, color, expected_direction in cases:
                    actor = Actor(position, origin="topleft")
                    actor.size = (20, 20)
                    actor.add_costume(color)
                    actor.direction = direction

                    borders = actor.detect_borders()
                    test.assertTrue(borders)
                    actor.bounce_from_border(borders)
                    test.assertEqual(actor.direction, expected_direction)

                    actor.move(12)

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        tester = ScreenshotTester([1], 1, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)
        return world

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
