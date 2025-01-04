from miniworlds import Actor, World, App
import unittest
from screenshot_tester import ScreenshotTester

class Test104(unittest.TestCase):
    
    def setUp(self):
        def test_code():
            world = World(400,300)
            
            @world.register
            def setup_environment(self, test):
                world.add_background("images/stone")

                actor1 = Actor()
                actor1.origin = "topleft"
                actor1.add_costume("images/player")
                actor1.position = (20,20)
                assert(actor1.position == (20, 20))
                #with test.assertRaises(Exception) as context:
                #    actor2 = Actor()
                #    actor2.position = (120,120)
                #    actor2.add_costume("images/player.abc")
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1]
        QUIT_FRAME = 1
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if (hasattr(world, "setup_environment")):
            world.setup_environment(self)
        
    

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == '__main__':
    unittest.main()


