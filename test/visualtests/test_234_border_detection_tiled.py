from miniworlds import Actor, App, TiledWorld
from .screenshot_tester import ScreenshotTester
import unittest


class Test234BorderDetectionTiled(unittest.TestCase):
    SCREENSHOT_TITLE = "Test234"

    def setUp(self):
        def test_code():
            world = TiledWorld(4, 4)

            @world.register
            def setup_environment(self, test):
                cases = [
                    ((0, 1), (220, 60, 60), ["left"]),
                    ((3, 1), (60, 160, 220), ["right"]),
                    ((1, 0), (80, 200, 120), ["top"]),
                    ((1, 3), (230, 190, 60), ["bottom"]),
                    ((0, 0), (160, 90, 220), ["left", "top"]),
                ]
                for position, color, expected in cases:
                    actor = Actor(position, world=world)
                    actor.add_costume(color)
                    test.assertEqual(actor.detect_borders(), expected)

                lookahead = Actor((2, 2), world=world)
                lookahead.add_costume((255, 255, 255))
                lookahead.direction = 90
                test.assertEqual(lookahead.detect_borders(distance=1), ["right"])

                backwards = Actor((1, 2), world=world)
                backwards.add_costume((30, 30, 30))
                backwards.direction = 90
                test.assertEqual(backwards.detect_borders(distance=-1), ["left"])

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
