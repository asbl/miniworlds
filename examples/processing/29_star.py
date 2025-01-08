from miniworldmaker import *
import random
board = PixelBoard((100,100))
a = Triangle((50,0), (20, 70), (80,70))
b = Triangle((50,90), (20, 20), (80,20))
a.border = 0
b.border = 0
board.run()