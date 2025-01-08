from miniworldmaker import *
import random
board = PixelBoard((100,100))

circle = Circle((50,50), 20)
x = 0

@board.register
def on_key_pressed_a(self):
    circle.x = circle.x - 1

@board.register
def on_key_pressed_d(self):
    circle.x = circle.x + 1
    

board.run()

