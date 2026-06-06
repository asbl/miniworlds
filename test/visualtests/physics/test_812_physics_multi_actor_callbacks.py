from miniworlds import App, Circle
from miniworlds_physics import PhysicsWorld

from .. import VISUALTESTS_ROOT_FILE
from ..screenshot_tester import ScreenshotTester
import unittest


class TestPhysicsMultiActorCallbacks(unittest.TestCase):
    SCREENSHOT_TITLE = "Test812"

    def setUp(self):
        def test_code():
            world = PhysicsWorld(260, 140)

            @world.register
            def setup_environment(self, test):
                self.gravity = (0, 0)
                self.damping = 1
                self.add_background((245, 247, 250))

                left = Circle((45, 70), 14)
                left.color = (220, 90, 90)
                left.physics.shape_type = "circle"
                left.physics.velocity_x = 180

                middle = Circle((130, 70), 14)
                middle.color = (90, 120, 220)
                middle.physics.shape_type = "circle"

                uninvolved = Circle((220, 70), 14)
                uninvolved.color = (80, 80, 95)
                uninvolved.physics.shape_type = "circle"

                self.left = left
                self.middle = middle
                self.uninvolved = uninvolved
                self.left_callback_count = 0
                self.uninvolved_callback_count = 0

                @left.register
                def on_touching_circle(self, other, info):
                    self.color = (80, 180, 120)
                    other.color = (255, 210, 90)
                    self.world.left_callback_count += 1

                @uninvolved.register
                def on_touching_circle(self, other, info):
                    self.color = (150, 90, 200)
                    self.world.uninvolved_callback_count += 1

            return world

        App.reset(unittest=True, file=str(VISUALTESTS_ROOT_FILE))
        world = test_code()
        tester = ScreenshotTester([1, 36], 36, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()

        self.assertGreater(self.world.left_callback_count, 0)
        self.assertEqual(self.world.uninvolved_callback_count, 0)
        self.assertEqual(self.world.left.color, (80, 180, 120))
        self.assertEqual(self.world.middle.color, (255, 210, 90))
        self.assertEqual(self.world.uninvolved.color, (80, 80, 95))


if __name__ == "__main__":
    unittest.main()
