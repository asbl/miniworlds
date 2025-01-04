from miniworlds import App, World, Text, OriginException
from screenshot_tester import ScreenshotTester
import unittest

class Test116(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                world.size = (200,800)

                # topleft at 10, 10
                t1 = Text.from_topleft((10,10), text = "1: topleft")
                t1.font_size = 50
                
                # centered at 100, 50
                t2 = Text.from_center((100,50), text = "2: center")
                t2.border = 1
                t2.font_size = 20
                print(">>>>T2 ", t2.position, t2.center)
                
                # topleft at 10, 80
                t3 = Text((10,80), text = "3: topleft", origin = "topleft")
                t3.border = 1
                t3.font_size = 20

                # centered at 100, 110
                t4 = Text((100,110), text = "4: centered", origin = "center")
                t4.border = 1
                t4.color = (255,100,100,100)
                t4.font_size = 20
                
                # topleft at 10, 140
                t5 = Text((10,140),)
                t5.origin = "topleft"
                t5.text = "5: topleft"
                t5.border = 1
                t5.color = (255,100,100,100)
                t5.font_size = 20
                
                # centered at 100, 170
                t6 = Text((100,190),)
                t6.origin = "center"
                t6.text = "6: centered"
                t6.border = 1
                t6.color = (255,100,100,100)
                t6.font_size = 40
                
                                # centered at 100, 170
                with test.assertRaises(OriginException):
                    t7 = Text((100,190),)
                    t7.origin = "centered"
                    
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1]
        QUIT_FRAME = 10
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)


    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()

