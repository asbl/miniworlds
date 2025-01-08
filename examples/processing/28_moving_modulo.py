from miniworldmaker import *
import random
board = PixelBoard((100,100))
c = Circle((0,50), 20)
x = 0
@board.register
def act(self):
    global x
    c.x = x % 100
    x = x + 1
board.run()