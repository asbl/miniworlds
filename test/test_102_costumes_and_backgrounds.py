from miniworlds import App, World, Actor, CostumeOutOfBoundsError
from screenshot_tester import ScreenshotTester
import unittest
import os


class Test102(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World(200, 400)
            path = os.path.dirname(__file__)
            world.app.register_path(path)
            world.tile_size = 40
            world.add_background("images/grass.png")
            actor = Actor()
            actor.position = (4, 4)
            actor.add_costume("images/player.png")

            # Actor 1: Purple in topleft corner
            actor1 = Actor.from_topleft((0,0))
            actor1.size = (40, 40)  # should be in topleft corner
            assert actor1.topleft, (0, 0)

            actor2 = Actor(position=(40, 40), origin = "topleft")
            assert actor2.center, (40, 40)
            actor2.size = (40, 40)
            assert actor2.topleft, (20, 20)
            assert actor2.size, (40, 40)

            # Actor 3: Below actor1, created with Image "1"
            actor3 = Actor(position=(40, 80), origin = "topleft")
            actor3.add_costume("images/1.png")
            actor3.size = (40, 40)
            assert actor3.position, (40, 80)

            # Actor 4: Below actor1, created with Image "2" in `on_setup`-Method
            class MyActor(Actor):
                def on_setup(self):
                    self.add_costume("images/2.png")
                    self.origin = "topleft"

            actor4 = MyActor(position=(40, 130))
            assert actor4.position, (40, 130)

            # Actor5: Created with image "3" without file ending
            actor5 = Actor(position=(60, 200), origin = "topleft")
            actor5.add_costume("images/3")
            assert actor5.position == (60, 200)
            # assert actor5.costume.image.get_width() == 40
            # assert actor5.costume.image.get_height() == 40

            # Actor6: Created with images "1" and "2", switches from
            class SwitchBackground(Actor):
                def on_setup(self):
                    self.add_costume("images/1")
                    self.add_costume("images/2")
                    self.origin = "topleft"

            SwitchBackground(position=(60, 250))

            # Actor 7: Like 6, but switches to costume 1 (remember, counting from 0)
            actor7 = SwitchBackground(position=(67, 307))
            actor7.switch_costume(1)

            # Actor 7 throws error because switching to costume 2 is not allowed
            with self.assertRaises(CostumeOutOfBoundsError):
                actor7.switch_costume(2)

            # Actor 8: Purple in topleft corner (with center)
            actor8 = Actor()
            actor8.origin = "topleft"
            actor8.size = (40, 40)
            actor8.center = (200, 0)
            assert(actor8.center == (200, 0))
            assert(actor8.position == (180.0, -20.0))
            
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1]
        QUIT_FRAME = 1
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)
        

    def test_main(self):
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
