from miniworldmaker import *
import random
board = PixelBoard((100,100))
c = Circle((0,50), 20)
@board.register
def act(self):
    c.x = c.x + 1
    
board.run()