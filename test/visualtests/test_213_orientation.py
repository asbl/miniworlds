from miniworlds import App, World, Actor
from .screenshot_tester import ScreenshotTester
import unittest


class Test213(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200,200)
            # Here comes your code
            @world.register
            def setup_environment(self, test):

                player1 = Actor(position=(0, 0), origin = "topleft")
                player1.size = (40, 40)
                player1.add_costume("images/char_blue.png")
                player1.costume.orientation = 0

                player2 = Actor(position=(40, 0), origin = "topleft")
                player2.size = (40, 40)
                player2.add_costume("images/char_blue.png")
                player2.costume.orientation = - 90

                player3 = Actor(position=(80, 0), origin = "topleft")
                player3.size = (40, 40)
                player3.add_costume("images/char_blue.png")
                player3.costume.orientation = 180

                player4 = Actor(position=(120, 0), origin = "topleft")
                player4.size = (40, 40)
                player4.add_costume("images/char_blue.png")
                player4.costume.orientation = 90

                class Player5(Actor):
                    def on_setup(self):
                        self.size = (40, 40)
                        self.add_costume("images/char_blue.png")
                        self.costume.orientation = 90
                        self.origin = "topleft"
                        
                Player5(position = (160,0))
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1]
        QUIT_FRAME = 1
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