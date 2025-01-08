from miniworldmaker import *
import random
board = PixelBoard((100,100))
Circle.from_center((50,50),50)
Arc.from_center((50,80),40,20, 180, 360)
Circle.from_center((30,30),10)
Circle.from_center((70,30),10)
Line((50,50),(50,70))
board.run()
