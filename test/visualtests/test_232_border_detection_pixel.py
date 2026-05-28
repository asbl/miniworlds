from miniworlds import Actor, App, World
from .screenshot_tester import ScreenshotTester
import unittest


class Test232BorderDetectionPixel(unittest.TestCase):
    SCREENSHOT_TITLE = "Test232"

    def setUp(self):
        def test_code():
            world = World(120, 120)

            @world.register
            def setup_environment(self, test):
                cases = [
                    ((0, 40), (220, 60, 60), ["left"]),
                    ((100, 40), (60, 160, 220), ["right"]),
                    ((40, 0), (80, 200, 120), ["top"]),
                    ((40, 100), (230, 190, 60), ["bottom"]),
                    ((0, 0), (160, 90, 220), ["left", "top"]),
                ]
                for position, color, expected in cases:
                    actor = Actor(position, origin="topleft")
                    actor.size = (20, 20)
                    actor.add_costume(color)
                    test.assertEqual(actor.detect_borders(), expected)

                lookahead = Actor((79.5, 70), origin="topleft")
                lookahead.size = (40, 20)
                lookahead.add_costume((255, 255, 255))
                lookahead.direction = 90
                test.assertEqual(lookahead.detect_borders(distance=0.5), ["right"])

                backwards = Actor((5, 95), origin="topleft")
                backwards.size = (20, 20)
                backwards.add_costume((30, 30, 30))
                backwards.direction = 90
                test.assertEqual(backwards.detect_borders(distance=-5), ["left"])

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
