from miniworlds import Actor, World, App
import imgcompare
import unittest
from .screenshot_tester import ScreenshotTester

def diff(ia, ib):
    percentage = imgcompare.image_diff_percent(ia, ib)
    return percentage

class Test105(unittest.TestCase):
    def setUp(self):
        def test_code():
            world = World(400,300)
            @world.register
            def setup_environment(self, test):
                world.add_background("images/grass.jpg")
                world.size = (800,300)
                world.background.is_scaled_to_width = True
                # 4 actors: In topleft corner, at (20,20)
                t1 = Actor(position=(0, 0), origin = "topleft")
                t2 = Actor(position=(60, 40), origin = "topleft")
                t2.add_costume("images/char_blue.png")
                t3 = Actor(position=(100, 40), origin = "topleft")
                t3.add_costume("images/char_blue.png")

                t4 = Actor()
                t4.center=(60, 60)
                t4.add_costume((100,100,100,200))
                test.assertEqual(t4.position, (60,60))
                test.assertEqual(t4.center, (60,60))
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


