import unittest

from miniworlds import Actor, App, World

from .screenshot_tester import ScreenshotTester


class TestRenderingPipelineCache(unittest.TestCase):
    SCREENSHOT_TITLE = "TestRenderingPipelineCache"

    def setUp(self):
        App.reset(unittest=True, file=__file__)
        world = World(240, 140)

        @world.register
        def setup_environment(self, test):
            actor = Actor((70, 70))
            actor.add_costume("images/player.png")
            actor.add_costume("images/alien1.png")
            actor.size = (40, 60)
            test.actor = actor

        @world.register
        def act_test(self):
            if self.test_frame == 1:
                self.tester.unittest.actor.size = (100, 50)
                self.tester.unittest.actor.flip_x()
            elif self.test_frame == 2:
                self.tester.unittest.actor.switch_costume(1)
                self.tester.unittest.actor.size = (55, 90)
                self.tester.unittest.actor.orientation = 90

        tester = ScreenshotTester([1, 2, 3], 3, self)
        tester.setup(world)
        world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
