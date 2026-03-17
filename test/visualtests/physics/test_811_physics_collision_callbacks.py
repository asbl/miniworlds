from miniworlds import App, Circle
from miniworlds_physics import PhysicsWorld

from .. import VISUALTESTS_ROOT_FILE
from ..screenshot_tester import ScreenshotTester
import unittest


class TestPhysicsCollisionCallbacks(unittest.TestCase):
    SCREENSHOT_TITLE = "Test811"
    def setUp(self):
        def test_code():
            world = PhysicsWorld(220, 140)

            @world.register
            def setup_environment(self, test):
                self.gravity = (0, 0)
                self.damping = 1
                self.add_background((245, 247, 250))

                left = Circle((55, 70), 14)
                left.color = (220, 90, 90)
                left.physics.shape_type = "circle"
                left.physics.velocity_x = 150

                right = Circle((165, 70), 14)
                right.color = (90, 120, 220)
                right.physics.shape_type = "circle"
                right.physics.velocity_x = -150

                self.left = left
                self.right = right
                self.separation_started = False

                @left.register
                def on_touching_circle(self, other, info):
                    self.color = (80, 180, 120)
                    other.color = (255, 210, 90)
                    if not self.world.separation_started:
                        self.physics.velocity_x = -150
                        other.physics.velocity_x = 150
                        self.world.separation_started = True

                @left.register
                def on_separation_from_circle(self, other, info):
                    self.color = (150, 90, 200)
                    other.color = (90, 90, 90)

            return world

        App.reset(unittest=True, file=str(VISUALTESTS_ROOT_FILE))
        world = test_code()
        tester = ScreenshotTester([1, 18, 36], 36, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()

        self.assertNotEqual(self.world.left.color, (220, 90, 90))
        self.assertNotEqual(self.world.right.color, (90, 120, 220))


if __name__ == "__main__":
    unittest.main()