from miniworldmaker import *
board = PixelBoard((100,100))
a = 3
@board.register
def on_key_pressed_a(self):
    global a
    a = a + 1
    print(a)
board.run()


