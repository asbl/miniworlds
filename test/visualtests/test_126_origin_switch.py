from miniworlds import Actor, App, World

from .screenshot_tester import ScreenshotTester
import unittest


class Test126OriginSwitch(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World(220, 160)

            @world.register
            def setup_environment(self, test):
                self.add_background((238, 240, 244))

                marker = Actor((60, 50))
                marker.add_costume((220, 60, 60, 255))
                marker.size = (12, 12)
                marker.origin = "topleft"

                switcher = Actor((60, 50), origin="center")
                switcher.add_costume("images/player.png")
                switcher.size = (42, 42)
                switcher.direction = 90
                self.switcher = switcher

                corner_actor = Actor((140, 40), origin="topleft")
                corner_actor.add_costume("images/ship.png")
                corner_actor.size = (36, 36)
                self.corner_actor = corner_actor

            @world.register
            def act_test(self):
                if self.frame == 10:
                    self.switcher.position_manager.switch_origin("topleft")
                if self.frame == 20:
                    self.corner_actor.position_manager.switch_origin("center")

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        tester = ScreenshotTester([1, 10, 20], 20, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
