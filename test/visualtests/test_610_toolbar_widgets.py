from miniworlds import App, World, Actor, Toolbar, Button, Label, Label, loop
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test610(unittest.TestCase):

    def setUp(self):
        def test_code():
            world = World()
            # Here comes your code
            @world.register
            def setup_environment(self, test):
                toolbar = Toolbar()
                toolbar.margin_left =  20
                toolbar.margin_right = 10
                toolbar.background_color = (255,0,255)

                button1 = Button("Toolbar Button")
                button1.text = "Changed Text"
                button1.set_image("images/arrow.png")
                button1.set_border((0,0,0,255), 2)
                button1.margin_bottom = 30
                toolbar.add(button1)
                print("Changed Text", button1.position)

                button2 = Button("Toolbar Button")
                button2.text = "Changed Text 2"
                button2.set_image("images/arrow.png")
                button2.margin_left = 10
                button2.margin_right = 10
                button2.set_background_color((200,200,0))
                toolbar.add(button2)
                print("Changed Text 2", button2.position)

                button = Label("Toolbar Label")
                button.text = "Changed Label"
                button.set_image("images/arrow.png")
                button.set_border((0,0,0,255), 2)
                button.margin_top = 30
                toolbar.add(button)

                #@button.register
                #def on_clicked_left():
                #    print("clicked left")
                    
                @world.register
                def on_message(self, text):
                    print(text)

                label = Label("Toolbar Label")
                label.text = "Changed Label"
                label.set_image("images/arrow.png")
                label.set_border((0,0,0,255), 2)
                toolbar.add(label)

                label = Label("Remove")
                toolbar.add(label)
                toolbar.remove(label)

                label = Label("0")
                toolbar.add(label)
                label.set_image((255,0,0))
                label.padding_left = 0
                label.padding_right = 0
                label.padding_top = 0
                label.padding_bottom = 0
                label.margin_right = 10
                label.margin_left = 0
                label.img_width = 40

                label = Label("status")
                toolbar.add(label)
                label.set_image((0,255,0))
                label.background_color = (255,255,255)
                label.padding_left = 0
                label.padding_right = 0
                label.padding_top = 0
                label.padding_bottom = 0
                label.margin_right = 0
                label.set_border((0,0,0,255), 2)
                label.text_align = "left"
                percent = 0
                @loop(frames = 10)
                def change_status():
                    nonlocal percent
                    label.img_width = label.width / 100 * percent
                    label.text = str(percent)
                    if percent < 100:
                        percent += 10
                world.layout.add_right(toolbar, size = 200)
                print("Changed Text", button1.position)
                print("Changed Text 2", button2.position)
            return world
        App.reset(unittest=True, file=__file__)
        world = test_code()
        """ Setup screenshot tester"""
        TEST_FRAMES = [1,30,60,100,110]
        QUIT_FRAME = 110
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
