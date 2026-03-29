from miniworlds import App, Costume, Actor, World
from .screenshot_tester import ScreenshotTester
import unittest


class TestCostumeAttachmentVisual(unittest.TestCase):
    SCREENSHOT_TITLE = "Test820"

    def setUp(self):
        def test_code():
            world = World(140, 70)
            world.background.fill((235, 240, 245))

            @world.register
            def setup_environment(self, test):
                actor_direct = Actor((15, 15), origin="topleft", world=world)
                actor_direct.size = (40, 40)
                direct_costume = Costume(actor_direct)
                direct_costume.add_image("images/walk1.png")
                direct_costume.add_image("images/walk2.png")

                actor_detached = Actor((80, 15), origin="topleft", world=world)
                actor_detached.size = (40, 40)
                detached_costume = Costume()
                detached_costume.add_image("images/player.png")
                actor_detached.add_costume(detached_costume)

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        tester = ScreenshotTester([1], 1, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()