from miniworlds import App, World, Actor, timer
from .screenshot_tester import ScreenshotTester
import unittest


class Test308(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World()

            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.add_background("images/1.png")
                world.background.add_image("images/2.png")

                bg3 = world.add_background("images/3.png")
                bg4 = world.add_background("images/4.png")
                bg4.add_image("images/5.png")

                actor = Actor(origin="topleft")
                actor.add_costume("images/1.png")
                actor.costume.add_image("images/2.png")

                c3 = actor.add_costume("images/3.png")
                c4 = actor.add_costume("images/4.png")
                c4.add_image("images/5.png")

                @timer(frames=20)
                def do():
                    world.switch_background(1)
                    actor.switch_costume(1)

                @timer(frames=40)
                def do():
                    world.switch_background(0)
                    actor.switch_costume(0)

                @timer(frames=60)
                def do():
                    world.background.set_image(1)
                    actor.costume.set_image(1)

                @timer(frames=80)
                def do():
                    world.background.from_appearance(bg4, 0)
                    actor.costume.from_appearance(c4, 0)
                    world.background.set_image(1)
                    actor.costume.set_image(1)

            return world

        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1, 5, 10, 15, 20]
        QUIT_FRAME = 21
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

        return world

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
