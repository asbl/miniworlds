from miniworlds import World, Actor, App
import unittest
from screenshot_tester import ScreenshotTester

class Test107(unittest.TestCase):
    def setUp(self):
        def test_code():
            """
            Test code here

            Returns
                World which should be used by tester
            """
            world = World(600, 300)
            @world.register
            def setup_environment(self, test):
                world.add_background("images/stone.jpg")
                # Top left
                obj1 = Actor(position=(50, 50))
                obj1.size = (80, 80)
                obj2 = Actor(position=(140, 50))
                obj2.size = (20, 80)
                obj3 = Actor(position=(170, 50))
                obj3.size = (20, 20)
                
                # Bottom left
                pl1 = Actor(position=(240, 50), origin="topleft")
                pl1.add_costume("images/player")
                pl1.size = (80, 80)
                pl1.border = 1

                pl2 = Actor(position=(330, 50), origin="topleft")
                pl2.add_costume("images/player")
                pl2.size = (20, 80)
                pl2.border = 1

                pl3 = Actor(position=(370, 50), origin="topleft")
                pl3.add_costume("images/player")
                pl3.size = (20, 20)
                pl3.border = 1

                
                # Bottom left
                pl1 = Actor(position=(50, 200))
                pl1.add_costume("images/player")
                pl1.size = (80, 80)
                pl1.border = 1

                pl2 = Actor(position=(140, 200))
                pl2.add_costume("images/player")
                pl2.size = (20, 80)
                pl2.border = 1

                pl3 = Actor(position=(170, 200))
                pl3.add_costume("images/player")
                pl3.size = (20, 20)
                pl3.border = 1

                # Bottom right
                class Sizer(Actor):
                    def on_setup(self):
                        self.size = (80, 80)

                pl4 = Sizer(position=(240, 200))
                pl4.add_costume("images/player")

                class Sizer2(Actor):
                    def on_setup(self):
                        self.size = (30, 30)

                pl5 = Sizer2(position=(290, 200))
                pl5.add_costume("images/player")
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

    


    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
