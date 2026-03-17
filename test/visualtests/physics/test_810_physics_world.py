from miniworlds import App, Circle, Rectangle
from miniworlds_physics import PhysicsWorld

from .. import VISUALTESTS_ROOT_FILE
from ..screenshot_tester import ScreenshotTester
import unittest


class TestPhysicsWorldGroundCollision(unittest.TestCase):
    SCREENSHOT_TITLE = "Test810"
    def setUp(self):
        def test_code():
            world = PhysicsWorld(160, 120)

            @world.register
            def setup_environment(self, test):
                self.gravity = (0, 300)
                self.damping = 1
                self.add_background((242, 246, 255))

                floor = Rectangle((0, 100), 160, 20)
                floor.color = (70, 70, 90)
                floor.physics.simulation = "static"

                ball = Circle((80, 18), 12)
                ball.color = (210, 80, 80)
                ball.physics.elasticity = 0
                ball.physics.shape_type = "circle"

                self.floor = floor
                self.ball = ball

            return world

        App.reset(unittest=True, file=str(VISUALTESTS_ROOT_FILE))
        world = test_code()
        TEST_FRAMES = [1, 30, 60]
        QUIT_FRAME = 60
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

        return world

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()

        ball_bottom = self.world.ball.position_manager.get_global_rect().bottom
        floor_top = self.world.floor.position_manager.get_global_rect().top

        self.assertGreater(self.world.ball.y, 18)
        self.assertLessEqual(ball_bottom, floor_top + 2)


if __name__ == "__main__":
    unittest.main()